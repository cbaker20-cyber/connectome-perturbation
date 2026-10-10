"""Four fixed trials with measured concurrent capacity and an allocation deadline."""
import os
for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[key] = '1'
import argparse
import json
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from eigencircuits.common import atomic_json, environment, now, read_json, sha256
from scripts.pcdr_smaller_pilot import package_plan, interrupted


def select_jobs(plan):
    jobs = [(i, j) for i, j in enumerate(plan['jobs']) if j['seed'] == 631401]
    expected = {(c, d) for c in ('baseline', 'mode') for d in (.00005, .000025)}
    if len(jobs) != 4 or {(j['condition'], j['dt_ms']) for _, j in jobs} != expected:
        raise ValueError('Require exactly the four fixed seed631401 trials')
    return jobs


def gate(measures, seconds, memory_mb, cpus):
    import math
    if len(measures) != 4 or sorted(m['dt_ms'] for m in measures) != [.000025, .000025, .00005, .00005]:
        raise ValueError('Require four concurrent probes, two at each step')
    for m in measures:
        if m['status'] != 'complete' or m['duration_s'] != .01 or not math.isfinite(m['seconds']) or m['seconds'] <= 0:
            raise ValueError('Invalid completed probe')
        if not math.isfinite(m['peak_rss_bytes']) or not 0 < m['peak_rss_bytes'] <= 16e9:
            raise ValueError('Probe memory leaves insufficient full-run headroom')
    if not all(math.isfinite(v) and v > 0 for v in (seconds, memory_mb, cpus)):
        raise ValueError('Invalid allocation')
    estimates = {str(dt): max(m['seconds'] for m in measures if m['dt_ms'] == dt)*200 for dt in (.00005, .000025)}
    return {'allowed': cpus >= 8 and memory_mb >= 92000 and max(estimates.values()) <= seconds,
            'per_trial_screen_seconds': estimates, 'available_seconds': seconds,
            'workers': 4, 'worker_address_space_limit_bytes': 20_000_000_000,
            'interpretation': 'Twice measured prefix scaling, not a guaranteed completion time; concurrency can slow later activity.'}


def stop_owned(process):
    if process.poll() is not None:
        return
    if os.name == 'nt':
        subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'], check=True,
                       capture_output=True, timeout=20, creationflags=subprocess.CREATE_NO_WINDOW)
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    process.wait(timeout=20)


def batch(commands, directory, deadline, update=lambda records: None):
    """Own only processes launched here; always retain logs and final exit records."""
    if len({name for name, _ in commands}) != len(commands):
        raise ValueError('Duplicate task name')
    if directory.exists():
        raise FileExistsError(directory)
    directory.mkdir(parents=True)
    active, records = [], []
    try:
        for name, command in commands:
            if time.monotonic() >= deadline:
                raise TimeoutError('No allocation budget remains')
            folder = directory/name
            folder.mkdir()
            stdout = (folder/'stdout.txt').open('w')
            stderr = (folder/'stderr.txt').open('w')
            try:
                process = subprocess.Popen(command, cwd=ROOT, stdout=stdout, stderr=stderr,
                    start_new_session=os.name != 'nt', creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            except BaseException:
                stdout.close(); stderr.close()
                raise
            record = {'name': name, 'command': command, 'pid': process.pid,
                      'started_utc': now(), 'status': 'running'}
            active.append((process, stdout, stderr, record, folder, time.monotonic()))
            records.append(record)
            atomic_json(folder/'process.json', record)
        while any(p.poll() is None for p, *_ in active):
            for p, _, _, r, folder, start in active:
                r['elapsed_seconds'] = time.monotonic()-start
                if p.poll() is not None:
                    r.update(returncode=p.returncode, status='complete' if p.returncode == 0 else 'failed')
                atomic_json(folder/'process.json', r)
            update(records)
            if time.monotonic() >= deadline:
                raise TimeoutError('Allocation/work deadline reached; partial outputs preserved')
            time.sleep(min(2, max(.001, deadline-time.monotonic())))
        return records
    finally:
        cleanup_errors = []
        for p, stdout, stderr, r, folder, start in active:
            was_running = p.poll() is None
            try:
                stop_owned(p)
            except (OSError, subprocess.SubprocessError) as error:
                cleanup_errors.append(repr(error))
                r['cleanup_error'] = repr(error)
            finally:
                stdout.close(); stderr.close()
                r.update(returncode=p.poll(), status='interrupted' if was_running else ('complete' if p.returncode == 0 else 'failed'),
                         elapsed_seconds=time.monotonic()-start, finished_utc=now())
                atomic_json(folder/'process.json', r)
        update(records)
        if cleanup_errors:
            raise RuntimeError('Owned-worker cleanup failed: '+str(cleanup_errors))


def archive(out):
    target = ROOT/'CCR_four_trial_results.zip'
    if target.exists():
        raise FileExistsError(target)
    temp = target.with_suffix('.zip.tmp')
    with zipfile.ZipFile(temp, 'x', zipfile.ZIP_DEFLATED, compresslevel=1) as z:
        for p in sorted(out.rglob('*')):
            if p.is_file():
                z.write(p, 'results/'+p.relative_to(out).as_posix())
        for name in read_json(ROOT/'package_manifest.json'):
            if name.startswith(('scripts/', 'eigencircuits/')) or name.endswith(('.json', '.md', '.txt', '.sh')) or name == 'model.py':
                z.write(ROOT/name, 'package/'+name)
        z.write(ROOT/'package_manifest.json', 'package/package_manifest.json')
        for name in ('launch.log', 'remote_tests.xml'):
            if (ROOT/name).is_file():
                z.write(ROOT/name, 'launcher/'+name)
    with zipfile.ZipFile(temp) as z:
        if z.testzip() is not None:
            raise ValueError('Result archive CRC failure')
    temp.rename(target)


def run():
    from scripts.pcdr_ccr_capacity import allocation
    from scripts.pcdr_resolution import seconds_left
    from scripts.pcdr_fine_ccr import checked, collect
    plan = package_plan()
    jobs = select_jobs(plan)
    cpus, memory = allocation()
    if cpus < 8 or memory < 92000 or not os.uname().nodename.startswith('cpn-'):
        raise ValueError('Require CCR compute node,8CPUs and92000MB; no simulation on login node')
    current = environment()
    if sys.version_info[:3] != (3, 11, 5) or current['packages'] != plan['packages']:
        raise ValueError('Environment differs from archived scientific environment')
    raw = subprocess.check_output(['squeue', '-h', '-j', os.environ['SLURM_JOB_ID'], '-o', '%L'], text=True, timeout=20).strip()
    remaining = seconds_left(raw)
    budget = min(70*3600, remaining-900)
    if budget <= 3600:
        raise ValueError('Less than one hour remains after the collection reserve')
    deadline = time.monotonic()+budget
    out = ROOT/'four_results'
    out.mkdir(exist_ok=False)
    status = {'status': 'running', 'started_utc': now(), 'slurm_job_id': os.environ['SLURM_JOB_ID'],
              'host': os.uname().nodename, 'cpus': cpus, 'memory_mb': memory, 'slurm_remaining': raw,
              'budget_seconds': budget, 'workers': 4, 'environment': current, 'scientific_total': 4,
              'scientific_completed': 0, 'original_30_seed_requirement_established': False}
    def update(records):
        status.update(processes=records, updated_utc=now())
        atomic_json(out/'progress.json', status)
    old = signal.signal(signal.SIGTERM, interrupted)
    try:
        allocation_text = subprocess.check_output(['scontrol', 'show', 'job', os.environ['SLURM_JOB_ID']], text=True, timeout=20)
        (out/'slurm_allocation.txt').write_text(allocation_text)
        shutil.copyfile(ROOT/'installed-libraries.txt', out/'installed-libraries.txt')
        status['phase'] = 'reference'
        script = str(ROOT/'scripts/pcdr_smaller_pilot.py')
        def child(args):
            return [sys.executable, str(Path(__file__)), 'child', script, *args]
        commands = [(kind, child(['prefix', '--out', str(out/kind), '--kind', kind, '--dt', '.0001']))
                    for kind in ('reference_baseline', 'reference_mode')]
        results = batch(commands, out/'logs/reference', min(deadline, time.monotonic()+3600), update)
        if any(r['returncode'] != 0 for r in results):
            raise RuntimeError('Reference failed; scientific trials not started')
        for kind, _ in commands:
            m = read_json(out/kind/'measurement.json')
            if m['status'] != 'complete' or not m['exact_reference']:
                raise ValueError('Reference not complete')
        status['phase'] = 'concurrent_capacity'
        commands = [(f'probe_{k}_{j["dt_ms"]}', child(['prefix', '--out', str(out/f'probe_{k}_{j["dt_ms"]}'),
                    '--kind', 'probe', '--dt', str(j['dt_ms'])])) for k, (_, j) in enumerate(jobs)]
        results = batch(commands, out/'logs/capacity', min(deadline, time.monotonic()+7200), update)
        if any(r['returncode'] != 0 for r in results):
            raise RuntimeError('Concurrent capacity check failed; scientific trials not started')
        measures = [read_json(out/name/'measurement.json') for name, _ in commands]
        decision = gate(measures, deadline-time.monotonic(), memory, cpus)
        atomic_json(out/'capacity_gate.json', decision)
        if not decision['allowed']:
            status.update(status='budget_insufficient', explanation='Measured concurrent screen does not fit; four scientific trials not started')
            return
        status['phase'] = 'scientific'
        commands = [(j['id'], child(['worker', '--out', str(out), '--index', str(i)])) for i, j in jobs]
        results = batch(commands, out/'logs/scientific', deadline, update)
        for r, (_, spec) in zip(results, jobs):
            if r['returncode'] == 0:
                checked(out/'trials'/spec['id'], spec)
                status['scientific_completed'] += 1
        if status['scientific_completed'] != 4:
            raise RuntimeError('Some scientific workers failed; all outputs preserved')
        anchors = [j for j in plan['anchors'] if j['seed'] == 631401]
        for spec in anchors:
            shutil.copytree(ROOT/'anchors'/spec['id'], out/'trials'/spec['id'])
            checked(out/'trials'/spec['id'], spec)
        collect(out, dict(plan, jobs=anchors+[j for _, j in jobs]))
        agreement = read_json(out/'step_agreement.json')
        agreement['single_seed_two_halvings_pass'] = agreement.pop('final_two_halvings_meet_declared_criteria')
        for g in agreement['groups']:
            g['single_seed_meets_thresholds'] = g.pop('meets_declared_criteria')
        agreement.update(original_30_seed_requirement_established=False,
                         interpretation='One fixed seed only; not the three-seed pilot or thirty-seed convergence study.')
        atomic_json(out/'step_agreement.json', agreement)
        status.update(status='scientific_complete', phase='finished')
    except BaseException as error:
        status.update(status='failed_or_interrupted', error=repr(error))
        raise
    finally:
        # Count only hash-checked complete trials, including those finished before a deadline interrupt.
        verified = []
        for _, spec in jobs:
            path = out/'trials'/spec['id']/'manifest.json'
            if path.exists() and read_json(path).get('status') == 'complete':
                try:
                    checked(path.parent, spec)
                    verified.append(spec['id'])
                except (ValueError, OSError, KeyError) as error:
                    status.setdefault('verification_errors', []).append(str(error))
        status.update(scientific_completed=len(verified), completed_ids=verified, finished_utc=now())
        atomic_json(out/'progress.json', status)
        signal.signal(signal.SIGTERM, old)
        archive(out)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['run', 'verify', 'child'])
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.action == 'child':
        import resource
        resource.setrlimit(resource.RLIMIT_AS, (20_000_000_000, 20_000_000_000))
        os.execv(sys.executable, [sys.executable, *args.command])
    elif args.action == 'verify':
        select_jobs(package_plan())
    else:
        run()
