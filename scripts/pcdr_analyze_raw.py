"""Reproduce collected rate results and compare saved neuron-level responses."""
import os
for key in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS']:
    os.environ[key] = '1'
import argparse
from pathlib import Path
import sys
import numpy as np
import pandas as pd
from scipy import sparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.pcdr_ccr_transfer import read, write, digest
from eigencircuits.common import MN9
from eigencircuits.readouts import footprint


def resampled_metrics(delta, support, weights):
    """Keep the original mean-then-absolute endpoint and whole-seed resampling."""
    active = np.flatnonzero(np.asarray(delta.getnnz(axis=0)).ravel())
    inside = np.isin(active, support)
    values = delta[:, active].toarray()
    a, f = [], []
    for start in range(0, len(weights), 100):
        means = np.abs(weights[start:start + 100] @ values)
        sums, totals = means[:, inside].sum(1), means.sum(1)
        a.extend(sums / len(support))
        f.extend(np.divide(sums, totals, out=np.full(len(totals), np.nan), where=totals > 0))
    return np.asarray(a), np.asarray(f)


def vector_comparison(a, b, support):
    a, b = np.asarray(a), np.asarray(b)
    difference = a - b
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    l1 = np.abs(a).sum()
    return {'difference_total_abs_hz': float(np.abs(difference).sum()),
            'difference_mode_abs_hz': float(np.abs(difference[support]).sum()),
            'difference_relative_to_first_l1': float(np.abs(difference).sum() / l1) if l1 else None,
            'signed_cosine': float(np.dot(a, b) / (na * nb)) if na and nb else None,
            'first_total_abs_hz': float(l1), 'second_total_abs_hz': float(np.abs(b).sum())}


def activity_report(diagnostic, out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    trials = pd.read_csv(diagnostic / 'trial_diagnostics.csv')
    traces = pd.read_csv(diagnostic / 'population_10ms.csv').set_index('trial_id')
    summary = trials.groupby(['variant', 'condition']).agg(
        n=('trial_id', 'size'), median_spikes=('spikes', 'median'), max_spikes=('spikes', 'max'),
        median_recruited=('recruited_noninput', 'median'), max_recruited=('recruited_noninput', 'max'),
        max_noninput_hz=('max_noninput_hz', 'max'), min_noninput_isi_ms=('min_noninput_isi_ms', 'min'))
    summary.to_csv(out / 'activity_summary.csv')
    baseline = trials[trials.condition == 'baseline'][['variant', 'seed', 'spikes', 'recruited_noninput']]
    pairs = trials[trials.condition != 'baseline'].merge(baseline, on=['variant', 'seed'], suffixes=('', '_baseline'), validate='many_to_one')
    pairs['spike_count_change'] = pairs.spikes - pairs.spikes_baseline
    pairs['recruited_change'] = pairs.recruited_noninput - pairs.recruited_noninput_baseline
    pairs.to_csv(out / 'paired_activity.csv', index=False)
    conditions = ['baseline', 'mode', 'mode_without_mn9', 'mn9_only', 'motor_003', 'motor_004', 'motor_005']
    fig, axes = plt.subplots(7, 2, figsize=(12, 15), sharex=True, sharey=True)
    time = (np.arange(100) + .5) * .01
    for col, variant in enumerate(['default', 'w120_i080']):
        for row, condition in enumerate(conditions):
            group = trials[(trials.variant == variant) & (trials.condition == condition)]
            values = traces.loc[group.trial_id].to_numpy()
            ax = axes[row, col]
            ax.plot(time, values.T, color='#8c9baa', alpha=.35, linewidth=.6)
            ax.plot(time, np.median(values, axis=0), color='#152f44', linewidth=1.5, label='Median of 30 trials')
            index = group.spikes.idxmax() if condition == 'baseline' else group.paired_total_abs_hz.idxmax()
            selected = group.loc[index]
            ax.plot(time, traces.loc[selected.trial_id].to_numpy(), color='#c65a18', linewidth=1.1, label=f"Seed {int(selected.seed)}")
            ax.set_yscale('symlog', linthresh=100)
            ax.set_title(f'{variant}: {condition}', fontsize=10)
            ax.legend(fontsize=7, loc='upper left')
            if col == 0: ax.set_ylabel('Spikes / 10 ms')
    axes[-1, 0].set_xlabel('Time (s)')
    axes[-1, 1].set_xlabel('Time (s)')
    fig.suptitle('Saved population spike counts: every seed retained\nOrange: largest paired total rate change; baseline: largest spike count', fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, .96))
    fig.savefig(out / 'population_traces.png', dpi=160)
    plt.close(fig)


def analyze(study, diagnostic, out):
    study, diagnostic, out = map(Path, [study, diagnostic, out])
    audit = read(diagnostic / 'audit.json')
    if audit['status'] != 'complete':
        raise ValueError('Trial validation is incomplete')
    for name, expected in audit['outputs'].items():
        if digest(diagnostic / name) != expected:
            raise ValueError('Changed diagnostic output: ' + name)
    if digest(study / 'jobs.json') != audit['jobs_sha256']:
        raise ValueError('Different study plan')
    plan = read(study / 'jobs.json')
    collection = read(study / 'collection_environment.json')
    if collection['status'] != 'complete':
        raise ValueError('Original collection did not finish')
    for name in ['results.json', 'per_seed.csv']:
        if digest(study / name) != collection['outputs'][name]:
            raise ValueError('Original collected output changed: ' + name)
    original = read(study / 'results.json')['rows']
    seeds = plan['design']['seeds']
    ids = pd.read_csv(diagnostic / 'neurons.csv', dtype={'root_id': str})
    lookup = {v: i for i, v in enumerate(ids.root_id)}
    conditions = {c['name']: [lookup[x] for x in c['ids']] for c in plan['conditions']}
    mode = conditions['mode']
    jobs = plan['jobs']
    trial_index = {j['trial_id']: i for i, j in enumerate(jobs)}
    def load_sparse(name):
        frame = pd.read_parquet(diagnostic / name)
        rows = frame.trial_id.map(trial_index)
        if rows.isna().any() or frame.duplicated(['trial_id', 'neuron_index']).any():
            raise ValueError('Unknown or duplicate sparse rows')
        return sparse.csr_matrix((frame.rate_or_delta_hz, (rows, frame.neuron_index)), shape=(len(jobs), len(ids)))
    all_delta = load_sparse('paired_deltas.parquet')
    baselines = load_sparse('baseline_rates.parquet')
    job_lookup = {(j['variant']['name'], j['condition'], j['seed']): i for i, j in enumerate(jobs)}
    def matrix(variant, condition, source=all_delta):
        return source[[job_lookup[variant, condition, s] for s in seeds]]
    recorded_seeds = pd.read_csv(study / 'per_seed.csv').set_index(['variant', 'condition', 'seed'])
    expected_keys = {(j['variant']['name'], j['condition'], j['seed']) for j in jobs if j['condition'] != 'baseline'}
    if not recorded_seeds.index.is_unique or set(recorded_seeds.index) != expected_keys:
        raise ValueError('Incomplete or duplicate collected seed rows')
    groups = {(variant, condition) for variant, condition, seed in expected_keys}
    if len(original) != len(groups) or {(r['variant'], r['condition']) for r in original} != groups:
        raise ValueError('Incomplete collected summary rows')
    weights = np.random.default_rng(630700).multinomial(len(seeds), np.full(len(seeds), 1 / len(seeds)), size=2000) / len(seeds)
    summaries, distributions, means = [], {}, {}
    for row in original:
        variant, condition = row['variant'], row['condition']
        delta = matrix(variant, condition)
        mean = np.asarray(delta.mean(0)).ravel()
        means[variant, condition] = mean
        support = conditions[condition]
        result = footprint(mean, support)
        result['mn9_delta_hz'] = float(mean[lookup[MN9]])
        for key, value in result.items():
            if not ((value is None and row[key] is None) or (value is not None and row[key] is not None and np.isclose(value, row[key], atol=1e-8, rtol=1e-10))):
                raise ValueError(f'Mean result mismatch: {variant}/{condition}/{key}')
        for i, seed in enumerate(seeds):
            values = delta.getrow(i).toarray().ravel()
            recorded = recorded_seeds.loc[(variant, condition, seed)]
            individual = footprint(values, support)
            individual['mn9_delta_hz'] = float(values[lookup[MN9]])
            for key, value in individual.items():
                if value is None:
                    if not pd.isna(recorded[key]): raise ValueError('Undefined fraction mismatch')
                elif not np.isclose(value, recorded[key], atol=1e-8, rtol=1e-10):
                    raise ValueError(f'Seed result mismatch: {variant}/{condition}/{seed}/{key}')
        a, f = resampled_metrics(delta, support, weights)
        distributions[variant, condition] = (a, f)
        for values, key in [(a, 'A_95pct'), (f, 'F_95pct')]:
            interval = np.nanquantile(values, [.025, .975]) if np.isfinite(values).any() else None
            if not ((interval is None and row[key] is None) or (interval is not None and np.allclose(interval, row[key], atol=1e-8, rtol=1e-10))):
                raise ValueError(f'Interval mismatch: {variant}/{condition}/{key}')
        summaries.append({'variant': variant, 'condition': condition, **result})
        print(f'Reproduced {variant}/{condition}', flush=True)
    out.mkdir(parents=True, exist_ok=False)
    contrasts, spatial = [], []
    for variant in [v['name'] for v in plan['variants']]:
        for condition in ['motor_003', 'motor_004', 'motor_005']:
            for k, metric in enumerate(['A', 'F']):
                values = distributions[variant, 'mode'][k] - distributions[variant, condition][k]
                mode_result = footprint(means[variant, 'mode'], mode)[metric]
                control_result = footprint(means[variant, condition], conditions[condition])[metric]
                low, high = np.quantile(values, [.025, .975])
                contrasts.append({'variant': variant, 'comparison': condition, 'metric': metric,
                                  'mode_minus_comparison': mode_result - control_result, 'low': low, 'high': high,
                                  'replicates': 2000, 'seed': 630700})
        for condition in ['mode_without_mn9', 'mn9_only']:
            spatial.append({'variant': variant, 'comparison': 'mode_vs_' + condition,
                            **vector_comparison(means[variant, 'mode'], means[variant, condition], mode)})
    singles = [c for c in conditions if c.startswith('mode_cell_')] + ['mn9_only']
    if len(singles) != 51: raise ValueError('Missing single-cell conditions')
    summed = sum(means['default', c] for c in singles)
    spatial.append({'variant': 'default', 'comparison': 'mode_vs_sum_of_singles',
                    **vector_comparison(means['default', 'mode'], summed, mode)})
    trial_stats = pd.read_csv(diagnostic / 'trial_diagnostics.csv').set_index('trial_id')
    zero_cells = []
    baseline = matrix('default', 'baseline', baselines)
    joint_rates = baseline + matrix('default', 'mode')
    for condition in singles:
        delta = matrix('default', condition)
        if delta.nnz: continue
        idx = conditions[condition][0]
        rates = baseline[:, idx].toarray().ravel()
        joint = joint_rates[:, idx].toarray().ravel()
        recorded = [trial_stats.loc[jobs[job_lookup['default', condition, s]]['trial_id'], 'spike_file_identical_to_baseline'] for s in seeds]
        if not all(str(value) in ['True', 'False'] for value in recorded):
            raise ValueError('Missing spike equality result')
        identical = [str(value) == 'True' for value in recorded]
        zero_cells.append({'condition': condition, 'root_id': ids.root_id.iloc[idx], 'baseline_mean_hz': rates.mean(),
                           'baseline_min_hz': rates.min(), 'baseline_max_hz': rates.max(),
                           'baseline_active_seeds': int(np.count_nonzero(rates)), 'identical_spike_seeds': sum(identical), 'n_seeds': len(seeds),
                           'joint_lesion_active_seeds': int(np.count_nonzero(joint)), 'joint_lesion_mean_hz': joint.mean(), 'joint_lesion_max_hz': joint.max()})
    pd.DataFrame(contrasts).to_csv(out / 'paired_footprint_contrasts.csv', index=False)
    pd.DataFrame(spatial).to_csv(out / 'spatial_comparisons.csv', index=False)
    pd.DataFrame(zero_cells).to_csv(out / 'zero_rate_cells.csv', index=False)
    activity_report(diagnostic, out)
    write(out / 'raw_analysis.json', {'status': 'complete', 'jobs_sha256': digest(study / 'jobs.json'),
          'diagnostic_audit_sha256': digest(diagnostic / 'audit.json'), 'script_sha256': digest(Path(__file__)),
          'reproduced_summary_rows': len(summaries), 'reproduced_seed_rows': len(recorded_seeds),
          'reproduced_interval_rows': len(summaries), 'zero_rate_cells': len(zero_cells),
          'interpretation': 'Retrospective paired intervals, conditional on this model and these chosen comparison sets. No reference-set p-values or biological replication.',
          'outputs': {p.name: digest(p) for p in out.iterdir()}})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--study', required=True)
    parser.add_argument('--diagnostic', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    analyze(args.study, args.diagnostic, args.out)
