"""Check the returned pathway archive and recalculate its declared measurements."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import zipfile

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def spike_counts(frame, inputs, dt, valid_ids):
    require(set(frame.columns) == {'t', 'flywire_id'}, 'Unexpected spike columns')
    require(frame.flywire_id.map(lambda v: isinstance(v, str)).all(), 'IDs must remain strings')
    require(set(frame.flywire_id) <= valid_ids, 'Unknown neuron IDs')
    t = frame.t.to_numpy()
    require(np.isfinite(t).all() and ((t >= 0) & (t < .75)).all(), 'Invalid spike times')
    require((np.diff(t) >= 0).all(), 'Unsorted spike times')
    ticks = np.rint(t * 1000 / dt).astype(np.int64)
    require(np.max(np.abs(t * 1000 / dt - ticks), initial=0) < 1e-6, 'Off-grid spikes')
    events = pd.DataFrame({'tick': ticks, 'id': frame.flywire_id})
    require(not events.duplicated().any(), 'Duplicate neuron/time event')
    noninput = events.loc[~events.id.isin(inputs)]
    # Stimulated cells have zero refractory duration in the original model.
    gaps = noninput.groupby('id').tick.diff().dropna()
    require((gaps >= round(2.2 / dt)).all(), 'Spike spacing shorter than refractory period')
    first = noninput.groupby('id').tick.min()
    lo, hi = round(650 / dt), round(730 / dt)
    counts = dict(noninput_spikes_650_730=int(noninput.tick.between(lo, hi-1).sum()),
                  newly_recruited_noninput_650_730=int(first.between(lo, hi-1).sum()))
    return counts, events


def validate_switch(switch, remove, ids, connections):
    require(switch['switch_ms'] == 600 and switch['remove'] is remove, 'Wrong switch specification')
    expected = [('720575940628695043', target) for target in
                ['720575940629667639', '720575940623862015']]
    pairs = switch['pairs']
    require(len(pairs) == 2 and all(len(p) == 2 and all(type(i) is int and 0 <= i < len(ids)
                for i in p) for p in pairs), 'Invalid switch indices')
    require([(ids[a], ids[b]) for a, b in pairs] == expected, 'Wrong switched connections')
    weights = []
    for a, b in pairs:
        row = connections.loc[connections.Presynaptic_Index.eq(a) & connections.Postsynaptic_Index.eq(b)]
        require(len(row) == 1, 'Missing or duplicate original connection')
        value = float(row['Excitatory x Connectivity'].iloc[0]) * .275 * 1.2
        weights.append(value * (.8 if value < 0 else 1))
    before, after = switch['weights_before_mv'], switch['weights_after_mv']
    require(len(before) == len(after) == 2, 'Wrong switch weight count')
    require(np.allclose(before, weights, rtol=0, atol=1e-12), 'Wrong original scaled weights')
    require(after == ([0., 0.] if remove else before), 'Wrong switch outcome')


def review(archive, package, reference, late=False):
    prefix = "connectome_late_pathway/" if late else "connectome_pathway/"
    conditions = ["late_reference", "late_edges"] if late else ["reference", "two_edges"]
    with zipfile.ZipFile(archive) as z, zipfile.ZipFile(package) as upload:
        names = z.namelist()
        require(len(names) == len(set(names)), 'Duplicate archive names')
        require(z.testzip() is None and upload.testzip() is None, 'ZIP integrity failure')
        read = lambda name: json.loads(z.read(name))
        frame = lambda name: pd.read_parquet(io.BytesIO(z.read(name)))
        plan_data = z.read('diagnostic_plan.json')
        require(plan_data == upload.read(prefix+'diagnostic_plan.json'), 'Changed plan')
        require(plan_data == (reference/'diagnostic_plan.json').read_bytes(), 'Different local reference plan')
        plan = json.loads(plan_data)
        require((plan['seed'], plan['variant'], plan['condition']) ==
                (631430, 'w120_i080', 'mn9_only'), 'Unexpected experiment')
        for name, h in plan['reference_files'].items():
            require(digest((reference/name).read_bytes()) == h, 'Changed reference '+name)
        for name, h in plan['model_files'].items():
            require(digest((ROOT/name).read_bytes()) == h, 'Changed model/data '+name)
        ids = pd.read_csv(ROOT/'2023_03_23_completeness_630_final.csv', index_col=0).index.astype(str)
        require(ids.is_unique, 'Duplicate neuron IDs')
        summary = read('summary.json')
        require(summary['status'] == 'complete' and summary['duration_ms'] == 750, 'Incomplete study')
        require(len(summary['results']) == len(summary['trials']) == 4, 'Wrong trial count')
        results, events_by_trial, manifests = [], {}, []
        source_names = {n.removeprefix('source/') for n in names if n.startswith('source/')}
        expected_sources = {n.removeprefix(prefix) for n in upload.namelist()
                            if n == prefix+'model.py' or
                            (n.startswith((prefix+'scripts/', prefix+'eigencircuits/'))
                             and n.endswith('.py'))}
        require(source_names == expected_sources, 'Archived source inventory differs from upload')
        tape = pd.read_parquet(reference/'input_events.parquet')
        tape = tape.loc[tape.tick < 7500].reset_index(drop=True)
        connections = pd.read_parquet(ROOT/'2023_03_23_connectivity_630_final.parquet')
        for dt in [.0004, .0002]:
            for condition in conditions:
                trial = f'{condition}_{dt}'
                m = read(trial+'/manifest.json')
                for key, value in dict(status='complete', dt_ms=dt, condition=condition,
                                       duration_ms=750, plan_sha256=digest(plan_data),
                                       exact_delivered_input=True).items():
                    require(m.get(key) == value, 'Invalid manifest '+trial+': '+key)
                require(m['environment']['packages'] == plan['packages'], 'Package mismatch')
                require(m['environment']['python'].startswith('3.11.'), 'Python mismatch')
                require(set(m['sources']) == source_names, 'Source inventory mismatch')
                for name, h in m['sources'].items():
                    data = z.read('source/'+name)
                    require(digest(data) == h, 'Source hash mismatch '+name)
                    require(data == upload.read(prefix+name), 'Source differs from upload '+name)
                required = {'spikes.parquet', 'scheduled_events.parquet', 'delivered_events.parquet',
                            'endpoints.json', 'simulation_progress.json'}
                if condition == 'two_edges':
                    required.add('removed_edges.csv')
                if late:
                    required.add('switch.json')
                require(set(m['outputs']) == required, 'Output inventory mismatch')
                for name, h in m['outputs'].items():
                    require(digest(z.read(trial+'/'+name)) == h, 'Output hash mismatch '+trial+'/'+name)
                require(read(trial+'/simulation_progress.json')['simulated_ms'] == 750, 'Incomplete simulation')
                process = read('logs/'+trial+'/process.json')
                require(process['returncode'] == 0 and not process['timed_out'], 'Process failed')
                require(not z.read('logs/'+trial+'/stderr.txt').strip(), 'Nonempty stderr needs review')
                expected = tape.copy()
                expected['tick'] *= round(.1/dt)
                for event_name in ['scheduled_events', 'delivered_events']:
                    actual = frame(trial+'/'+event_name+'.parquet')
                    pd.testing.assert_frame_equal(actual, expected, check_dtype=False, check_exact=True)
                old_delivered = pd.read_parquet(reference/'reference'/str(dt)/'delivered_events.parquet')
                old_delivered = old_delivered.loc[old_delivered.tick < round(750/dt)].reset_index(drop=True)
                pd.testing.assert_frame_equal(frame(trial+'/delivered_events.parquet'), old_delivered,
                                              check_dtype=False, check_exact=True)
                spikes = frame(trial+'/spikes.parquet')
                counts, events = spike_counts(spikes, plan['input_ids'], dt, set(ids))
                saved = read(trial+'/endpoints.json')
                for key, value in counts.items():
                    require(saved[key] == value, 'Endpoint mismatch '+trial)
                for neuron, times in saved['source_times_ms'].items():
                    require((spikes.loc[spikes.flywire_id.eq(neuron), 't']*1000).tolist() == times,
                            'Source spike-history mismatch')
                require(dict(dt_ms=dt, condition=condition, **saved) in summary['results'], 'Summary differs')
                require(m in summary['trials'], 'Summary manifest differs')
                if late:
                    old = pd.read_parquet(reference/'reference'/str(dt)/'spikes.parquet')
                    pd.testing.assert_frame_equal(spikes.loc[spikes.t < .6].reset_index(drop=True),
                                                  old.loc[old.t < .6].reset_index(drop=True),
                                                  check_dtype=False, check_exact=True)
                    require(m.get('exact_pre_switch_spikes') is True and m.get('switch_ms') == 600,
                            'Missing pre-switch verification')
                    switch = read(trial+'/switch.json')
                    validate_switch(switch, condition == 'late_edges', ids, connections)
                if condition in ['reference', 'late_reference']:
                    old = pd.read_parquet(reference/'reference'/str(dt)/'spikes.parquet')
                    pd.testing.assert_frame_equal(spikes, old.loc[old.t < .75].reset_index(drop=True),
                                                  check_dtype=False, check_exact=True)
                    require(m['exact_reference_spikes'] is True, 'Missing reference verification')
                elif not late:
                    removed = pd.read_csv(io.BytesIO(z.read(trial+'/removed_edges.csv')))
                    pairs = set(zip(removed.Presynaptic_ID.astype(str), removed.Postsynaptic_ID.astype(str)))
                    require(pairs == {('720575940628695043', v) for v in
                                      ['720575940629667639','720575940623862015']} and len(removed) == 2,
                            'Wrong removed connections')
                    for row in removed.itertuples(index=False):
                        require(ids[row.Presynaptic_Index] == str(row.Presynaptic_ID) and
                                ids[row.Postsynaptic_Index] == str(row.Postsynaptic_ID), 'ID/index mismatch')
                    subset = connections.loc[connections.Presynaptic_Index.eq(int(removed.Presynaptic_Index.iloc[0]))]
                    actual = subset.merge(removed, how='inner', on=list(removed.columns))
                    require(len(actual) == 2, 'Removed rows do not match original connectivity')
                results.append(dict(trial=trial, dt_ms=dt, condition=condition, **counts,
                                    total_spikes=len(spikes), elapsed_seconds=m['elapsed_seconds'],
                                    peak_rss_bytes=m['peak_rss_bytes']))
                events_by_trial[trial] = events
                manifests.append(m)
        comparisons = []
        for dt in [.0004, .0002]:
            a, b = [events_by_trial[f'{c}_{dt}'] for c in conditions]
            differences = a.merge(b, on=['tick','id'], how='outer', indicator=True)
            differences = differences.loc[differences._merge.ne('both')]
            earliest = differences.tick.min()
            counts_a, counts_b = [v.set_index('id').index.value_counts() for v in [a,b]]
            change = counts_b.subtract(counts_a, fill_value=0)
            comparisons.append(dict(dt_ms=dt, first_changed_spike_ms=None if differences.empty else float(earliest*dt),
                first_changed_events=differences.loc[differences.tick.eq(earliest)].to_dict('records'),
                neurons_with_changed_total_count=int(change.ne(0).sum()),
                absolute_count_difference=int(change.abs().sum())))
        return dict(archive_sha256=digest(Path(archive).read_bytes()),
                    package_sha256=digest(Path(package).read_bytes()), checked_files=len(names),
                    checks_passed=True, results=results, comparisons=comparisons,
                    finished_utc=max(m['finished_utc'] for m in manifests))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, default=ROOT/'CCR_pathway_results.zip')
    parser.add_argument('--package', type=Path, default=ROOT/'results/pcdr/pathway_package_validation_20261006/original_upload.zip')
    parser.add_argument('--reference', type=Path, default=ROOT/'results/pcdr/diagnostic_inputs_20261005')
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--late', action='store_true')
    args = parser.parse_args()
    result = review(args.archive, args.package, args.reference, args.late)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps(result, indent=2))
