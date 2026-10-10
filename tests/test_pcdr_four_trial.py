import copy
import json
from pathlib import Path
import sys
import time

import pytest

from scripts.pcdr_four_trial import batch, gate, select_jobs


def measures():
    return [dict(dt_ms=dt, duration_s=.01, status='complete', seconds=seconds, peak_rss_bytes=3e9)
            for dt, seconds in [(.00005, 480), (.00005, 500), (.000025, 950), (.000025, 1000)]]


def test_gate_uses_slowest_concurrent_worker_not_serial_sum():
    result = gate(measures(), 210000, 92000, 8)
    assert result['allowed']
    assert result['per_trial_screen_seconds'] == {'5e-05': 100000, '2.5e-05': 200000}
    assert not gate(measures(), 199999, 92000, 8)['allowed']
    assert not gate(measures(), 210000, 91999, 8)['allowed']
    assert not gate(measures(), 210000, 92000, 7)['allowed']


@pytest.mark.parametrize('field,value', [('seconds', float('nan')), ('seconds', -1),
    ('duration_s', 1), ('status', 'running'), ('peak_rss_bytes', 17e9)])
def test_gate_rejects_invalid_measurement(field, value):
    m = measures(); m[0][field] = value
    with pytest.raises(ValueError):
        gate(m, 210000, 92000, 8)


def test_panel_excludes_other_seeds_and_rejects_duplicate():
    jobs = [dict(seed=s, condition=c, dt_ms=d) for s in (631401, 631402, 631403)
            for c in ('baseline', 'mode') for d in (.00005, .000025)]
    assert len(select_jobs({'jobs': jobs})) == 4
    jobs[0] = copy.deepcopy(jobs[1])
    with pytest.raises(ValueError):
        select_jobs({'jobs': jobs})


def test_batch_preserves_success_and_failed_worker(tmp_path):
    records = batch([('ok', [sys.executable, '-c', 'print(42)']),
                     ('fail', [sys.executable, '-c', 'raise RuntimeError("intentional")'])],
                    tmp_path/'logs', time.monotonic()+15)
    assert [r['returncode'] for r in records] == [0, 1]
    assert '42' in (tmp_path/'logs/ok/stdout.txt').read_text()
    assert 'intentional' in (tmp_path/'logs/fail/stderr.txt').read_text()
    with pytest.raises(FileExistsError):
        batch([], tmp_path/'logs', time.monotonic()+15)


def test_batch_timeout_stops_owned_children_and_records_exit(tmp_path):
    with pytest.raises(TimeoutError):
        batch([('slow', [sys.executable, '-c', 'import time;time.sleep(60)'])],
              tmp_path/'logs', time.monotonic()+.5)
    r = json.loads((tmp_path/'logs/slow/process.json').read_text())
    assert r['returncode'] is not None and r['status'] == 'interrupted'


def test_batch_callback_interruption_cleans_up(tmp_path):
    def interrupt(records):
        if any(r['status'] == 'running' for r in records):
            raise KeyboardInterrupt('intentional controller interrupt')
    with pytest.raises(KeyboardInterrupt):
        batch([('slow', [sys.executable, '-c', 'import time;time.sleep(60)'])],
              tmp_path/'logs', time.monotonic()+15, interrupt)
    r = json.loads((tmp_path/'logs/slow/process.json').read_text())
    assert r['returncode'] is not None


def test_partial_launch_failure_cleans_first_worker(tmp_path):
    with pytest.raises(FileNotFoundError):
        batch([('slow', [sys.executable, '-c', 'import time;time.sleep(60)']),
               ('missing', [str(tmp_path/'not_a_program')])], tmp_path/'logs', time.monotonic()+15)
    r = json.loads((tmp_path/'logs/slow/process.json').read_text())
    assert r['returncode'] is not None
