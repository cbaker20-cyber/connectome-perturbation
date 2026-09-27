import json
import numpy as np
import pandas as pd
import pytest
from scripts import pcdr_raw_diagnostics as diagnostic
from eigencircuits.common import fingerprint

IDS = ['720575940660219265', '720575940660219266', '720575940660219267']


def test_local_snapshot_hash_checks(tmp_path, monkeypatch):
    import hashlib
    import zipfile
    monkeypatch.setattr(diagnostic, 'ROOT', tmp_path)
    h = lambda data: hashlib.sha256(data).hexdigest()
    paths = ['input.csv', 'eigencircuits/common.py', 'perturbation/baseline.py']
    for name in paths:
        path = tmp_path / name
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(b'original')
    manifest = json.dumps({'files': {name: h(b'original') for name in paths}}).encode()
    plan = {'transfer_sha256': h(manifest), 'provenance': {'inputs': {'input.csv': h(b'original')}, 'sources': {name: h(b'original') for name in paths[1:]}}}
    archive = tmp_path / 'upload.zip'
    def write_archive(content):
        with zipfile.ZipFile(archive, 'w') as z:
            z.writestr('connectome/transfer_manifest.json', manifest)
            for name in paths: z.writestr('connectome/' + name, content)
    write_archive(b'original')
    diagnostic.verify_local_snapshot(archive, plan)
    (tmp_path / 'input.csv').write_bytes(b'changed')
    with pytest.raises(ValueError, match='Local input differs'):
        diagnostic.verify_local_snapshot(archive, plan)
    (tmp_path / 'input.csv').write_bytes(b'original')
    write_archive(b'changed')
    with pytest.raises(ValueError, match='Changed snapshot file'):
        diagnostic.verify_local_snapshot(archive, plan)


def test_process_readers_match_serial_and_propagate_errors(tmp_path):
    variant = dict(name='default', weight_scale=1., inhibitory_scale=1., strong_fraction=None)
    jobs = diagnostic.planned_jobs([{'name': 'baseline', 'ids': []}], [variant], [1, 2])
    provenance = {'inputs': {}, 'sources': {}, 'environment': {}}
    plan = {'jobs': jobs, 'provenance': provenance}
    (tmp_path / 'trials').mkdir()
    for job in jobs:
        path = tmp_path / 'trials' / job['trial_id']
        m = fixture_trial(path, name=job['trial_id'])
        for name in ['source_snapshot.zip', 'environment.json']:
            (path / name).write_bytes(b'fixture')
        m.update({key: job[key] for key in ['trial_id', 'seed', 'context', 'lesion_ids']})
        m.update({key: value for key, value in variant.items() if key != 'name'})
        m.update(status='complete', provenance=provenance, backend='numpy', input_hz=150., input_protocol='fixed_binomial_tape_v1',
                 outputs={p.name: diagnostic.digest(p) for p in path.iterdir()})
        (path / 'manifest.json').write_text(json.dumps(m))
    serial = list(diagnostic.checked_trials(tmp_path, plan, IDS, 1))
    parallel = list(diagnostic.checked_trials(tmp_path, plan, IDS, 2))
    for (j, (m, (rates, trace, row))), (jj, (mm, (rr, tt, rrow))) in zip(serial, parallel):
        assert j == jj and m == mm and row == rrow
        np.testing.assert_array_equal(rates, rr)
        np.testing.assert_array_equal(trace, tt)
    (tmp_path / 'trials' / jobs[1]['trial_id'] / 'environment.json').write_bytes(b'changed')
    with pytest.raises(ValueError, match='Corrupt output'):
        list(diagnostic.checked_trials(tmp_path, plan, IDS, 2))
def fixture_trial(path, times=(0., .0022, .9999), cells=(0, 0, 1), name='test'):
    path.mkdir(exist_ok=True)
    spikes = pd.DataFrame({'t': times, 'flywire_id': [IDS[i] for i in cells], 'trial': [name]*len(times), 'exp_name': ['sugar']*len(times)})
    counts = np.bincount(cells, minlength=3)
    rates = pd.DataFrame({'root_id': IDS, 'spike_count': counts, 'rate_hz': counts.astype(float)})
    events = pd.DataFrame({'tick': pd.Series([0], dtype='int64'), 'flywire_id': [IDS[1]]})
    for filename, frame in [('spikes', spikes), ('rates', rates), ('input_events', events), ('delivered_events', events)]:
        frame.to_parquet(path / (filename + '.parquet'), index=False)
    return dict(trial_id=name, context='sugar', dt_ms=.1, duration_s=1., input_ids=[IDS[1]], spike_count=len(times),
                recruited_noninput=int(np.count_nonzero(counts[[0, 2]])), spike_digest=fingerprint(spikes[['t', 'flywire_id']].to_dict('list')),
                input_digest=fingerprint(events.to_dict('list')), delivered_input_digest=fingerprint(events.to_dict('list')))


def test_known_counts_boundaries_and_large_ids(tmp_path):
    m = fixture_trial(tmp_path)
    rates, trace, row = diagnostic.inspect_trial(tmp_path, m, IDS)
    assert rates.tolist() == [2., 1., 0.]
    assert trace[0] == 2 and trace[99] == 1 and trace.sum() == 3
    assert row['min_noninput_isi_ms'] == pytest.approx(2.2)


@pytest.mark.parametrize('times,cells,error', [((0., .0021), (0, 0), 'refractory'), ((.00015,), (0,), 'grid'), ((1.,), (0,), 'time'), ((0., 0.), (1, 1), 'Duplicate')])
def test_invalid_timing(tmp_path, times, cells, error):
    m = fixture_trial(tmp_path, times, cells)
    with pytest.raises(ValueError, match=error):
        diagnostic.inspect_trial(tmp_path, m, IDS)


def test_empty_spikes_and_sensory_refractory_exception(tmp_path):
    m = fixture_trial(tmp_path, (), ())
    rates, trace, row = diagnostic.inspect_trial(tmp_path, m, IDS)
    assert rates.sum() == trace.sum() == 0 and row['min_noninput_isi_ms'] is None
    m = fixture_trial(tmp_path, (0., .0001), (1, 1))
    diagnostic.inspect_trial(tmp_path, m, IDS)


@pytest.mark.parametrize('failure', ['rates', 'float_ids', 'delivered', 'digest', 'duplicate_ids'])
def test_corrupt_tables(tmp_path, failure):
    m = fixture_trial(tmp_path)
    if failure in ['rates', 'float_ids', 'duplicate_ids']:
        frame = pd.read_parquet(tmp_path / 'rates.parquet')
        if failure == 'rates': frame.loc[0, 'rate_hz'] = 3.
        elif failure == 'float_ids': frame['root_id'] = frame.root_id.astype(float)
        else: frame.loc[2, 'root_id'] = IDS[0]
        frame.to_parquet(tmp_path / 'rates.parquet', index=False)
    elif failure == 'digest': m['input_digest'] = 'wrong'
    else:
        frame = pd.read_parquet(tmp_path / 'delivered_events.parquet')
        frame.loc[0, 'tick'] = 1
        frame.to_parquet(tmp_path / 'delivered_events.parquet', index=False)
    with pytest.raises(ValueError): diagnostic.inspect_trial(tmp_path, m, IDS)


@pytest.mark.parametrize('empty', [False, True])
def test_export_and_refuse_overwrite(tmp_path, monkeypatch, empty):
    study, out = tmp_path / 'study', tmp_path / 'diagnostic'
    study.mkdir()
    conditions = [{'name': 'baseline', 'ids': []}, {'name': 'mode', 'ids': [IDS[0]]}]
    variants = [{'name': 'default', 'weight_scale': 1., 'inhibitory_scale': 1., 'strong_fraction': None}]
    jobs = diagnostic.planned_jobs(conditions, variants, [1])
    plan = dict(conditions=conditions, variants=variants, design={'seeds': [1]}, jobs=jobs, transfer_sha256='hash', provenance={'environment': {}})
    (study / 'jobs.json').write_text(json.dumps(plan))
    manifests = {}
    (study / 'trials').mkdir()
    for job, times, cells in [(jobs[0], (0., .0022), (0, 0)), (jobs[1], (0.,), (0,))]:
        if empty: times, cells = (), ()
        manifests[job['trial_id']] = fixture_trial(study / 'trials' / job['trial_id'], times, cells, job['trial_id'])
    monkeypatch.setattr(diagnostic, 'verify', lambda: None)
    monkeypatch.setattr(diagnostic, 'digest', lambda p: 'hash')
    monkeypatch.setattr(diagnostic, 'neuron_ids', lambda: IDS)
    monkeypatch.setattr(diagnostic, 'sugar_ids', lambda: [IDS[1]])
    monkeypatch.setattr(diagnostic, 'validated', lambda p, j, plan: manifests[j['trial_id']])
    diagnostic.run(study, out)
    delta = pd.read_parquet(out / 'paired_deltas.parquet')
    assert delta.neuron_index.tolist() == ([] if empty else [0])
    assert delta.rate_or_delta_hz.tolist() == ([] if empty else [-1.])
    assert json.loads((out / 'audit.json').read_text())['status'] == 'complete'
    with pytest.raises(FileExistsError): diagnostic.run(study, out)
    (study / 'controller.lock').write_text('other worker')
    with pytest.raises(ValueError, match='locks'): diagnostic.run(study, tmp_path / 'other')
    (study / 'controller.lock').unlink()
    lesion_path = study / 'trials' / jobs[1]['trial_id']
    events = pd.read_parquet(lesion_path / 'input_events.parquet')
    events['tick'] = 1
    for name, key in [('input_events', 'input_digest'), ('delivered_events', 'delivered_input_digest')]:
        events.to_parquet(lesion_path / (name + '.parquet'), index=False)
        manifests[jobs[1]['trial_id']][key] = fingerprint(events.to_dict('list'))
    failed = tmp_path / 'failed'
    with pytest.raises(ValueError, match='different scheduled inputs'):
        diagnostic.run(study, failed)
    audit = json.loads((failed / 'audit.json').read_text())
    assert audit['status'] == 'failed' and audit['completed_trials'] == 1
