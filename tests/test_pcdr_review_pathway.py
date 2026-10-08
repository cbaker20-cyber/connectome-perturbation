import numpy as np
import pandas as pd
import pytest

from scripts.pcdr_review_pathway import spike_counts, validate_switch


def test_window_boundaries_and_prior_recruitment():
    frame = pd.DataFrame({'t': [.1, .1001, .649, .650, .652, .729, .730],
                          'flywire_id': ['input', 'input', 'a', 'b', 'a', 'b', 'c']})
    counts, _ = spike_counts(frame, ['input'], .0002, {'input', 'a', 'b', 'c'})
    assert counts == dict(noninput_spikes_650_730=3, newly_recruited_noninput_650_730=1)


@pytest.mark.parametrize('times,ids,message', [
    ([.1, .1], ['a', 'a'], 'Duplicate'),
    ([.1, .1001], ['a', 'a'], 'refractory'),
    ([.1000001], ['a'], 'Off-grid'),
    ([np.nan], ['a'], 'Invalid'),
    ([.75], ['a'], 'Invalid'),
    ([.2, .1], ['a', 'b'], 'Unsorted'),
    ([.1], ['unknown'], 'Unknown'),
    ([.1], [720575940628695043.0], 'strings'),
])
def test_invalid_spikes(times, ids, message):
    with pytest.raises(ValueError, match=message):
        spike_counts(pd.DataFrame({'t': times, 'flywire_id': ids}), [], .0002, {'a', 'b'})


def test_empty_spikes():
    counts, _ = spike_counts(pd.DataFrame({'t': pd.Series(dtype=float),
                                          'flywire_id': pd.Series(dtype=str)}), [], .0002, set())
    assert counts == dict(noninput_spikes_650_730=0, newly_recruited_noninput_650_730=0)


@pytest.mark.parametrize('remove', [False, True])
def test_switch_record_and_invalid_changes(remove):
    from copy import deepcopy
    ids = ['720575940628695043','720575940629667639','720575940623862015']
    connections = pd.DataFrame({'Presynaptic_Index':[0,0], 'Postsynaptic_Index':[1,2],
                                'Excitatory x Connectivity':[286,237]})
    before = [94.38,78.21]
    valid = dict(switch_ms=600, remove=remove, pairs=[[0,1],[0,2]],
                 weights_before_mv=before, weights_after_mv=[0.,0.] if remove else before)
    validate_switch(valid, remove, ids, connections)
    for key, bad in [('switch_ms',599), ('remove',not remove), ('pairs',[[0,2],[0,1]]),
                     ('weights_before_mv',[94.,78.21]), ('weights_after_mv',[1.,1.]),
                     ('pairs',[[0.0,1],[0,2]])]:
        altered = deepcopy(valid); altered[key] = bad
        with pytest.raises(ValueError): validate_switch(altered, remove, ids, connections)
    with pytest.raises(ValueError):
        validate_switch(valid,remove,ids,pd.concat([connections,connections.iloc[:1]]))


@pytest.fixture
def separate_archive(tmp_path, monkeypatch):
    import json
    import zipfile
    from scripts import pcdr_review_pathway as reviewer

    # Tiny, explicitly synthetic records exercise archive checks without a simulation.
    monkeypatch.setattr(reviewer, 'ROOT', tmp_path)
    ids = ['720575940628695043', '720575940629667639', '720575940623862015']
    pd.DataFrame(index=ids).to_csv(tmp_path/'2023_03_23_completeness_630_final.csv')
    pd.DataFrame({'Presynaptic_Index': [0, 0], 'Postsynaptic_Index': [1, 2],
                  'Excitatory x Connectivity': [286, 237]}).to_parquet(
                      tmp_path/'2023_03_23_connectivity_630_final.parquet')
    reference = tmp_path/'reference'
    reference.mkdir()
    tape = pd.DataFrame({'tick': pd.Series(dtype='int64'), 'flywire_id': pd.Series(dtype=str)})
    tape.to_parquet(reference/'input_events.parquet')
    spikes = pd.DataFrame({'t': [.1, .65], 'flywire_id': ids[:2]})
    encode = lambda v: json.dumps(v).encode()
    plan = encode(dict(seed=631430, variant='w120_i080', condition='mn9_only',
                       reference_files={}, model_files={}, packages={}, input_ids=[]))
    (reference/'diagnostic_plan.json').write_bytes(plan)
    contents = {'diagnostic_plan.json': plan, 'source/model.py': b'# synthetic fixture\n',
                'installed-libraries.txt': b''}
    results, manifests = [], []
    for dt in [.0004, .0002]:
        old = reference/'reference'/str(dt)
        old.mkdir(parents=True)
        spikes.to_parquet(old/'spikes.parquet')
        tape.to_parquet(old/'delivered_events.parquet')
        for c in ['late_reference', 'late_edges', 'late_g', 'late_h']:
            trial = f'{c}_{dt}'
            selected = [1] if c == 'late_g' else [2] if c == 'late_h' else [1, 2]
            before = [{1: 94.38, 2: 78.21}[i] for i in selected]
            endpoints = dict(noninput_spikes_650_730=1, newly_recruited_noninput_650_730=1,
                            source_times_ms={ids[0]: [100.], ids[1]: [650.], ids[2]: []})
            outputs = {'spikes.parquet': spikes.to_parquet(), 'scheduled_events.parquet': tape.to_parquet(),
                       'delivered_events.parquet': tape.to_parquet(), 'endpoints.json': encode(endpoints),
                       'simulation_progress.json': encode(dict(simulated_ms=750)),
                       'switch.json': encode(dict(switch_ms=600, remove=c != 'late_reference',
                            pairs=[[0, i] for i in selected], weights_before_mv=before,
                            weights_after_mv=before if c == 'late_reference' else [0.] * len(selected)))}
            m = dict(status='complete', dt_ms=dt, condition=c, duration_ms=750,
                     plan_sha256=reviewer.digest(plan), exact_delivered_input=True,
                     environment=dict(packages={}, python='3.11.5'),
                     sources={'model.py': reviewer.digest(contents['source/model.py'])},
                     outputs={n: reviewer.digest(v) for n, v in outputs.items()},
                     exact_pre_switch_spikes=True, switch_ms=600, exact_reference_spikes=True,
                     elapsed_seconds=1, peak_rss_bytes=1, finished_utc='synthetic')
            contents.update({trial+'/'+n: v for n, v in outputs.items()})
            contents[trial+'/manifest.json'] = encode(m)
            contents['logs/'+trial+'/process.json'] = encode(dict(returncode=0, timed_out=False))
            contents['logs/'+trial+'/stdout.txt'] = b''
            contents['logs/'+trial+'/stderr.txt'] = b''
            results.append(dict(dt_ms=dt, condition=c, **endpoints))
            manifests.append(m)
    contents['summary.json'] = encode(dict(status='complete', duration_ms=750,
                                         results=results, trials=manifests))
    package = tmp_path/'upload.zip'
    with zipfile.ZipFile(package, 'w') as z:
        z.writestr('connectome_separate_pathway/diagnostic_plan.json', plan)
        z.writestr('connectome_separate_pathway/model.py', contents['source/model.py'])
    return contents, package, reference


@pytest.mark.parametrize('fault,message', [
    (None, None), ('missing', 'trial count'), ('duplicate_condition', 'duplicate condition'),
    ('target', 'switched connections'), ('time', 'switch specification'),
    ('stale_source', 'differs from upload'), ('changed_output', 'Output hash'),
    ('extra_file', 'archive inventory'), ('duplicate_path', 'Duplicate archive'),
])
def test_separate_archive_checks(separate_archive, tmp_path, fault, message):
    import json
    import zipfile
    from scripts.pcdr_review_pathway import review, digest

    contents, package, reference = separate_archive
    trial = 'late_g_0.0004'
    summary = json.loads(contents['summary.json'])
    encode = lambda v: json.dumps(v).encode()
    if fault == 'missing':
        summary['results'].pop()
    elif fault == 'duplicate_condition':
        summary['results'][-1] = summary['results'][0]
    elif fault in ['target', 'time']:
        name = trial+'/switch.json'
        switch = json.loads(contents[name])
        switch.update(pairs=[[0, 2]] if fault == 'target' else [[0, 1]],
                      switch_ms=599 if fault == 'time' else 600)
        contents[name] = encode(switch)
        for m in summary['trials']:
            if (m['condition'], m['dt_ms']) == ('late_g', .0004):
                m['outputs']['switch.json'] = digest(contents[name])
                contents[trial+'/manifest.json'] = encode(m)
    elif fault == 'stale_source':
        contents['source/model.py'] = b'# different source\n'
        for m in summary['trials']:
            m['sources']['model.py'] = digest(contents['source/model.py'])
            contents[f"{m['condition']}_{m['dt_ms']}/manifest.json"] = encode(m)
    elif fault == 'changed_output':
        contents[trial+'/spikes.parquet'] += b'changed'
    elif fault == 'extra_file':
        contents['unexpected.txt'] = b''
    contents['summary.json'] = encode(summary)
    archive = tmp_path/'synthetic.zip'
    with zipfile.ZipFile(archive, 'w') as z:
        for name, data in contents.items():
            z.writestr(name, data)
        if fault == 'duplicate_path':
            with pytest.warns(UserWarning, match='Duplicate'):
                z.writestr('summary.json', contents['summary.json'])
    if fault:
        with pytest.raises(ValueError, match=message):
            review(archive, package, reference, separate=True)
    else:
        result = review(archive, package, reference, separate=True)
        assert result['checks_passed'] and len(result['results']) == 8
        assert len(result['comparisons']) == 6


@pytest.mark.parametrize('fault', [None, 'changed_bytes', 'changed_endpoint', 'changed_spike'])
def test_previous_experiment_comparison(separate_archive, tmp_path, fault):
    import io
    import json
    import zipfile
    from scripts.pcdr_compare_separate import compare
    from scripts.pcdr_review_pathway import digest

    contents, _, _ = separate_archive
    archive, previous = tmp_path/'current.zip', tmp_path/'previous.zip'
    with zipfile.ZipFile(archive, 'w') as z:
        for name, data in contents.items():
            z.writestr(name, data)
    if fault == 'changed_endpoint':
        name = 'late_edges_0.0004/endpoints.json'
        endpoint = json.loads(contents[name])
        endpoint['noninput_spikes_650_730'] += 1
        contents[name] = json.dumps(endpoint).encode()
    if fault == 'changed_spike':
        name = 'late_edges_0.0004/spikes.parquet'
        spikes = pd.read_parquet(io.BytesIO(contents[name]))
        spikes.loc[1, 't'] = .66
        contents[name] = spikes.to_parquet()
    with zipfile.ZipFile(previous, 'w') as z:
        for name, data in contents.items():
            z.writestr(name, data)
    reviews = [dict(checks_passed=True, archive_sha256=digest(p.read_bytes())) for p in [archive, previous]]
    if fault == 'changed_bytes':
        with previous.open('ab') as f:
            f.write(b'changed')
    if fault:
        error = AssertionError if fault == 'changed_spike' else ValueError
        with pytest.raises(error):
            compare(archive, previous, *reviews)
    else:
        result = compare(archive, previous, *reviews)
        assert len(result['repeated_conditions']) == 4
        assert all(v['noninput_spikes_730_750'] == 0 for v in result['supplementary_windows'])
        assert all(v['identical_spike_events'] for v in result['single_comparisons'])
