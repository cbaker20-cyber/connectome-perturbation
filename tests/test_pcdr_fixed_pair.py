import copy
import json
import zipfile

import pytest

from scripts import pcdr_fixed_pair as fixed


def plan():
    with zipfile.ZipFile(fixed.ROOT/'exports/CCR_Four_Trial.zip') as archive:
        return json.loads(archive.read('connectome_four_trial/smaller_plan.json'))


def test_extension_changes_only_step_and_identifier():
    original = plan()
    saved = copy.deepcopy(original)
    seed, dt, jobs = fixed.select_pair(original)
    assert seed == 631401 and dt == .0000125
    assert original == saved
    for _, job in jobs:
        source = next(j for j in original['jobs'] if
                      j['seed'] == seed and j['dt_ms'] == .000025 and
                      j['condition'] == job['condition'])
        assert {k: v for k, v in job.items() if k not in ('dt_ms', 'id')} == {
            k: v for k, v in source.items() if k not in ('dt_ms', 'id')}


def test_reject_wrong_scope_and_missing_pair():
    with pytest.raises(ValueError):
        fixed.select_pair(plan(), 1)
    p = plan()
    p['jobs'] = [j for j in p['jobs'] if j['seed'] != 631401]
    with pytest.raises(ValueError):
        fixed.select_pair(p)


def measures():
    return [dict(status='complete', duration_s=.01, dt_ms=fixed.DT,
                 seconds=s, peak_rss_bytes=3e9) for s in (50, 60)]


def test_capacity_boundary_and_invalid_measurements():
    assert fixed.capacity(measures(), fixed.DT, 12000)['allowed']
    assert not fixed.capacity(measures(), fixed.DT, 11999)['allowed']
    for field, value in [('status', 'running'), ('seconds', float('nan')),
                         ('peak_rss_bytes', 17e9), ('dt_ms', .000025)]:
        m = measures()
        m[1][field] = value
        with pytest.raises(ValueError):
            fixed.capacity(m, fixed.DT, 12000)


def test_allocation_requires_exact_single_job(monkeypatch):
    monkeypatch.setattr(fixed.subprocess, 'check_output', lambda *a, **k: '123|1-00:00:00\n')
    assert fixed.allocation_seconds('123') == 86400
    for output in ('', '124|01:00:00', '123|01:00:00\n124|01:00:00'):
        monkeypatch.setattr(fixed.subprocess, 'check_output', lambda *a, **k: output)
        with pytest.raises(ValueError):
            fixed.allocation_seconds('123')


def test_unknown_prefix_refused_before_simulation(tmp_path):
    with pytest.raises(ValueError, match='Unknown prefix'):
        fixed.prefix_worker(tmp_path/'unused', 'invalid', fixed.DT)
    assert not (tmp_path/'unused').exists()
