"""Run only short checkpoint-equivalence probes, never full scientific trials."""
import argparse
import os
from pathlib import Path
import signal
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from eigencircuits.common import atomic_json, now, read_json
from scripts.pcdr_checkpoint_compare import compare
from scripts.pcdr_fixed_pair import allocation_seconds
from scripts.pcdr_smaller_pilot import interrupted, run_owned


def stages():
    return [(c,'reference','reference',10) for c in ('baseline','mode')] + [
        (c,'checkpoint',branch,stop) for c in ('baseline','mode')
        for branch,stop in (('uninterrupted',20),('restarted',10),('restarted',20))]


def run(out):
    from scripts.pcdr_ccr_capacity import allocation
    cpus,memory=allocation()
    if cpus<2 or memory<64000 or not os.uname().nodename.startswith('cpn-'):
        raise ValueError('Require compute allocation with 2 CPUs and 64000 MB')
    remaining=allocation_seconds(os.environ['SLURM_JOB_ID'])
    if remaining<10*3600+600:
        raise ValueError('Require ten-hour validation allowance plus termination reserve')
    out.mkdir(parents=True,exist_ok=False)
    deadline=time.monotonic()+10*3600
    progress=dict(status='running',started_utc=now(),scientific_trials_launched=0,
                  slurm_job=os.environ['SLURM_JOB_ID'],cpus=cpus,memory_mb=memory,
                  stages=[],comparisons={})
    atomic_json(out/'progress.json',progress)
    for sig in (signal.SIGTERM,signal.SIGINT):
        signal.signal(sig,interrupted)
    try:
        for condition,kind,branch,stop in stages():
            label=f'{condition}_{branch}_{stop}'
            budget=min(deadline-time.monotonic(),allocation_seconds(os.environ['SLURM_JOB_ID'])-300,
                       1800 if kind=='reference' else 7200)
            if budget<300:
                raise RuntimeError('Insufficient remaining validation allowance')
            command=[sys.executable,str(ROOT/'scripts/pcdr_checkpoint_probe.py'),
                     '--out',str(out/'measurements'/label),'--checkpoint',str(out/'checkpoints'/condition/branch),
                     '--condition',condition,'--kind',kind,'--stop-ms',str(stop)]
            result=run_owned(command,out/'processes'/label,budget,ROOT)
            progress['stages'].append(dict(label=label,process=result))
            atomic_json(out/'progress.json',progress)
            if result['returncode']!=0 or result['timed_out']:
                raise RuntimeError(f'Validation process failed: {label}')
            measurement=read_json(out/'measurements'/label/'measurement.json')
            if measurement['status']!='complete' or (kind=='reference' and not measurement.get('exact_reference')):
                raise ValueError(f'Invalid validation measurement: {label}')
        for condition in ('baseline','mode'):
            base=out/'checkpoints'/condition
            progress['comparisons'][condition]=compare(base/'uninterrupted',base/'restarted')
        progress.update(status='validation_complete',finished_utc=now())
    except BaseException as error:
        progress.update(status='failed',error=repr(error),finished_utc=now())
        raise
    finally:
        atomic_json(out/'progress.json',progress)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    run(args.out.resolve())
