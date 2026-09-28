"""Check full resolution-run events and recalculate paired results."""
import os
os.environ['MPLBACKEND'] = 'Agg'
import argparse
from pathlib import Path
import sys
import numpy as np
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.pcdr_ccr_transfer import read, write, digest
from scripts.pcdr_ccr_sensitivity import validated
from scripts.pcdr_raw_diagnostics import event_keys
from eigencircuits.common import fingerprint, neuron_ids, MN9, environment
from eigencircuits.readouts import footprint


def same(a, b):
    if isinstance(a, dict):
        if not isinstance(b, dict) or not set(a) <= set(b): raise ValueError('Missing result fields')
        for k in a: same(a[k], b[k])
    elif a is None:
        if b is not None and not pd.isna(b): raise ValueError('Undefined result mismatch')
    elif not np.isclose(a, b, atol=1e-8, rtol=1e-10):
        raise ValueError(f'Result mismatch: {a} versus {b}')


def check(study, followup, out):
    study, followup, out = map(Path, [study, followup, out])
    plan = read(followup / 'plan.json')
    if plan != read(ROOT / 'docs/pcdr/CCR_RESOLUTION_PLAN.json'): raise ValueError('Changed follow-up plan')
    progress = read(followup / 'progress.json')
    if progress['status'] != 'complete' or progress['completed'] != len(plan['jobs']): raise ValueError('Incomplete run')
    for source, expected in plan['sources'].items():
        if digest(followup / 'source' / Path(source).name) != expected: raise ValueError('Changed source')
    if digest(study / 'jobs.json') != plan['original_jobs_sha256']: raise ValueError('Different original study')
    original = read(study / 'jobs.json')
    old_jobs = {j['trial_id']: j for j in original['jobs']}
    ids = neuron_ids(); index = pd.Index(ids); lookup = {v: i for i, v in enumerate(ids)}
    support = [lookup[v] for v in plan['mode_ids']]
    exported_ids = pd.read_csv(followup / 'neurons.csv', dtype=str).root_id.tolist()
    if exported_ids != ids: raise ValueError('Neuron order mismatch')
    vectors, activity = {}, []
    summaries = pd.read_csv(followup / 'trial_summary.csv').set_index('trial')
    if not summaries.index.is_unique or set(summaries.index) != {s['id'] for s in plan['jobs']}: raise ValueError('Summary coverage mismatch')
    for spec in plan['jobs']:
        name = spec['id']; directory = followup / 'trials' / name
        m = read(directory / 'manifest.json')
        if m['status'] != 'complete' or m['spec'] != spec or m['environment'] != progress['environment']: raise ValueError('Worker metadata mismatch')
        expected_files = {'rates.parquet', 'spikes.parquet', 'delivered_events.parquet', 'population.json'}
        if set(m['outputs']) != expected_files: raise ValueError('Missing worker outputs')
        for file, expected in m['outputs'].items():
            if digest(directory / file) != expected: raise ValueError('Changed worker output')
        process = read(followup / 'logs' / name / 'process.json')
        if process['returncode'] != 0 or process['timed_out']: raise ValueError('Worker did not finish')
        olddir = study / 'trials' / spec['source_trial']
        old = validated(olddir, old_jobs[spec['source_trial']], original)
        if digest(olddir / 'manifest.json') != m['source_manifest_sha256']: raise ValueError('Source trial changed')
        scheduled = pd.read_parquet(olddir / 'input_events.parquet')
        if fingerprint(scheduled.to_dict('list')) != old['input_digest'] or m['physical_input_digest'] != old['input_digest']: raise ValueError('Input tape mismatch')
        scheduled['tick'] *= round(.1 / spec['dt_ms'])
        delivered = pd.read_parquet(directory / 'delivered_events.parquet')
        total_ticks = round(1000 / spec['dt_ms'])
        a = event_keys(scheduled, old['input_ids'], total_ticks)
        b = event_keys(delivered, old['input_ids'], total_ticks)
        if not np.isin(b, a).all(): raise ValueError('Unexpected delivered event')
        spikes = pd.read_parquet(directory / 'spikes.parquet')
        cells = index.get_indexer(spikes.flywire_id)
        t = spikes.t.to_numpy(); dt = spec['dt_ms'] / 1000
        if np.any(cells < 0) or not np.isfinite(t).all() or np.any(t < 0) or np.any(t >= 1): raise ValueError('Invalid spike')
        ticks = np.rint(t / dt).astype(np.int64)
        if not np.allclose(t, ticks * dt, atol=1e-10, rtol=0): raise ValueError('Off-grid spike')
        order = np.lexsort((ticks, cells)); gaps = np.diff(ticks[order]); equal = np.diff(cells[order]) == 0
        sensory = np.isin(np.asarray(ids), old['input_ids'])
        required = np.where(sensory[cells[order][1:]], dt, .0022)
        if np.any(equal & (gaps * dt < required - 1e-10)): raise ValueError('Spike-spacing violation')
        counts = np.bincount(cells, minlength=len(ids)).astype(float)
        rates = pd.read_parquet(directory / 'rates.parquet')
        if rates.root_id.duplicated().any() or not set(rates.root_id) <= set(ids): raise ValueError('Invalid rate IDs')
        for key in ['rate_hz', 'spike_count']:
            if not np.array_equal(counts, rates.set_index('root_id')[key].reindex(ids, fill_value=0)): raise ValueError('Rate/spike disagreement')
        if fingerprint(spikes[['t', 'flywire_id']].to_dict('list')) != m['spike_digest']: raise ValueError('Spike digest mismatch')
        trace = np.bincount(np.floor((t + 1e-12) / .01).astype(int), minlength=100)
        if trace.tolist() != read(directory / 'population.json'): raise ValueError('Population trace mismatch')
        same({'spike_count': len(t), 'recruited_noninput': int(np.count_nonzero(counts[~sensory])), 'mn9_hz': counts[lookup[MN9]]}, m)
        if spec['stage'] == 'replay':
            if m['spike_digest'] != old['spike_digest'] or fingerprint(delivered.to_dict('list')) != old['delivered_input_digest']: raise ValueError('Replay differs')
        vectors[name] = counts
        same({'spikes': len(t), 'mn9_hz': counts[lookup[MN9]], 'recruited_noninput': int(np.count_nonzero(counts[~sensory]))}, summaries.loc[name].to_dict())
        activity.append({'id': name, 'stage': spec['stage'], 'source_trial': spec['source_trial'], 'seed': spec['seed'], 'dt_ms': spec['dt_ms'],
                         'spikes': len(t), 'recruited_noninput': m['recruited_noninput'], 'delivered_events': len(delivered),
                         'max_noninput_hz': counts[~sensory].max(), 'peak_spikes_per_10ms': trace.max()})
    jobs = {(j['stage'], j['dt_ms'], j['variant'], j['condition'], j['seed']): j for j in plan['jobs']}
    saved = pd.read_csv(followup / 'per_seed.csv')
    keys = ['stage', 'dt_ms', 'variant', 'condition', 'seed']
    if saved.duplicated(keys).any(): raise ValueError('Duplicate pairs')
    saved = saved.set_index(keys)
    groups, rows = {}, []
    for spec in plan['jobs']:
        if spec['stage'] == 'replay' or spec['condition'] == 'baseline': continue
        key = (spec['stage'], spec['dt_ms'], spec['variant'], spec['condition'], spec['seed'])
        base = jobs[key[0], key[1], key[2], 'baseline', key[4]]
        delta = vectors[spec['id']] - vectors[base['id']]
        own = [lookup[v] for v in spec['lesion_ids']]
        fixed = footprint(delta, support)
        result = {**footprint(delta, own), 'fixed_mode_A': fixed['A'], 'fixed_mode_F': fixed['F'], 'mn9_change_hz': delta[lookup[MN9]]}
        same(result, saved.loc[key].to_dict())
        rows.append({**dict(zip(keys,key)), **result})
        groups.setdefault(key[:4], []).append(delta)
    if len(rows) != len(saved): raise ValueError('Pair coverage mismatch')
    means = read(followup / 'mean_results.json')['rows']
    if len(means) != len(groups): raise ValueError('Mean coverage mismatch')
    for row in means:
        key = tuple(row[k] for k in keys[:4])
        mean = np.mean(groups[key], axis=0)
        spec = next(j for j in plan['jobs'] if tuple(j[k] for k in keys[:4]) == key)
        same({**footprint(mean, [lookup[v] for v in spec['lesion_ids']]), 'fixed_mode': footprint(mean, support), 'n_pairs': len(groups[key]), 'mn9_change_hz': mean[lookup[MN9]]}, row)
    differences = []
    for condition in sorted({k[3] for k in groups if k[0] == 'default'}):
        coarse = np.mean(groups['default', .05, 'default', condition], axis=0)
        fine = np.mean(groups['default', .025, 'default', condition], axis=0)
        difference = float(np.abs(fine - coarse).sum())
        magnitude = float(np.abs(fine).sum())
        differences.append({'condition': condition, 'mean_vector_l1_difference_hz': difference,
                            'relative_to_0025_response': difference / magnitude if magnitude else None})
    out.mkdir(parents=True, exist_ok=False)
    pd.DataFrame(activity).to_csv(out / 'checked_activity.csv', index=False)
    pd.DataFrame(rows).to_csv(out / 'checked_pairs.csv', index=False)
    write(out / 'checked_means.json', means)
    write(out / 'default_step_differences.json', differences)
    write(out / 'full_check.json', {'status': 'complete', 'trials_checked': len(vectors), 'exact_replays': 4,
          'pairs_reproduced': len(rows), 'mean_rows_reproduced': len(means),
          'archive_sha256': digest(followup.parent / 'CCR_resolution_results.zip'),
          'plan_sha256': digest(followup / 'plan.json'), 'script_sha256': digest(Path(__file__)),
          'analysis_environment': environment(), 'outputs': {p.name: digest(p) for p in out.iterdir()}})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['study', 'followup', 'out']: parser.add_argument('--' + name, required=True)
    args = parser.parse_args()
    check(args.study, args.followup, args.out)
