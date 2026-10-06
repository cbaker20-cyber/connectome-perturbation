"""Run and verify the four declared pathway trials, then collect one result ZIP."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.pcdr_ccr_transfer import read, write, digest
from scripts.pcdr_bounded_process import run_bounded
from eigencircuits.common import now

JOBS = [(dt, condition) for dt in [.0004, .0002] for condition in ['reference', 'two_edges']]


def name(dt, condition):
    return f'{condition}_{dt}'


def verify(path, plan, dt, condition, duration):
    m = read(path/'manifest.json')
    expected = dict(status='complete', dt_ms=dt, condition=condition, duration_ms=duration,
                    plan_sha256=digest(plan), exact_delivered_input=True)
    if any(m.get(k) != v for k,v in expected.items()):
        raise ValueError('Incomplete or different trial: '+str(path))
    if condition == 'reference' and m.get('exact_reference_spikes') is not True:
        raise ValueError('Reference did not reproduce saved spikes')
    required = {'spikes.parquet','scheduled_events.parquet','delivered_events.parquet','simulation_progress.json'}
    if condition == 'two_edges': required.add('removed_edges.csv')
    if duration == 750: required.add('endpoints.json')
    if set(m['outputs']) != required:
        raise ValueError('Missing or unexpected trial outputs')
    for filename, expected_hash in m['outputs'].items():
        if digest(path/filename) != expected_hash:
            raise ValueError('Changed trial output: '+filename)
    source_names = {'model.py'} | {p.relative_to(ROOT).as_posix() for folder in ['scripts','eigencircuits']
                                    for p in (ROOT/folder).glob('*.py')}
    if set(m['sources']) != source_names:
        raise ValueError('Different source inventory')
    for filename, expected_hash in m['sources'].items():
        if digest(ROOT/filename) != expected_hash:
            raise ValueError('Changed trial source: '+filename)
    return m


def run(plan, out, hours=7., duration=750, workers=4):
    plan, out = Path(plan).resolve(), Path(out).resolve()
    if not 0 < hours <= 7 or duration not in [2,750] or workers not in [1,2,4]:
        raise ValueError('Invalid deadline, duration or workers')
    out.mkdir(parents=True, exist_ok=True)
    lock = out/'.controller.lock'
    with lock.open('x') as stream:
        stream.write(f'{os.getpid()} {now()}\n')
    completed = []
    try:
        pending = []
        for dt, condition in JOBS:
            directory = out/name(dt,condition)
            if directory.exists():
                verify(directory,plan,dt,condition,duration)
                completed.append(name(dt,condition))
            else:
                if (out/'logs'/name(dt,condition)).exists():
                    raise FileExistsError('Preserve and review previous attempt logs before retrying')
                pending.append((dt,condition))
        def progress(status):
            write(out/'progress.json', dict(status=status, completed=sorted(completed), total=4,
                                           duration_ms=duration, updated_utc=now()))
        progress('running')
        def launch(job):
            dt, condition = job
            trial = name(dt,condition)
            result = run_bounded([sys.executable,str(ROOT/'scripts/pcdr_pathway_trial.py'),
                '--plan',str(plan),'--out',str(out/trial),'--dt',str(dt),'--condition',condition,
                '--duration-ms',str(duration)],out/'logs'/trial,hours*3600,cwd=ROOT)
            write(out/'logs'/trial/'process.json',result)
            if result['returncode'] or result['timed_out']:
                raise RuntimeError('Trial failed or exceeded deadline: '+trial)
            verify(out/trial,plan,dt,condition,duration)
            return trial
        errors = []
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(launch,job) for job in pending]
            for future in as_completed(futures):
                try:
                    completed.append(future.result())
                except Exception as error:
                    errors.append(repr(error))
                progress('running' if not errors else 'finishing_other_trials_after_failure')
        if errors:
            raise RuntimeError('; '.join(errors))
        trials = [verify(out/name(dt,c),plan,dt,c,duration) for dt,c in JOBS]
        results = [dict(dt_ms=dt,condition=c,**read(out/name(dt,c)/'endpoints.json'))
                   for dt,c in JOBS] if duration == 750 else []
        write(out/'summary.json',dict(status='complete', duration_ms=duration, results=results,
                                    trials=trials, interpretation='Selected-case intervention; not a convergence or eigencircuit-specific test.'))
        progress('collecting')
        target = out.parent/('CCR_pathway_results.zip' if duration == 750 else 'pathway_setup_results.zip')
        temporary = target.with_suffix('.zip.tmp')
        with zipfile.ZipFile(temporary,'w',zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(out.rglob('*')):
                if path.is_file() and path != lock and path.name != 'progress.json':
                    archive.write(path,path.relative_to(out).as_posix())
            archive.write(plan,'diagnostic_plan.json')
            for filename in trials[0]['sources']:
                archive.write(ROOT/filename,'source/'+filename)
        with zipfile.ZipFile(temporary) as archive:
            if archive.testzip() is not None:
                raise ValueError('Result ZIP failed CRC check')
        temporary.replace(target)
        progress('complete')
    except BaseException as error:
        write(out/'progress.json',dict(status='failed',completed=sorted(completed),error=repr(error),updated_utc=now()))
        raise
    finally:
        lock.unlink()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan',type=Path,required=True); parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--hours',type=float,default=7); parser.add_argument('--duration-ms',type=int,default=750)
    parser.add_argument('--workers',type=int,default=4)
    args=parser.parse_args();run(args.plan,args.out,args.hours,args.duration_ms,args.workers)
