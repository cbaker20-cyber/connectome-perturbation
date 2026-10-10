"""Deadline-limited CCR reproduction, capacity probes and gated fixed pilot."""
import os
for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[key] = '1'
os.environ['MPLBACKEND'] = 'Agg'
import argparse
from datetime import datetime, timezone
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np
import pandas as pd
from eigencircuits.common import atomic_json, environment, neuron_ids, now, read_json, sha256


def run_owned(command, directory, timeout_seconds, cwd):
    if not np.isfinite(timeout_seconds) or timeout_seconds <= 0:
        raise ValueError('Positive finite worker timeout required')
    directory.mkdir(parents=True,exist_ok=False)
    record={'command':list(command),'started_utc':now(),'deadline_seconds':timeout_seconds}
    started=time.monotonic()
    with (directory/'stdout.txt').open('w') as stdout, (directory/'stderr.txt').open('w') as stderr:
        flags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0
        process=subprocess.Popen(command,cwd=cwd,stdout=stdout,stderr=stderr,
                                 start_new_session=os.name!='nt',creationflags=flags)
        record.update(pid=process.pid,timed_out=False)
        try:
            process.wait(timeout=timeout_seconds)
        except subprocess.TimeoutExpired:
            record['timed_out']=True
        except BaseException as error:
            record['interrupted']=repr(error)
            raise
        finally:
            # An interrupted controller must not leave its separately grouped worker running.
            if process.poll() is None:
                if os.name=='nt':
                    stopped=subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],
                                           capture_output=True,text=True,timeout=15,creationflags=flags)
                    record['cleanup']={'returncode':stopped.returncode,'stderr':stopped.stderr}
                else:
                    try:os.killpg(process.pid,signal.SIGKILL)
                    except ProcessLookupError:pass
                process.wait(timeout=15)
            record.update(returncode=process.returncode,elapsed_seconds=time.monotonic()-started,finished_utc=now())
            atomic_json(directory/'process.json',record)
    return record


def interrupted(signum, frame):
    raise KeyboardInterrupt(f'Controller received signal {signum}')


def deadline_seconds(deadline, slurm_seconds, clock=None):
    end = datetime.fromisoformat(deadline)
    if end.tzinfo is None or not np.isfinite(slurm_seconds) or slurm_seconds <= 0:
        raise ValueError('Timezone and positive finite Slurm remainder required')
    clock = clock or datetime.now(timezone.utc)
    return max(0., min((end-clock).total_seconds(), slurm_seconds)-300.)


def scientific_gate(measurements, remaining, memory_mb):
    expected = {.00005, .000025}
    if len(measurements) != 2 or {m['dt_ms'] for m in measurements} != expected:
        raise ValueError('Both distinct declared capacity steps required')
    for m in measurements:
        if m['duration_s'] != .01 or m['status'] != 'complete':
            raise ValueError('Only complete ten-ms probes can set the capacity screen')
        if not np.isfinite(m['seconds']) or m['seconds'] <= 0 or not np.isfinite(m['peak_rss_bytes']) or m['peak_rss_bytes'] <= 0:
            raise ValueError('Invalid capacity measurement')
    if not np.isfinite(remaining) or not np.isfinite(memory_mb) or memory_mb <= 0:
        raise ValueError('Invalid remaining resource budget')
    estimates = {str(m['dt_ms']): 2*m['seconds']/.01 for m in measurements}
    required = 6*sum(estimates.values())
    memory = max(16_000_000_000, 1.5*max(m['peak_rss_bytes'] for m in measurements))
    return {'allowed': remaining >= required and memory_mb*1_000_000 >= memory+8_000_000_000,
            'required_serial_seconds': required, 'remaining_seconds': remaining,
            'per_trial_seconds': estimates, 'worker_memory_screen_bytes': memory,
            'limits': 'Twice short-prefix scaling is a scheduling screen, not a guaranteed runtime or full-duration memory measurement.'}


def package_plan():
    manifest = read_json(ROOT/'package_manifest.json')
    for name, expected in manifest.items():
        path = ROOT/name
        if not path.is_file() or sha256(path) != expected:
            raise ValueError('Missing or changed package file: '+name)
    plan = read_json(ROOT/'smaller_plan.json')
    jobs = plan['jobs']
    keys = {(j['seed'], j['condition'], j['dt_ms']) for j in jobs}
    expected = {(s, c, d) for s in (631401,631402,631403)
                for c in ('baseline','mode') for d in (.00005,.000025)}
    if len(jobs) != 12 or keys != expected or len({j['id'] for j in jobs}) != 12:
        raise ValueError('Pilot jobs differ from the declared panel')
    if plan['criteria'] != read_json(ROOT/'anchor_plan.json')['criteria']:
        raise ValueError('Original criteria changed')
    mode = plan['mode_ids']
    if len(mode)!=51 or len(set(mode))!=51 or any(not isinstance(v,str) or not v.isdigit() for v in mode):
        raise ValueError('Invalid mode IDs')
    for j in jobs:
        ids=j['lesion_ids']
        expected_ids=[] if j['condition']=='baseline' else mode
        # Mode rank order and archived lesion ID order differ; membership must agree exactly.
        if j['variant'] != 'default' or len(ids)!=len(set(ids)) or set(ids)!=set(expected_ids):
            raise ValueError('Changed variant or lesion support')
    return plan


def compare_prefix(spikes, delivered, reference, duration_s, dt_ms):
    ref_spikes = pd.read_parquet(reference/'spikes.parquet')
    ref_delivered = pd.read_parquet(reference/'delivered_events.parquet')
    stop = round(duration_s*1000/dt_ms)
    ticks = np.rint(ref_spikes.t.to_numpy()*1000/dt_ms).astype(np.int64)
    ref_spikes = ref_spikes.loc[ticks < stop].reset_index(drop=True)
    ref_delivered = ref_delivered.loc[ref_delivered.tick < stop].reset_index(drop=True)
    pd.testing.assert_frame_equal(spikes[['t','flywire_id']], ref_spikes[['t','flywire_id']], check_dtype=False, check_exact=True)
    pd.testing.assert_frame_equal(delivered[['tick','flywire_id']], ref_delivered[['tick','flywire_id']], check_dtype=False, check_exact=True)


def prefix_worker(out, kind, dt_ms):
    from eigencircuits.memory import peak_rss
    from scripts.pcdr_fine_sim import input_tape, simulate
    plan = package_plan()
    condition = 'mode' if kind == 'reference_mode' else 'baseline'
    if kind.startswith('reference') and dt_ms != .0001:
        raise ValueError('Reference must use archived step')
    if kind == 'probe' and dt_ms not in (.00005,.000025):
        raise ValueError('Undeclared probe step')
    out.mkdir(parents=True, exist_ok=False)
    record = {'status':'running','kind':kind,'dt_ms':dt_ms,'duration_s':.01,
              'started_utc':now(),'environment':environment()}
    atomic_json(out/'measurement.json',record)
    try:
        source = ROOT/'original/trials'/f'default_{condition}_631401'
        saved = read_json(source/'manifest.json')
        ids = neuron_ids(); lookup = {v:i for i,v in enumerate(ids)}
        events = pd.read_parquet(source/'input_events.parquet')
        events = events.loc[events.tick < 100].copy()
        started = time.monotonic()
        frames = simulate(631401,[lookup[v] for v in saved['input_ids']],
                          [lookup[v] for v in (plan['mode_ids'] if condition=='mode' else [])],
                          tape=input_tape(events,saved['input_ids'],dt_ms,.01),
                          duration_s=.01,dt_ms=dt_ms,chunk_ms=10.,return_delivered=True)
        elapsed = time.monotonic()-started
        for frame in frames:
            frame['flywire_id'] = pd.Series([ids[i] for i in frame.pop('neuron_index')],dtype='string')
        spikes, scheduled, delivered = frames
        expected = events[['tick','flywire_id']].copy()
        expected['tick'] = expected.tick*round(.1/dt_ms)
        pd.testing.assert_frame_equal(scheduled[['tick','flywire_id']],expected.reset_index(drop=True),check_dtype=False,check_exact=True)
        if delivered.duplicated().any() or not pd.MultiIndex.from_frame(delivered).isin(pd.MultiIndex.from_frame(scheduled)).all():
            raise ValueError('Invalid delivered input')
        for name,frame in zip(('spikes','scheduled','delivered'),frames):
            frame.to_parquet(out/(name+'.parquet'),index=False)
        if kind.startswith('reference'):
            compare_prefix(spikes,delivered,ROOT/'anchors'/f'fine_0p0001_default_{condition}_631401',.01,dt_ms)
        record.update(status='complete',finished_utc=now(),seconds=elapsed,
                      peak_rss_bytes=peak_rss(),spike_count=len(spikes),
                      exact_reference=kind.startswith('reference'),
                      outputs={p.name:sha256(p) for p in out.glob('*.parquet')})
        atomic_json(out/'measurement.json',record)
    except BaseException as error:
        record.update(status='failed',finished_utc=now(),error=repr(error))
        atomic_json(out/'measurement.json',record)
        raise


def archive(out):
    target = out.parent/'CCR_smaller_pilot_results.zip'
    if target.exists():
        raise FileExistsError('Refuse to replace existing result archive')
    temp = target.with_suffix('.zip.tmp')
    with zipfile.ZipFile(temp,'w',zipfile.ZIP_DEFLATED,compresslevel=1) as z:
        for path in sorted(out.rglob('*')):
            if path.is_file() and path.name != 'controller.lock':
                z.write(path,'results/'+path.relative_to(out).as_posix())
        for name in read_json(ROOT/'package_manifest.json'):
            if name.startswith(('scripts/','eigencircuits/')) or name.endswith(('.json','.sh','.txt','.md')) or name=='model.py':
                z.write(ROOT/name,'package/'+name)
        z.write(ROOT/'package_manifest.json','package/package_manifest.json')
    with zipfile.ZipFile(temp) as z:
        if z.testzip() is not None:
            raise ValueError('Result archive CRC failure')
    temp.rename(target)


def run(out):
    from scripts.pcdr_ccr_capacity import allocation
    from scripts.pcdr_resolution import seconds_left
    plan = package_plan()
    cpus,memory = allocation()
    if cpus < 3 or memory < 32000:
        raise ValueError('Require at least3 CPUs and32000MB for serial probe with reserve')
    host = os.uname().nodename
    if not host.startswith('cpn-'):
        raise ValueError('Refuse simulation outside an observed CCR compute-node hostname')
    current = environment()
    if sys.version_info[:3] != (3,11,5) or current['packages'] != plan['packages']:
        raise ValueError('Simulation environment differs from archived reference')
    def remaining():
        value = subprocess.check_output(['squeue','-h','-j',os.environ['SLURM_JOB_ID'],'-o','%L'],text=True,timeout=20)
        return deadline_seconds(plan['deadline_utc'],seconds_left(value))
    if remaining() <= 60:
        raise TimeoutError('No work budget remains before collection reserve')
    out.mkdir(parents=True,exist_ok=False)
    lock=out/'controller.lock'
    with lock.open('x') as f:f.write(f'{os.getpid()} Slurm {os.environ["SLURM_JOB_ID"]}\n')
    previous=signal.signal(signal.SIGTERM,interrupted)
    status={'status':'running','started_utc':now(),'slurm_job_id':os.environ['SLURM_JOB_ID'],
            'host':host,'cpus':cpus,'memory_mb':memory,'workers':1,'scientific_completed':0,
            'scientific_total':12,'probes_completed':0,'environment':current}
    try:
        if (ROOT/'installed-libraries.txt').exists():
            shutil.copyfile(ROOT/'installed-libraries.txt',out/'installed-libraries.txt')
        atomic_json(out/'progress.json',status)
        measures=[]
        for kind,dt in [('reference_baseline',.0001),('reference_mode',.0001),('probe',.00005),('probe',.000025)]:
            name=f'{kind}_{dt}'
            target=out/name
            timeout=min(2700.,remaining())
            if timeout <= 0:raise TimeoutError('Block or allocation budget reached')
            status.update(active=name,updated_utc=now());atomic_json(out/'progress.json',status)
            process=run_owned([sys.executable,str(Path(__file__)),'prefix','--out',str(target),'--kind',kind,'--dt',str(dt)],out/'logs'/name,timeout,cwd=ROOT)
            if process['returncode'] or process['timed_out']:
                raise RuntimeError('Prefix failed or timed out: '+name)
            m=read_json(target/'measurement.json')
            if m['status']!='complete':raise ValueError('Incomplete prefix: '+name)
            for file,digest in m['outputs'].items():
                if sha256(target/file)!=digest:raise ValueError('Changed prefix output: '+file)
            if kind=='probe':measures.append(m)
            status['probes_completed']+=1
        gate=scientific_gate(measures,remaining(),memory)
        atomic_json(out/'capacity_gate.json',gate)
        if not gate['allowed']:
            status.update(status='budget_insufficient',active=None,finished_utc=now(),
                          explanation='References/probes completed. Twelve scientific trials remain unexecuted; cannot fit the declared resource screen.')
            atomic_json(out/'progress.json',status)
            return
        for i,spec in enumerate(plan['jobs']):
            status.update(active=spec['id'],updated_utc=now());atomic_json(out/'progress.json',status)
            timeout=min(gate['per_trial_seconds'][str(spec['dt_ms'])],remaining())
            if timeout <= 0:raise TimeoutError('Scientific budget reached')
            proc=run_owned([sys.executable,str(Path(__file__)),'worker','--out',str(out),'--index',str(i)],out/'logs'/spec['id'],timeout,cwd=ROOT)
            if proc['returncode'] or proc['timed_out']:raise RuntimeError('Scientific trial failed: '+spec['id'])
            status['scientific_completed']+=1
        # Existing anchors are read-only copies; all twelve new jobs are required before summarizing.
        from scripts.pcdr_fine_ccr import collect,checked
        for spec in plan['jobs']:checked(out/'trials'/spec['id'],spec)
        for spec in plan['anchors']:
            shutil.copytree(ROOT/'anchors'/spec['id'],out/'trials'/spec['id'])
            checked(out/'trials'/spec['id'],spec)
        analysis=dict(plan,jobs=plan['anchors']+plan['jobs'],steps_ms=[.0001,.00005,.000025])
        collect(out,analysis)
        agreement=read_json(out/'step_agreement.json')
        agreement['pilot_panel_final_two_halvings_pass']=agreement.pop('final_two_halvings_meet_declared_criteria')
        for group in agreement['groups']:
            group['pilot_panel_meets_thresholds']=group.pop('meets_declared_criteria')
        agreement['pilot_only']=True
        agreement['original_30_seed_requirement_established']=False
        agreement['interpretation']='Three previously inspected seeds only; any pilot agreement does not establish the original thirty-seed criterion. All original failures remain.'
        atomic_json(out/'step_agreement.json',agreement)
        status.update(status='scientific_complete',active=None,finished_utc=now())
        atomic_json(out/'progress.json',status)
    except BaseException as error:
        status.update(status='failed_or_interrupted',error=repr(error),finished_utc=now())
        atomic_json(out/'progress.json',status)
        raise
    finally:
        signal.signal(signal.SIGTERM,previous)
        lock.unlink()
        archive(out)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['verify','run','prefix','worker'])
    parser.add_argument('--out',type=Path,default=ROOT/'smaller_results')
    parser.add_argument('--kind',choices=['reference_baseline','reference_mode','probe'])
    parser.add_argument('--dt',type=float)
    parser.add_argument('--index',type=int)
    a=parser.parse_args()
    if a.action=='verify':package_plan()
    elif a.action=='run':run(a.out.resolve())
    elif a.action=='prefix':prefix_worker(a.out.resolve(),a.kind,a.dt)
    else:
        plan=package_plan()
        if a.index is None or not 0<=a.index<len(plan['jobs']):raise ValueError('Invalid scientific trial index')
        from scripts import pcdr_resolution as resolution
        from scripts.pcdr_fine_sim import input_tape,simulate
        resolution.simulate=simulate;resolution.input_tape=input_tape
        resolution.worker(ROOT/'original',a.out.resolve()/'trials'/plan['jobs'][a.index]['id'],plan['jobs'][a.index])


if __name__=='__main__':
    main()
