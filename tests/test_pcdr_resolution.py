import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from scripts import pcdr_resolution as runner
from scripts.pcdr_followup_sim import input_tape as previous_tape


@pytest.mark.parametrize('dt', [.1, .05, .025, .0125, .00625])
def test_same_physical_event_times_and_no_extra_jumps(dt):
    events = pd.DataFrame({'tick': [0, 137, 9999], 'flywire_id': ['101', '102', '101']})
    tape = runner.input_tape(events, ['101', '102'], dt)
    ticks, cells = np.nonzero(tape)
    np.testing.assert_allclose(ticks * dt, events.tick * .1)
    assert cells.tolist() == [0, 1, 0] and tape.sum() == 3
    if dt >= .025: np.testing.assert_array_equal(tape, previous_tape(events, ['101', '102'], dt))


@pytest.mark.parametrize('value,expected', [('04:03:02', 14582), ('12:34', 754), ('1-02:03:04', 93784)])
def test_remaining_time(value, expected):
    assert runner.seconds_left(value) == expected


@pytest.mark.parametrize('value', ['', 'UNLIMITED', 'INVALID', 'abc'])
def test_unavailable_remaining_time_fails(value):
    with pytest.raises(ValueError): runner.seconds_left(value)


def test_frozen_plan_has_paired_baselines_and_full_default_coverage():
    plan = json.loads(Path('docs/pcdr/CCR_RESOLUTION_PLAN.json').read_text())
    jobs = plan['jobs']
    assert len(jobs) == len({j['id'] for j in jobs}) == 530
    keys = {(j['stage'], j['dt_ms'], j['variant'], j['condition'], j['seed']) for j in jobs}
    for j in jobs:
        if j['condition'] != 'baseline':
            assert (j['stage'], j['dt_ms'], j['variant'], 'baseline', j['seed']) in keys
    default = [j for j in jobs if j['stage'] == 'default']
    assert len(default) == 480
    assert len({j['seed'] for j in default}) == 30
    assert {j['dt_ms'] for j in default} == {.05, .025}
    assert len(plan['active_ids']) == 29 and set(plan['active_ids']) < set(plan['mode_ids'])


@pytest.mark.parametrize('fail', [False, True])
def test_stage_order_failure_stop_and_full_evidence_package(tmp_path, monkeypatch, fail):
    from scripts import pcdr_ccr_capacity as capacity
    study = tmp_path / 'old'; study.mkdir()
    script = tmp_path / 'new.py'; script.write_text('saved source')
    original = {'jobs': [{'trial_id': 'old'}], 'provenance': {'environment': {'python': 'same', 'packages': {}}}}
    (study / 'jobs.json').write_text(json.dumps(original))
    plan = {'original_jobs_sha256': 'hash', 'previous_plan_sha256': 'hash', 'sources': {'new.py': 'hash'},
            'jobs': [dict(id=s, stage=s, source_trial='old') for s in ['replay', 'finer', 'default']]}
    (tmp_path / 'resolution_plan.json').write_text(json.dumps(plan))
    monkeypatch.setattr(runner, 'ROOT', tmp_path)
    monkeypatch.setattr(runner, 'verify', lambda: None)
    monkeypatch.setattr(runner, 'digest', lambda p: 'hash')
    monkeypatch.setattr(runner, 'validated', lambda *a: None)
    monkeypatch.setattr(runner, 'environment', lambda: {'python': 'same', 'packages': {}})
    monkeypatch.setattr(runner, 'neuron_ids', lambda: ['101'])
    monkeypatch.setattr(capacity, 'allocation', lambda: (24, 192000))
    monkeypatch.setenv('SLURM_JOB_ID', '123')
    monkeypatch.setattr(runner.subprocess, 'check_output', lambda *a, **k: '04:00:00')
    called, collected = [], []
    def execute(command, directory, *a, **k):
        called.append(directory.name)
        p = directory.parent.parent / 'trials' / directory.name
        p.mkdir(parents=True); (p / 'spikes.parquet').write_bytes(b'complete evidence fixture')
        return {'returncode': int(fail), 'timed_out': False}
    monkeypatch.setattr(runner, 'run_bounded', execute)
    monkeypatch.setattr(runner, 'collect', lambda *a: collected.append(True))
    out = tmp_path / 'new'
    if fail:
        with pytest.raises(RuntimeError, match='Worker failed'): runner.run(study, out, 3.5)
        assert called == ['replay'] and not collected
    else:
        runner.run(study, out, 3.5)
        assert called == ['replay', 'finer', 'default'] and collected == [True]
    import zipfile
    with zipfile.ZipFile(out / 'CCR_resolution_results.zip') as z:
        assert 'trials/replay/spikes.parquet' in z.namelist()
        status = json.loads(z.read('progress.json'))
        assert status['budget_seconds'] == 3.5 * 3600
        assert status['status'] == ('failed' if fail else 'complete')
    with pytest.raises(FileExistsError): runner.run(study, out, 3.5)


def test_collection_keeps_actual_and_fixed_support_separate(tmp_path, monkeypatch):
    ids = [runner.MN9, '720575940660219266']
    monkeypatch.setattr(runner, 'neuron_ids', lambda: ids)
    jobs = []
    for condition, values, lesion in [('baseline', [1., 1.], []), ('mode', [3., 3.], ids), ('active29', [2., 1.], ids[:1])]:
        j = dict(id=condition, condition=condition, seed=1, stage='default', dt_ms=.05, variant='default', lesion_ids=lesion)
        jobs.append(j)
        p = tmp_path / 'trials' / condition; p.mkdir(parents=True)
        pd.DataFrame({'root_id': ids, 'rate_hz': values}).to_parquet(p / 'rates.parquet', index=False)
        runner.write(p / 'manifest.json', {'spec': j, 'status': 'complete', 'outputs': {'rates.parquet': runner.digest(p / 'rates.parquet')},
                     'spike_count': int(sum(values)), 'mn9_hz': values[0], 'recruited_noninput': 2, 'peak_rss_bytes': 100,
                     'physical_input_digest': 'same'})
    runner.collect(tmp_path, {'jobs': jobs, 'mode_ids': ids})
    rows = runner.read(tmp_path / 'mean_results.json')['rows']
    small = next(r for r in rows if r['condition'] == 'active29')
    assert small['A'] == 1. and small['fixed_mode']['A'] == .5
    assert small['total_absolute_sum_hz'] == 1. and small['F'] == 1.
    manifest = tmp_path / 'trials' / 'active29' / 'manifest.json'
    data = runner.read(manifest); data['physical_input_digest'] = 'different'; runner.write(manifest, data)
    with pytest.raises(ValueError, match='Unpaired input'): runner.collect(tmp_path, {'jobs': jobs, 'mode_ids': ids})
