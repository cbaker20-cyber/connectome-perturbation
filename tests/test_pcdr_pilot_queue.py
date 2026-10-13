import json
from pathlib import Path
from types import SimpleNamespace
import sys
import zipfile

import pytest

from scripts import pcdr_pilot_queue as queue


def plan():
    return {'packages': {}, 'jobs': [dict(id=f'{s}_{d}_{c}', seed=s, dt_ms=d, condition=c)
        for s in (631401, 631402, 631403) for d in (.00005, .000025)
        for c in ('baseline', 'mode')]}


def probe(dt=.000025):
    return dict(status='complete', duration_s=.01, dt_ms=dt, seconds=1200, peak_rss_bytes=6e9)


def test_remaining_panel_is_exact_and_excludes_active_pair():
    selected = [j for task in range(5) for _, j in queue.select_pair(plan(), task)[2]]
    assert len({j['id'] for j in selected}) == 10
    assert not any(j['seed'] == 631401 and j['dt_ms'] == .00005 for j in selected)
    with pytest.raises(ValueError):
        queue.select_pair(plan(), 5)
    p = plan()
    p['jobs'].append(p['jobs'][2])
    with pytest.raises(ValueError):
        queue.select_pair(p, 0)


def test_capacity_boundary_and_slowest_worker():
    m = [probe(), dict(probe(), seconds=1250)]
    assert queue.capacity(m, .000025, 250000)['allowed']
    assert not queue.capacity(m, .000025, 249999)['allowed']
    assert queue.capacity(m, .000025, 250000)['per_trial_screen_seconds'] == 250000


@pytest.mark.parametrize('field,value', [('seconds', float('nan')), ('seconds', 0),
    ('peak_rss_bytes', float('inf')), ('peak_rss_bytes', 17e9),
    ('status', 'running'), ('dt_ms', .00005), ('duration_s', 1)])
def test_invalid_probe(field, value):
    with pytest.raises(ValueError):
        queue.capacity([probe(), dict(probe(), **{field: value})], .000025, 250000)


def test_invalid_budget():
    with pytest.raises(ValueError):
        queue.capacity([probe(), probe()], .000025, float('inf'))


def test_retry_only_after_unstarted_refusal(tmp_path, monkeypatch):
    monkeypatch.setattr(queue, 'ROOT', tmp_path)
    prior = tmp_path/'queued_pair_0_20261013'
    prior.mkdir()
    queue.atomic_json(prior/'progress.json', dict(status='budget_insufficient', scientific_completed=0))
    assert queue.output_folder(0, .000025, 'sapphire').name == 'sapphire_pair_0_20261013'
    with pytest.raises(ValueError, match='scope'):
        queue.output_folder(1, .00005, 'sapphire')
    (prior/'logs/scientific').mkdir(parents=True)
    with pytest.raises(ValueError, match='Prior scientific launch'):
        queue.output_folder(0, .000025, 'sapphire')
    queue.atomic_json(prior/'progress.json', dict(status='running', scientific_completed=0))
    with pytest.raises(ValueError, match='preserved refusal'):
        queue.output_folder(0, .000025, 'sapphire')


def write_prefix(folder, dt=.0001):
    folder.mkdir(parents=True)
    files = {}
    for name in ('spikes.parquet', 'scheduled.parquet', 'delivered.parquet'):
        (folder/name).write_bytes(b'known output bytes')
        files[name] = queue.sha256(folder/name)
    queue.atomic_json(folder/'measurement.json', dict(probe(dt), outputs=files, exact_reference=True))


def test_prefix_hash_and_output_set(tmp_path):
    folder = tmp_path/'prefix'
    write_prefix(folder)
    assert queue.measurement(folder, reference=True)['exact_reference']
    (folder/'spikes.parquet').write_bytes(b'changed')
    with pytest.raises(ValueError, match='Changed prefix'):
        queue.measurement(folder)
    m = json.loads((folder/'measurement.json').read_text())
    m['outputs'] = {}
    queue.atomic_json(folder/'measurement.json', m)
    with pytest.raises(ValueError, match='output set'):
        queue.measurement(folder)


@pytest.fixture
def controller(tmp_path, monkeypatch):
    from scripts import pcdr_ccr_capacity, pcdr_fine_ccr
    p = plan()
    for name in ('package_manifest.json', 'smaller_plan.json', 'execution_plan.json'):
        (tmp_path/name).write_text('{}')
    monkeypatch.setattr(queue, 'ROOT', tmp_path)
    monkeypatch.setattr(queue, 'package_plan', lambda: p)
    monkeypatch.setattr(queue, 'environment', lambda: {'packages': {}})
    monkeypatch.setattr(queue.sys, 'version_info', (3, 11, 5))
    monkeypatch.setattr(queue.os, 'uname', lambda: SimpleNamespace(nodename='cpn-test'), raising=False)
    for name, value in {'SLURM_ARRAY_TASK_ID': '0', 'SLURM_ARRAY_JOB_ID': '1234', 'SLURM_JOB_ID': '1235'}.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setitem(sys.modules, 'fcntl', SimpleNamespace(LOCK_EX=1, LOCK_NB=2, flock=lambda *a: None))
    monkeypatch.setattr(pcdr_ccr_capacity, 'allocation', lambda: (4, 64000))
    monkeypatch.setattr(queue.subprocess, 'check_output', lambda *a, **k: '3-00:00:00')
    monkeypatch.setattr(pcdr_fine_ccr, 'checked', lambda *a: None)
    calls = []
    def batch(commands, directory, deadline, update):
        calls.append(commands)
        for name, cmd in commands:
            out = Path(cmd[cmd.index('--out')+1])
            if 'prefix' in cmd:
                write_prefix(out, float(cmd[-1]))
            else:
                spec = p['jobs'][int(cmd[-1])]
                target = out/'trials'/spec['id']
                target.mkdir(parents=True)
                queue.atomic_json(target/'manifest.json', {'status': 'complete'})
        records = [dict(returncode=0, name=n) for n, _ in commands]
        update(records)
        return records
    monkeypatch.setattr(queue, 'batch', batch)
    return tmp_path, calls


def test_controller_completes_only_selected_pair(controller):
    root, calls = controller
    queue.main()
    assert len(calls) == 3 and all(len(c) == 2 for c in calls)
    status = json.loads((root/'queued_pair_0_20261013/progress.json').read_text())
    assert status['status'] == 'pair_complete' and status['scientific_completed'] == 2
    assert 'Convergence not established' in status['interpretation']
    with zipfile.ZipFile(root/'CCR_queued_pair_0_20261013.zip') as z:
        assert z.testzip() is None
        assert 'results/queue_source.py' in z.namelist()
    with pytest.raises(FileExistsError):
        queue.main()


def test_capacity_refusal_never_starts_science(controller, monkeypatch):
    root, calls = controller
    monkeypatch.setattr(queue, 'capacity', lambda *a: {'allowed': False})
    queue.main()
    assert len(calls) == 2
    status = json.loads((root/'queued_pair_0_20261013/progress.json').read_text())
    assert status['status'] == 'budget_insufficient' and status['scientific_completed'] == 0


def test_failed_reference_preserved(controller, monkeypatch):
    root, calls = controller
    monkeypatch.setattr(queue, 'batch', lambda *a: [{'returncode': 1}])
    with pytest.raises(RuntimeError, match='Reference worker failed'):
        queue.main()
    status = json.loads((root/'queued_pair_0_20261013/progress.json').read_text())
    assert status['status'] == 'failed_or_interrupted' and status['scientific_completed'] == 0
    assert (root/'CCR_queued_pair_0_20261013.zip').exists()
