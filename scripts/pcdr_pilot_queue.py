"""Run the five remaining frozen pilot pairs as bounded Slurm array tasks."""
import math
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
import zipfile

ROOT = Path(os.environ.get('PCDR_PACKAGE', '/user/cbaker4/connectome_four_trial'))
sys.path.insert(0, str(ROOT))
from eigencircuits.common import atomic_json, environment, now, read_json, sha256
from scripts.pcdr_four_trial import batch
from scripts.pcdr_smaller_pilot import interrupted, package_plan

# The seed631401/0.00005ms pair already has live workers in the recovery folder.
PAIRS = ((631401, .000025), (631402, .00005), (631402, .000025),
         (631403, .00005), (631403, .000025))


def select_pair(plan, task):
    if not 0 <= task < len(PAIRS):
        raise ValueError('Unknown array task')
    seed, dt = PAIRS[task]
    selected = [(i, j) for i, j in enumerate(plan['jobs'])
                if j['seed'] == seed and j['dt_ms'] == dt]
    if len(selected) != 2 or {j['condition'] for _, j in selected} != {'baseline', 'mode'}:
        raise ValueError('Missing or duplicate frozen pair')
    if len({j['id'] for _, j in selected}) != 2:
        raise ValueError('Duplicate trial identifier')
    return seed, dt, selected


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


def output_folder(task, dt, attempt):
    if attempt == 'initial':
        return ROOT/f'queued_pair_{task}_20261013'
    if attempt != 'sapphire' or task != 0 or dt != .000025:
        raise ValueError('Unplanned retry scope')
    prior = read_json(ROOT/f'queued_pair_{task}_20261013/progress.json')
    if prior['status'] != 'budget_insufficient' or prior['scientific_completed'] != 0:
        raise ValueError('Retry requires preserved refusal with no completed science')
    if (ROOT/f'queued_pair_{task}_20261013/logs/scientific').exists():
        raise ValueError('Prior scientific launch requires separate review')
    return ROOT/f'sapphire_pair_{task}_20261013'


def main():
    import fcntl
    from scripts.pcdr_ccr_capacity import allocation
    from scripts.pcdr_resolution import seconds_left
    from scripts.pcdr_fine_ccr import checked
    task = int(os.environ['SLURM_ARRAY_TASK_ID'])
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
    remaining = seconds_left(subprocess.check_output(
        ['squeue', '-h', '-j', job, '-o', '%L'], text=True, timeout=20))
    budget = min(70*3600, remaining-1200)
    if budget < 3600:
        raise ValueError('Insufficient allocation budget')
    deadline = time.monotonic()+budget
    attempt = os.environ.get('PCDR_EXECUTION_ATTEMPT', 'initial')
    out = output_folder(task, dt, attempt)
    with (ROOT/f'.queued_pair_{task}.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        out.mkdir(exist_ok=False)
        status = dict(status='running', phase='reference', started_utc=now(),
                      job_id=job, array_job_id=os.environ['SLURM_ARRAY_JOB_ID'], task=task,
                      host=os.uname().nodename, cpus=cpus, memory_mb=memory,
                      seed=seed, dt_ms=dt, scientific_completed=0, environment=current,
                      execution_attempt=attempt,
                      budget_seconds=budget, original_criteria_unchanged=True)
        def update(records):
            status.update(processes=records, updated_utc=now())
            atomic_json(out/'progress.json', status)
        def child(*args):
            return [sys.executable, str(ROOT/'scripts/pcdr_four_trial.py'), 'child',
                    str(ROOT/'scripts/pcdr_smaller_pilot.py'), *args]
        previous = signal.signal(signal.SIGTERM, interrupted)
        try:
            atomic_json(out/'execution_amendment.json', dict(status,
                trial_ids=[j['id'] for _, j in selected],
                calibration_seed=631401, duration_s=1, margin_factor=2,
                reason='Complete remaining fixed pilot pairs; exclude active recovery pair',
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


if __name__ == '__main__':
    main()
