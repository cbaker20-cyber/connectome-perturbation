"""Check downloaded follow-up events and recalculate its reported results."""
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
from scripts.pcdr_analyze_raw import vector_comparison, resampled_metrics
from scipy.sparse import csr_matrix


def same(a, b):
    if isinstance(a, dict):
        if not isinstance(b, dict) or not set(a) <= set(b): raise ValueError('Missing result fields')
        for k in a: same(a[k], b[k])
    elif a is None:
        if b is not None and not pd.isna(b): raise ValueError('Undefined result mismatch')
    elif not np.isclose(a, b, atol=1e-8, rtol=1e-10):
        raise ValueError(f'Result mismatch: {a} versus {b}')


def plot_steps(frame, path):
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2, 3, figsize=(11, 7), sharex=True, sharey=True)
    conditions = ['mode', 'mode_without_mn9', 'mn9_only', 'motor_003', 'motor_004', 'motor_005']
    for ax, condition in zip(axes.flat, conditions):
        for seed, rows in frame[frame.condition == condition].groupby('seed'):
            rows = rows.sort_values('dt_ms', ascending=False)
            ax.plot(rows.dt_ms, rows.total_absolute_sum_hz, marker='o', label=str(seed))
        ax.set_xscale('log', base=2)
        ax.set_yscale('log')
        ax.set_xlim(.12, .02)
        ax.set_xticks([.1, .05, .025], ['0.1', '0.05', '0.025'])
        ax.set_title(condition.replace('_', ' '))
        ax.set_xlabel('Time step (ms)')
        ax.legend(title='Seed', fontsize=8)
        ax.grid(alpha=.2)
    for ax in axes[:, 0]: ax.set_ylabel('Total absolute rate change\n(summed Hz)')
    fig.suptitle('Selected trials at weight 1.2 / inhibitory multiplier 0.8\nSame scheduled physical input events at every step; fixed 51-cell support for A/F')
    fig.tight_layout(rect=(0, 0, 1, .93))
    fig.savefig(path, dpi=160)
    plt.close(fig)


def check(study, followup, out):
    study, followup, out = map(Path, [study, followup, out])
    plan = read(followup / 'plan.json')
    if plan != read(ROOT / 'docs/pcdr/CCR_FOLLOWUP_PLAN.json'): raise ValueError('Changed follow-up plan')
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
    vectors, source_vectors, activity = {}, {}, []
    summaries = pd.read_csv(followup / 'trial_summary.csv').set_index('id')
    if not summaries.index.is_unique or set(summaries.index) != {s['id'] for s in plan['jobs']}: raise ValueError('Summary coverage mismatch')
    for spec in plan['jobs']:
        name = spec['id']; directory = followup / 'trials' / name
        m = read(directory / 'manifest.json')
        if m['status'] != 'complete' or m['spec'] != spec or m['environment'] != progress['analysis_environment']: raise ValueError('Worker metadata mismatch')
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
        old_rates = pd.read_parquet(olddir / 'rates.parquet').set_index('root_id').rate_hz.reindex(ids).to_numpy()
        source_vectors[spec['source_trial']] = old_rates
        vectors[name] = counts
        same({'spikes': len(t), 'mn9_hz': counts[lookup[MN9]], 'difference_from_source_l1_hz': np.abs(counts - old_rates).sum()}, summaries.loc[name].to_dict())
        activity.append({'id': name, 'stage': spec['stage'], 'source_trial': spec['source_trial'], 'seed': spec['seed'], 'dt_ms': spec['dt_ms'],
                         'spikes': len(t), 'recruited_noninput': m['recruited_noninput'], 'delivered_events': len(delivered),
                         'max_noninput_hz': counts[~sensory].max(), 'peak_spikes_per_10ms': trace.max()})
    pairs = pd.read_csv(followup / 'timestep_pairs.csv').set_index('trial')
    paired_rows = []
    for spec in plan['jobs']:
        if spec['stage'] not in ['replay', 'timestep'] or not spec['lesion_ids'] or not spec['source_trial'].startswith('w120_i080_'): continue
        prefix = 'replay_' if spec['stage'] == 'replay' else 'dt' + str(spec['dt_ms']).replace('.', 'p') + '_'
        delta = vectors[spec['id']] - vectors[prefix + f"w120_i080_baseline_{spec['seed']}"]
        result = {**footprint(delta, support), 'mn9_change_hz': delta[lookup[MN9]]}
        same(result, pairs.loc[spec['id']].to_dict())
        paired_rows.append({'trial': spec['id'], 'condition': spec['source_trial'].removeprefix('w120_i080_').rsplit('_', 1)[0], 'seed': spec['seed'], 'dt_ms': spec['dt_ms'], **result})
    if not pairs.index.is_unique or set(pairs.index) != {r['trial'] for r in paired_rows}: raise ValueError('Paired step coverage mismatch')
    reduced, full = [], []
    for seed in plan['seeds']:
        p = study / 'trials' / f'default_baseline_{seed}'
        validated(p, old_jobs[p.name], original)
        baseline = pd.read_parquet(p / 'rates.parquet').set_index('root_id').rate_hz.reindex(ids).to_numpy()
        reduced.append(vectors[f'active29_{seed}'] - baseline)
        full.append(source_vectors[f'default_mode_{seed}'] - baseline)
    reduced, full = np.asarray(reduced), np.asarray(full)
    mean, original_mean = reduced.mean(0), full.mean(0)
    result = {'fixed_51_support': footprint(mean, support), 'full_mode_fixed_51_support': footprint(original_mean, support),
              'mean_vector_difference_l1_hz': float(np.abs(mean - original_mean).sum()), 'mn9_change_hz': mean[lookup[MN9]]}
    same(result, read(followup / 'active29_summary.json'))
    weights = np.random.default_rng(630727).multinomial(30, np.full(30, 1/30), size=2000) / 30
    small = resampled_metrics(csr_matrix(reduced), support, weights)
    large = resampled_metrics(csr_matrix(full), support, weights)
    intervals = {}
    for i, metric in enumerate(['A', 'F']):
        intervals[metric] = {'difference': result['fixed_51_support'][metric] - result['full_mode_fixed_51_support'][metric],
                              'interval': np.quantile(small[i] - large[i], [.025, .975]).tolist()}
    out.mkdir(parents=True, exist_ok=False)
    pd.DataFrame(activity).to_csv(out / 'checked_activity.csv', index=False)
    pd.DataFrame(paired_rows).to_csv(out / 'checked_step_pairs.csv', index=False)
    plot_steps(pd.DataFrame(paired_rows), out / 'step_comparison.png')
    write(out / 'checked_active29.json', {**result, 'spatial': vector_comparison(original_mean, mean, support),
          'paired_intervals': intervals, 'bootstrap_seed': 630727, 'replicates': 2000,
          'interpretation': 'Retrospective marginal intervals on the same 30 seeds and fixed 51-cell support; no equivalence margin.'})
    write(out / 'full_check.json', {'status': 'complete', 'trials_checked': len(vectors), 'exact_replays': 25,
          'paired_step_rows_reproduced': len(paired_rows), 'plan_sha256': digest(followup / 'plan.json'),
          'script_sha256': digest(Path(__file__)), 'analysis_environment': environment(),
          'outputs': {p.name: digest(p) for p in out.iterdir()}})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['study', 'followup', 'out']: parser.add_argument('--' + name, required=True)
    args = parser.parse_args()
    check(args.study, args.followup, args.out)
