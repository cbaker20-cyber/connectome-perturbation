import json
import sys
from types import SimpleNamespace
import zipfile

import pytest

from scripts import pcdr_recover_pair as recovery


def measures():
    return [dict(status='complete', duration_s=.01, dt_ms=.00005,
                 seconds=s, peak_rss_bytes=3e9) for s in (700, 800)]


def test_pair_budget_boundary():
    assert recovery.fits(measures(), 160000)['allowed']
    assert not recovery.fits(measures(), 159999)['allowed']
    assert recovery.fits(measures(), 160000)['per_trial_screen_seconds'] == 160000


@pytest.mark.parametrize('field,value', [('seconds', float('nan')), ('seconds', 0),
    ('dt_ms', .000025), ('status', 'running'), ('peak_rss_bytes', 21e9),
    ('peak_rss_bytes', float('nan')), ('duration_s', 1)])
def test_invalid_probe_rejected(field, value):
    m = measures()
    m[0][field] = value
    with pytest.raises(ValueError):
        recovery.fits(m, 200000)


@pytest.fixture
def controller(tmp_path, monkeypatch):
    from scripts import pcdr_ccr_capacity, pcdr_resolution, pcdr_fine_ccr
    jobs = [dict(id=f'{condition}_{dt}_{seed}', seed=seed, condition=condition, dt_ms=dt)
            for seed in (631401, 631402, 631403)
            for condition in ('baseline', 'mode') for dt in (.00005, .000025)]
    anchors = [dict(id=f'anchor_{c}', seed=631401) for c in ('baseline', 'mode')]
    plan = dict(jobs=jobs, anchors=anchors, packages={})
    for name in ('package_manifest.json', 'smaller_plan.json', 'execution_plan.json'):
        (tmp_path/name).write_text('{}')
    for j in anchors:
        (tmp_path/'anchors'/j['id']).mkdir(parents=True)
    monkeypatch.setattr(recovery, 'ROOT', tmp_path)
    monkeypatch.setattr(recovery, 'package_plan', lambda: plan)
    monkeypatch.setattr(recovery, 'environment', lambda: {'packages': {}})
    monkeypatch.setattr(recovery.sys, 'version_info', (3, 11, 5))
    monkeypatch.setattr(recovery.os, 'uname', lambda: SimpleNamespace(nodename='cpn-c04-18'), raising=False)
    monkeypatch.setenv('SLURM_JOB_ID', '26427314')
    monkeypatch.setattr(pcdr_ccr_capacity, 'allocation', lambda: (4, 256000))
    monkeypatch.setattr(recovery.subprocess, 'check_output', lambda *a, **k: '2-07:00:00')
    monkeypatch.setitem(sys.modules, 'fcntl', SimpleNamespace(LOCK_EX=1, LOCK_NB=2, flock=lambda *a: None))
    monkeypatch.setattr(pcdr_fine_ccr, 'checked', lambda p, j: None)
    def collect(out, selected):
        assert len(selected['jobs']) == 4
        assert selected['steps_ms'] == [.0001, .00005]
        recovery.atomic_json(out/'step_agreement.json', {
            'groups': [{'meets_declared_criteria': True}],
            'final_two_halvings_meet_declared_criteria': None})
    monkeypatch.setattr(pcdr_fine_ccr, 'collect', collect)
    calls = []
    def batch(commands, directory, deadline, update):
        calls.append(commands)
        records = []
        for name, command in commands:
            if 'prefix' in command:
                target = tmp_path/'recovery_pair_20261013'/name
                target.mkdir(parents=True)
                m = dict(measures()[0], exact_reference=True)
                recovery.atomic_json(target/'measurement.json', m)
            else:
                index = int(command[-1])
                j = jobs[index]
                assert j['seed'] == 631401 and j['dt_ms'] == .00005
                target = tmp_path/'recovery_pair_20261013/trials'/j['id']
                target.mkdir(parents=True)
                recovery.atomic_json(target/'manifest.json', {'status': 'complete'})
            records.append(dict(name=name, returncode=0))
        update(records)
        return records
    monkeypatch.setattr(recovery, 'batch', batch)
    return tmp_path, calls


def test_controller_selects_pair_and_labels_limited_evidence(controller):
    root, calls = controller
    recovery.main()
    out = root/'recovery_pair_20261013'
    assert [len(c) for c in calls] == [2, 2, 2]
    status = json.loads((out/'progress.json').read_text())
    assert status['status'] == 'pair_complete' and status['scientific_completed'] == 2
    agreement = json.loads((out/'step_agreement.json').read_text())
    assert agreement['original_30_seed_requirement_established'] is False
    assert 'final_two_halvings_meet_declared_criteria' not in agreement
    assert agreement['groups'][0] == {'single_pair_meets_thresholds': True}
    with zipfile.ZipFile(root/'CCR_recovery_pair_20261013.zip') as archive:
        assert archive.testzip() is None
        assert 'results/recovery_source.py' in archive.namelist()
    with pytest.raises(FileExistsError):
        recovery.main()


def test_gate_refusal_preserves_record_without_launch(controller, monkeypatch):
    root, calls = controller
    monkeypatch.setattr(recovery, 'fits', lambda *a: {'allowed': False})
    recovery.main()
    assert len(calls) == 2
    status = json.loads((root/'recovery_pair_20261013/progress.json').read_text())
    assert status['status'] == 'budget_insufficient' and status['scientific_completed'] == 0


def test_reference_failure_prevents_science(controller, monkeypatch):
    root, calls = controller
    monkeypatch.setattr(recovery, 'batch', lambda *a: [{'returncode': 1}])
    with pytest.raises(RuntimeError, match='Reference worker failed'):
        recovery.main()
    status = json.loads((root/'recovery_pair_20261013/progress.json').read_text())
    assert status['status'] == 'failed_or_interrupted'
    assert status['scientific_completed'] == 0
    assert (root/'CCR_recovery_pair_20261013.zip').is_file()
