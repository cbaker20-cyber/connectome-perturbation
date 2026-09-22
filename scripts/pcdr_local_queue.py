"""Serial, resumable local execution; independent of the chat and model quota."""
import argparse
import ctypes
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone


def stamp():
    return datetime.now(timezone.utc).isoformat()


def write(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2), encoding='utf-8')
    # Windows readers/virus scanners can briefly deny replacement of an open file.
    # Retry only the status replacement; never rerun a completed simulation here.
    for attempt in range(61):
        try:
            os.replace(temporary, path)
            return
        except PermissionError:
            if attempt == 60:
                raise
            time.sleep(0.5)


def available_memory():
    class Memory(ctypes.Structure):
        _fields_ = [('length', ctypes.c_ulong), ('load', ctypes.c_ulong)] + [
            (name, ctypes.c_ulonglong) for name in ['total', 'available', 'page', 'free_page', 'virtual', 'free_virtual', 'extended']]
    m = Memory(); m.length = ctypes.sizeof(m)
    if os.name == 'nt' and ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)):
        return m.available
    return None


def execute(command, root, env, log, timeout):
    """Kill the child tree on Windows timeout, including the venv redirector."""
    process = subprocess.Popen(command, cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT)
    try:
        result = process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        if os.name == 'nt':
            subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'], stdout=log, stderr=log)
        else:
            process.kill()
        process.wait()
        raise
    if result:
        raise subprocess.CalledProcessError(result, command)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--study', required=True)
    parser.add_argument('--features', required=True)
    parser.add_argument('--hours', type=float, default=30)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    study = Path(args.study).resolve()
    plan = json.loads((study/'jobs.json').read_text())
    logdir = study/'local_logs'; logdir.mkdir(exist_ok=True)
    statefile = study/'local_status.json'
    state = json.loads(statefile.read_text()) if statefile.exists() else {
        'started_utc': stamp(), 'deadline_epoch': time.time()+args.hours*3600,
        'status': 'starting', 'completed': 0, 'total': len(plan['jobs'])}
    state.update(pid=os.getpid(), controller=str(Path(__file__).resolve()))
    lock = study/'local_controller.lock'
    with lock.open('x') as f:
        f.write(str(os.getpid()))
    env = dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1', NUMEXPR_NUM_THREADS='1')
    # Request wakefulness while executing; do not change permanent power settings.
    if os.name == 'nt':
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000001)
    try:
        # Five seeds across all cells first; retain the full frozen thirty-seed study.
        jobs = sorted(plan['jobs'], key=lambda j: (j['seed'], j['index']))
        for job in jobs:
            target = study/'trials'/job['trial_id']/'manifest.json'
            if target.exists() and json.loads(target.read_text()).get('status') == 'complete':
                continue
            while True:
                if time.time() >= state['deadline_epoch'] or (study/'STOP').exists():
                    state.update(status='stopped_at_limit', updated_utc=stamp()); write(statefile, state)
                    return
                memory = available_memory()
                if shutil.disk_usage(study).free < 10*1024**3:
                    raise RuntimeError('Less than 10 GiB free disk; preserving completed runs.')
                if memory is None or memory >= 4*1024**3:
                    break
                state.update(status='waiting_for_memory', available_bytes=memory, updated_utc=stamp()); write(statefile, state)
                time.sleep(30)
            state.update(status='running', current_index=job['index'], current_trial=job['trial_id'], updated_utc=stamp())
            write(statefile, state)
            command = [sys.executable, '-m', 'eigencircuits.ccr', 'worker', '--study', str(study), '--index', str(job['index'])]
            with (logdir/f"{job['index']:04}.txt").open('a', encoding='utf-8') as f:
                f.write(stamp()+' '+json.dumps(command)+'\n'); f.flush()
                execute(command, root, env, f, min(600, max(1, state['deadline_epoch']-time.time())))
            state['completed'] = sum(json.loads(p.read_text()).get('status') == 'complete'
                                     for p in (study/'trials').glob('*/manifest.json'))
            write(statefile, state)
        state.update(status='collecting', updated_utc=stamp()); write(statefile, state)
        with (logdir/'collect.txt').open('a', encoding='utf-8') as f:
            execute([sys.executable, '-m', 'eigencircuits.ccr', 'collect', '--study', str(study),
                     '--features', str(Path(args.features).resolve())], root, env, f,
                    min(1200, max(1, state['deadline_epoch']-time.time())))
        state.update(status='complete', updated_utc=stamp()); write(statefile, state)
    except BaseException as error:
        state.update(status='failed', error=repr(error), updated_utc=stamp()); write(statefile, state)
        raise
    finally:
        if os.name == 'nt':
            ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)
        lock.unlink(missing_ok=True)


if __name__ == '__main__':
    main()
