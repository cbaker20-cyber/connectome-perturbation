"""Run one research worker with an external deadline and retained logs."""
import os
from pathlib import Path
import subprocess
import time


def run_bounded(command, directory, timeout_seconds, cwd=None):
    if timeout_seconds <= 0:
        raise ValueError('timeout must be positive')
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
    with (directory/'stdout.txt').open('w') as stdout, (directory/'stderr.txt').open('w') as stderr:
        process = subprocess.Popen(command, cwd=cwd, stdout=stdout, stderr=stderr,
                                   creationflags=flags, start_new_session=os.name != 'nt')
        expired = False
        cleanup = None
        try:
            process.wait(timeout=timeout_seconds)
        except subprocess.TimeoutExpired:
            expired = True
            if os.name == 'nt':
                # The venv launcher can have a Python child; stop this owned tree.
                killed = subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'],
                                        capture_output=True, text=True, timeout=15,
                                        creationflags=flags)
                cleanup = {'returncode': killed.returncode, 'stdout': killed.stdout,
                           'stderr': killed.stderr}
            else:
                import signal
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            process.wait(timeout=15)
    return {'command': list(command), 'pid': process.pid, 'timed_out': expired,
            'returncode': process.returncode, 'elapsed_seconds': time.monotonic()-started,
            'deadline_seconds': timeout_seconds, 'cleanup': cleanup}
