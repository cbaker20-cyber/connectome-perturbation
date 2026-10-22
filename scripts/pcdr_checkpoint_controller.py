"""Advance the authorized fixed pair within one allocation; resume from saved endpoints."""
import argparse
from pathlib import Path
import shutil
import socket
import os
import signal
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from eigencircuits.common import atomic_json, environment, now, read_json, sha256
from scripts.pcdr_checkpoint_compare import checked_generation
from scripts.pcdr_checkpoint_capacity import segment_screen
from scripts.pcdr_checkpoint_worker import owned_attempt
from scripts.pcdr_fixed_pair import allocation_seconds, select_pair
from scripts.pcdr_smaller_pilot import interrupted, package_plan, run_owned


def validation_binding(validation, plan):
    local=read_json(validation/'local_verification.json')
    provenance=read_json(validation/'provenance_verification.json')
    if local['status']!='passed' or provenance['status']!='passed':
        raise ValueError('Local validation is incomplete')
    if local['archive_sha256']!='56c0352d3696dbc730f90d0f038ea6e5703746831b7f2103a105acf34c739339':
        raise ValueError('Unexpected validation archive')
    current=environment()
    if current['packages']!=plan['packages'] or sys.version_info[:3]!=(3,11,5):
        raise ValueError('Production environment differs from validated environment')
    records={f.parent.name:read_json(f) for f in (validation/'run/measurements').glob('*/measurement.json')}
    expected={f'{c}_{branch}_{stop}' for c in ('baseline','mode')
              for branch,stop in [('reference',10),('uninterrupted',20),('restarted',10),('restarted',20)]}
    if set(records)!=expected:
        raise ValueError('Missing or unexpected validation records')
    for label,m in records.items():
        if m['status']!='complete' or m['environment']['packages']!=current['packages']:
            raise ValueError('Changed validation status or environment')
        if m['environment']['python']!=current['python']:
            raise ValueError('Python build differs from validation')
        for name in ('scripts/pcdr_checkpoint_sim.py','model.py'):
            if m['source_hashes'][name]!=sha256(ROOT/name):
                raise ValueError('Simulator or model differs from validated source')
        if 'reference' in label and not m.get('exact_reference'):
            raise ValueError('Reference reproduction missing')
    for condition in ('baseline','mode'):
        result=local['comparisons'][condition]
        if result!={'exact_state':True,'exact_delivered':True,'tick':1600000}:
            raise ValueError('Restart comparison missing or changed')
    return {label:m for label,m in records.items() if 'reference' not in label}


def next_stop(out, spec):
    condition=spec['condition']
    checkpoint=out/'checkpoints'/condition
    if (checkpoint/'owner.lock').exists() or (out/'segments'/condition/'owner.lock').exists():
        raise ValueError(f'Unresolved worker ownership: {condition}')
    trial=out/'trials'/spec['id']
    if trial.exists():
        record=read_json(trial/'manifest.json')
        if record['status']!='complete' or record['spec']!=spec:
            raise ValueError('Existing trial is incomplete or has different specification')
        if set(record['outputs'])!={'spikes.parquet','rates.parquet','delivered_events.parquet','population.json'}:
            raise ValueError('Unexpected completed output set')
        for name,digest in record['outputs'].items():
            if sha256(trial/name)!=digest:
                raise ValueError('Completed output hash mismatch')
        return None
    if not (checkpoint/'latest.json').exists():
        return 100
    record,_=checked_generation(checkpoint)
    config=record['config']
    if config['seed']!=631401 or config['dt_ms']!=.0000125 or config['duration_s']!=1.:
        raise ValueError('Checkpoint is outside authorized pair')
    tick=record['tick']; step=8000000
    if tick%step or not step<=tick<=10*step:
        raise ValueError('Checkpoint is not a production segment boundary')
    return min(1000,(tick//step+1)*100)


def run(out, validation, hours=70):
    from scripts.pcdr_ccr_capacity import allocation
    if not 0<hours<=70:
        raise ValueError('Allocation work limit must be positive and at most 70 hours')
    cpus,memory=allocation()
    if cpus<2 or memory<64000 or not socket.gethostname().startswith('cpn-'):
        raise ValueError('Require compute allocation with 2 CPUs and 64000 MB')
    plan=package_plan(); specs=[s for _,s in select_pair(plan)[2]]
    measurements=validation_binding(validation,plan)
    # An immutable contract prevents changing controller/worker code between allocations.
    sources=['scripts/'+name for name in ('pcdr_checkpoint_controller.py','pcdr_checkpoint_worker.py',
             'pcdr_checkpoint_capacity.py','pcdr_checkpoint_sim.py')]
    contract=dict(specs=specs,sources={s:sha256(ROOT/s) for s in sources},
                  validation={str(f.relative_to(validation)):sha256(f) for f in sorted(validation.glob('run/measurements/*/measurement.json'))},
                  verification={name:sha256(validation/name) for name in
                                ('local_verification.json','provenance_verification.json')})
    with owned_attempt(out,'controller',0) as (attempt,owner):
        contract_path=out/'execution_contract.json'
        if contract_path.exists():
            if read_json(contract_path)!=contract: raise ValueError('Execution contract changed')
        else:
            atomic_json(contract_path,contract)
        progress=dict(status='running',owner=owner,started_utc=now(),stages=[])
        atomic_json(attempt/'controller.json',progress)
        deadline=time.monotonic()+hours*3600
        for sig in (signal.SIGTERM,signal.SIGINT): signal.signal(sig,interrupted)
        try:
            while True:
                candidates=[(next_stop(out,s),s) for s in specs]
                candidates=[(stop,s) for stop,s in candidates if stop is not None]
                if not candidates:
                    progress['status']='execution_complete'
                    break
                stop,spec=min(candidates,key=lambda item:(item[0],item[1]['condition']))
                remaining=min(deadline-time.monotonic(),allocation_seconds(os.environ['SLURM_JOB_ID']))
                if remaining<=3600:
                    progress['status']='allocation_budget_stop'
                    break
                history=[]
                for condition in ('baseline','mode'):
                    for path in (out/'segments'/condition).glob('*/segment.json'):
                        record=read_json(path)
                        if record['status']=='checkpoint_saved': history.append(record)
                gate=segment_screen(measurements,remaining,memory,shutil.disk_usage(out).free,history)
                progress['last_gate']=gate
                if not gate['allowed']:
                    progress['status']='allocation_budget_stop'
                    break
                label=f"{spec['condition']}_{stop}_{len(progress['stages'])}"
                command=[sys.executable,str(ROOT/'scripts/pcdr_checkpoint_worker.py'),'--out',str(out),
                         '--condition',spec['condition'],'--stop-ms',str(stop)]
                result=run_owned(command,attempt/'processes'/label,gate['segment_screen_seconds'],ROOT)
                progress['stages'].append(dict(condition=spec['condition'],stop_ms=stop,process=result))
                atomic_json(attempt/'controller.json',progress)
                if result['returncode']!=0 or result['timed_out']:
                    raise RuntimeError(f'Worker failed; preserve locks and inspect ownership: {label}')
                following=next_stop(out,spec)
                if following!=(None if stop==1000 else stop+100):
                    raise ValueError('Worker did not produce the expected saved endpoint')
        except BaseException as error:
            progress.update(status='failed',error=repr(error))
            raise
        finally:
            progress['finished_utc']=now()
            atomic_json(attempt/'controller.json',progress)
            atomic_json(out/'progress.json',progress)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--validation',type=Path,required=True)
    parser.add_argument('--hours',type=float,default=70)
    args=parser.parse_args()
    run(args.out.resolve(),args.validation.resolve(),args.hours)
