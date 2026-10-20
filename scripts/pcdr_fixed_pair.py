"""One authorized fixed seed pair at 0.0000125 ms; frozen simulator unchanged."""
import argparse
import math
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from eigencircuits.common import atomic_json, environment, now, read_json, sha256, neuron_ids
import pandas as pd
from scripts.pcdr_four_trial import batch
from scripts.pcdr_smaller_pilot import interrupted, package_plan, compare_prefix

SEED = 631401
DT = .0000125


def select_pair(plan, task=0):
    if task != 0:
        raise ValueError('Only one fixed pair is authorized')
    original = [j for j in plan['jobs'] if j['seed'] == SEED and j['dt_ms'] == .000025]
    if len(original) != 2 or {j['condition'] for j in original} != {'baseline', 'mode'}:
        raise ValueError('Missing or duplicate source pair')
    jobs = [dict(j, id=f"fixed_{DT}_{j['condition']}_{SEED}", dt_ms=DT) for j in original]
    return SEED, DT, list(enumerate(jobs))


def capacity(measures, dt, remaining):
    if not math.isfinite(remaining) or remaining <= 0:
        raise ValueError('Invalid remaining budget')
    if len(measures) != 2:
        raise ValueError('Two concurrent probes required')
    for m in measures:
        if m['status'] != 'complete' or m['duration_s'] != .01 or m['dt_ms'] != dt:
            raise ValueError('Wrong or incomplete probe')
        if not math.isfinite(m['seconds']) or m['seconds'] <= 0:
            raise ValueError('Invalid duration')
        if not math.isfinite(m['peak_rss_bytes']) or not 0 < m['peak_rss_bytes'] <= 16e9:
            raise ValueError('Invalid or excessive probe memory')
    screen = 200 * max(m['seconds'] for m in measures)
    return dict(allowed=screen <= remaining, per_trial_screen_seconds=screen,
                remaining_seconds=remaining, workers=2, margin_factor=2,
                interpretation='Twice short-prefix scaling is a screen, not a guaranteed completion time.')


def measurement(folder, reference=False):
    m = read_json(folder/'measurement.json')
    if m['status'] != 'complete' or (reference and not m['exact_reference']):
        raise ValueError(f'Prefix not verified: {folder.name}')
    if set(m['outputs']) != {'spikes.parquet', 'scheduled.parquet', 'delivered.parquet'}:
        raise ValueError('Unexpected prefix output set')
    for name, digest in m['outputs'].items():
        if sha256(folder/name) != digest:
            raise ValueError(f'Changed prefix output: {folder.name}/{name}')
    return m


def archive(out):
    target = ROOT/f'CCR_{out.name}.zip'
    temp = target.with_suffix('.zip.tmp')
    if target.exists():
        raise FileExistsError(target)
    with zipfile.ZipFile(temp, 'x', zipfile.ZIP_DEFLATED, compresslevel=1) as z:
        for p in sorted(out.rglob('*')):
            if p.is_file():
                z.write(p, 'results/'+p.relative_to(out).as_posix())
        for name in ('package_manifest.json', 'smaller_plan.json', 'execution_plan.json'):
            z.write(ROOT/name, 'package/'+name)
    with zipfile.ZipFile(temp) as z:
        if z.testzip() is not None:
            raise ValueError('Archive CRC failure')
    temp.rename(target)


def allocation_seconds(job):
    from scripts.pcdr_resolution import seconds_left
    rows = subprocess.check_output(['squeue', '-h', '-j', job, '-o', '%i|%L'],
                                   text=True, timeout=20).strip().splitlines()
    if len(rows) != 1 or rows[0].split('|')[0].strip() != job:
        raise ValueError(f'Expected one allocation row for {job}: {rows!r}')
    remaining = seconds_left(rows[0].split('|', 1)[1].strip())
    if remaining <= 0:
        raise ValueError('Allocation has no time remaining')
    return remaining


def main():
    import fcntl
    from scripts.pcdr_ccr_capacity import allocation
    from scripts.pcdr_fine_ccr import checked
    task = 0
    job = os.environ['SLURM_JOB_ID']
    if not job.isdecimal() or not os.uname().nodename.startswith('cpn-'):
        raise ValueError('CCR compute allocation required')
    cpus, memory = allocation()
    if cpus < 4 or memory < 64000:
        raise ValueError('Require4CPUs and64000MB')
    plan = package_plan()
    seed, dt, selected = select_pair(plan, task)
    current = environment()
    if sys.version_info[:3] != (3, 11, 5) or current['packages'] != plan['packages']:
        raise ValueError('Environment differs from frozen study')
    remaining = allocation_seconds(job)
    budget = min(70*3600, remaining-1200)
    if budget < 3600:
        raise ValueError('Insufficient allocation budget')
    deadline = time.monotonic()+budget
    attempt = 'fixed_seed_extension'
    out = ROOT/'fixed_pair_20261020'
    with (ROOT/'.fixed_pair_20261020.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        out.mkdir(exist_ok=False)
        status = dict(status='running', phase='reference', started_utc=now(),
                      job_id=job, task=task,
                      host=os.uname().nodename, cpus=cpus, memory_mb=memory,
                      seed=seed, dt_ms=dt, scientific_completed=0, environment=current,
                      execution_attempt=attempt,
                      budget_seconds=budget, original_criteria_unchanged=True)
        def update(records):
            status.update(processes=records, updated_utc=now())
            atomic_json(out/'progress.json', status)
        def child(*args):
            return [sys.executable, str(ROOT/'scripts/pcdr_four_trial.py'), 'child',
                    str(Path(__file__).resolve()), *args]
        previous = signal.signal(signal.SIGTERM, interrupted)
        try:
            atomic_json(out/'execution_amendment.json', dict(status,
                trial_ids=[j['id'] for _, j in selected],
                calibration_seed=631401, duration_s=1, margin_factor=2,
                reason='First original failing seed; one further halving, diagnostic only',
                jobs=[j for _, j in selected],
                frozen_plan_sha256=sha256(ROOT/'smaller_plan.json')))
            shutil.copyfile(Path(__file__), out/'queue_source.py')
            (out/'allocation.txt').write_text(subprocess.check_output(
                ['scontrol', 'show', 'job', job], text=True, timeout=20))
            refs = ['reference_baseline', 'reference_mode']
            commands = [(n, child('prefix', '--out', str(out/n), '--kind', n, '--dt', '.0001')) for n in refs]
            records = batch(commands, out/'logs/references', min(deadline, time.monotonic()+3600), update)
            if any(r['returncode'] for r in records):
                raise RuntimeError('Reference worker failed')
            for n in refs:
                measurement(out/n, reference=True)
            status['phase'] = 'capacity'
            names = ['probe_a', 'probe_b']
            commands = [(n, child('prefix', '--out', str(out/n), '--kind', 'probe', '--dt', str(dt))) for n in names]
            records = batch(commands, out/'logs/capacity', min(deadline, time.monotonic()+7200), update)
            if any(r['returncode'] for r in records):
                raise RuntimeError('Capacity worker failed')
            decision = capacity([measurement(out/n) for n in names], dt, deadline-time.monotonic())
            atomic_json(out/'capacity_gate.json', decision)
            if not decision['allowed']:
                status.update(status='budget_insufficient', phase='stopped')
                return
            status['phase'] = 'scientific'
            commands = [(j['id'], child('worker', '--out', str(out), '--index', str(i))) for i, j in selected]
            records = batch(commands, out/'logs/scientific', deadline, update)
            if any(r['returncode'] for r in records):
                raise RuntimeError('Scientific worker failed')
            for _, j in selected:
                checked(out/'trials'/j['id'], j)
            status.update(status='pair_complete', phase='finished',
                          interpretation='Pair complete; combined adjacent-step analysis and independent verification pending. Convergence not established.')
        except BaseException as error:
            status.update(status='failed_or_interrupted', error=repr(error))
            raise
        finally:
            completed = []
            for _, j in selected:
                p = out/'trials'/j['id']/'manifest.json'
                try:
                    if p.exists() and read_json(p).get('status') == 'complete':
                        checked(p.parent, j)
                        completed.append(j['id'])
                except (OSError, ValueError, KeyError) as error:
                    status.setdefault('verification_errors', []).append(repr(error))
            status.update(scientific_completed=len(completed), completed_ids=completed, finished_utc=now())
            atomic_json(out/'progress.json', status)
            signal.signal(signal.SIGTERM, previous)
            archive(out)


def prefix_worker(out, kind, dt_ms):
    from eigencircuits.memory import peak_rss
    from scripts.pcdr_fine_sim import input_tape, simulate
    if kind not in ('reference_baseline', 'reference_mode', 'probe'):
        raise ValueError('Unknown prefix kind')
    plan = package_plan()
    condition = 'mode' if kind == 'reference_mode' else 'baseline'
    if kind.startswith('reference') and dt_ms != .0001:
        raise ValueError('Reference must use archived step')
    if kind == 'probe' and dt_ms != DT:
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


def dispatch():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['run', 'prefix', 'worker', 'verify'])
    parser.add_argument('--out', type=Path)
    parser.add_argument('--kind')
    parser.add_argument('--dt', type=float)
    parser.add_argument('--index', type=int)
    args = parser.parse_args()
    if args.action == 'run':
        main()
    elif args.action == 'prefix':
        prefix_worker(args.out.resolve(), args.kind, args.dt)
    else:
        plan = package_plan()
        _, _, jobs = select_pair(plan)
        if args.action == 'verify':
            return
        if args.index not in (0, 1):
            raise ValueError('Unknown fixed trial index')
        from scripts import pcdr_resolution as resolution
        from scripts.pcdr_fine_sim import input_tape, simulate
        resolution.simulate = simulate
        resolution.input_tape = input_tape
        spec = jobs[args.index][1]
        resolution.worker(ROOT/'original', args.out.resolve()/'trials'/spec['id'], spec)


if __name__ == '__main__':
    dispatch()

