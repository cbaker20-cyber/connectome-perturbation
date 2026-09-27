import numpy as np
import pandas as pd
import pytest
from scripts.pcdr_followup_sim import input_tape, simulate


@pytest.mark.parametrize('dt', [.1, .05, .025])
def test_physical_times_and_counts_are_preserved(dt):
    events = pd.DataFrame({'tick': [0, 17, 9999], 'flywire_id': ['101', '102', '101']})
    tape = input_tape(events, ['101', '102'], dt)
    ticks, cells = np.nonzero(tape)
    np.testing.assert_allclose(ticks * dt, events.tick.to_numpy() * .1)
    assert cells.tolist() == [0, 1, 0] and tape.sum() == 3


@pytest.mark.parametrize('events', [pd.DataFrame({'tick': [10000], 'flywire_id': ['101']}),
    pd.DataFrame({'tick': [1, 1], 'flywire_id': ['101', '101']}),
    pd.DataFrame({'tick': [1.5], 'flywire_id': ['101']}),
    pd.DataFrame({'tick': [1], 'flywire_id': ['999']})])
def test_invalid_input_tapes_fail(events):
    with pytest.raises(ValueError): input_tape(events, ['101'], .05)


def test_same_step_matches_original_and_finer_steps_keep_events(tmp_path):
    from eigencircuits.trials import simulate as original
    comp, con = tmp_path / 'comp.csv', tmp_path / 'con.parquet'
    pd.DataFrame({'Completed': [1, 1, 1]}, index=[101, 102, 103]).to_csv(comp)
    pd.DataFrame({'Presynaptic_Index': [0, 1], 'Postsynaptic_Index': [1, 2],
                  'Excitatory x Connectivity': [15., -3.]}).to_parquet(con)
    expected, external, delivered = original(42, [0], [], duration_s=.02, completeness=comp, connectivity=con, return_delivered=True)
    events = external.rename(columns={'neuron_index': 'flywire_id'})
    events['flywire_id'] = '101'
    for dt in [.1, .05, .025]:
        tape = input_tape(events, ['101'], dt, duration_s=.02)
        spikes, schedule, actual = simulate(42, [0], [], tape=tape, duration_s=.02, dt_ms=dt,
            completeness=comp, connectivity=con, return_delivered=True)
        np.testing.assert_allclose(schedule.tick.to_numpy() * dt, external.tick.to_numpy() * .1)
        if dt == .1:
            pd.testing.assert_frame_equal(spikes, expected)
            pd.testing.assert_frame_equal(actual, delivered)


@pytest.mark.parametrize('fail', [False, True])
def test_controller_stages_and_failure_package(tmp_path, monkeypatch, fail):
    import json
    import zipfile
    from scripts import pcdr_followup as runner
    from scripts import pcdr_ccr_capacity as capacity
    study = tmp_path / 'old'
    study.mkdir()
    sources = ['scripts/pcdr_followup.py', 'scripts/pcdr_followup_sim.py']
    for name in sources:
        p = tmp_path / name; p.parent.mkdir(exist_ok=True); p.write_text('recorded')
    plan = {'original_jobs_sha256': 'hash', 'seeds': [1], 'mode_ids': ['101'], 'active_ids': ['101'],
            'sources': {name: 'hash' for name in sources}, 'jobs': [
                {'id': stage, 'stage': stage, 'source_trial': 'default_baseline_1'} for stage in ['replay', 'timestep', 'active29']]}
    (tmp_path / 'followup_plan.json').write_text(json.dumps(plan))
    (study / 'jobs.json').write_text(json.dumps({'jobs': [{'trial_id': 'default_baseline_1'}], 'provenance': {'environment': {'python': 'same', 'packages': {}}}}))
    monkeypatch.setattr(runner, 'ROOT', tmp_path)
    monkeypatch.setattr(runner, 'verify', lambda: None)
    monkeypatch.setattr(runner, 'digest', lambda p: 'hash')
    monkeypatch.setattr(runner, 'validated', lambda *args: None)
    monkeypatch.setattr(runner, 'environment', lambda: {'python': 'same', 'packages': {}})
    monkeypatch.setattr(runner, 'neuron_ids', lambda: ['101'])
    monkeypatch.setattr(capacity, 'allocation', lambda: (32, 192000))
    monkeypatch.setattr(pd, 'read_parquet', lambda p: pd.DataFrame({'root_id': ['101'], 'rate_hz': [1.]}))
    called, collected = [], []
    def execute(command, directory, *args, **kwargs):
        called.append(directory.name)
        return {'returncode': int(fail), 'timed_out': False}
    monkeypatch.setattr(runner, 'run_bounded', execute)
    monkeypatch.setattr(runner, 'collect', lambda *args: collected.append(True))
    out = tmp_path / 'new'
    if fail:
        with pytest.raises(RuntimeError, match='Worker failed'): runner.run(study, out, 1)
        assert called == ['replay'] and not collected
    else:
        runner.run(study, out, 1)
        assert called == ['replay', 'timestep', 'active29'] and collected == [True]
    with zipfile.ZipFile(out / 'CCR_followup_results.zip') as z:
        status = json.loads(z.read('progress.json'))
        assert status['status'] == ('failed' if fail else 'complete')
        assert 'logs/replay/process.json' in z.namelist()
    with pytest.raises(FileExistsError): runner.run(study, out, 1)


def test_collection_pairs_matching_steps_and_keeps_zero_neurons(tmp_path, monkeypatch):
    from scripts import pcdr_followup as runner
    study, out = tmp_path / 'old', tmp_path / 'new'
    ids = [runner.MN9, '720575940660219266']
    monkeypatch.setattr(runner, 'neuron_ids', lambda: ids)
    def rates(path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame({'root_id': [ids[0]], 'rate_hz': [value]}).to_parquet(path, index=False)
    for name, value in [('w120_i080_baseline_1', 1.), ('w120_i080_mode_1', 3.), ('default_baseline_1', 1.), ('default_mode_1', 3.)]:
        rates(study / 'trials' / name / 'rates.parquet', value)
    jobs = []
    for stage, dt, prefix in [('replay', .1, 'replay_'), ('timestep', .05, 'dt0p05_')]:
        for condition, value in [('baseline', 1.), ('mode', 3.)]:
            name = 'w120_i080_' + condition + '_1'
            jobs.append((dict(id=prefix+name, stage=stage, dt_ms=dt, source_trial=name, seed=1,
                             lesion_ids=[] if condition == 'baseline' else [ids[0]], baseline_trial='w120_i080_baseline_1'), value))
    jobs.append((dict(id='active29_1', stage='active29', dt_ms=.1, source_trial='default_mode_1', seed=1, lesion_ids=[ids[0]]), 2.))
    for spec, value in jobs:
        directory = out / 'trials' / spec['id']
        rates(directory / 'rates.parquet', value)
        runner.write(directory / 'manifest.json', {'status': 'complete', 'spec': spec, 'spike_count': int(value),
                     'mn9_hz': value, 'outputs': {'rates.parquet': runner.digest(directory / 'rates.parquet')}})
    runner.collect(study, out, {'jobs': [j for j, value in jobs], 'mode_ids': [ids[0]], 'seeds': [1]})
    result = runner.read(out / 'active29_summary.json')
    assert result['fixed_51_support']['A'] == 1.
    assert result['mean_vector_difference_l1_hz'] == 1.
    pairs = pd.read_csv(out / 'timestep_pairs.csv')
    assert pairs.dt_ms.tolist() == [.1, .05] and pairs.A.tolist() == [2., 2.]
    rates(out / 'trials' / 'active29_1' / 'rates.parquet', 4.)
    with pytest.raises(ValueError, match='Changed worker output'):
        runner.collect(study, out, {'jobs': [j for j, value in jobs], 'mode_ids': [ids[0]], 'seeds': [1]})
