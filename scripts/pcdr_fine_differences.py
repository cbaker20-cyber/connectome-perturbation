"""Describe saved fine-step differences without rerunning or reselecting trials."""
import argparse
from itertools import combinations
from pathlib import Path
import sys
import zipfile
import json

import numpy as np
import pandas as pd
from scipy import sparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.pcdr_ccr_transfer import read, write, digest
from eigencircuits.common import environment


def binned(t, cells, n, width_ms=10):
    t, cells = np.asarray(t), np.asarray(cells)
    if width_ms not in (1, 5, 10, 20):
        raise ValueError('Unsupported bin width')
    if (t.shape != cells.shape or t.ndim != 1 or not np.isfinite(t).all()
            or np.any(t < 0) or np.any(t >= 1)
            or not np.issubdtype(cells.dtype, np.integer)
            or np.any(cells < 0) or np.any(cells >= n)):
        raise ValueError('Invalid spikes')
    bins = np.floor((t + 1e-12) / (width_ms / 1000)).astype(int)
    return sparse.csr_matrix((np.ones(len(t), dtype=np.int32), (bins, cells)),
                             shape=(1000 // width_ms, n))


def distances(coarse, fine):
    coarse, fine = np.asarray(coarse, dtype=float), np.asarray(fine, dtype=float)
    if coarse.shape != fine.shape or coarse.ndim != 2 or not np.isfinite([coarse, fine]).all():
        raise ValueError('Finite paired matrices required')
    if len(fine) < 2:
        raise ValueError('At least two seeds required')
    within = np.abs(coarse - fine).sum(axis=1)
    between = np.array([np.abs(fine[i] - fine[j]).sum() for i, j in combinations(range(len(fine)), 2)])
    return within, between


def first_bin(values, width_ms):
    indices = np.flatnonzero(values)
    return int(indices[0] * width_ms) if len(indices) else None


def quantiles(values):
    return dict(zip(['min', 'q25', 'median', 'q75', 'max'], np.quantile(values, [0, .25, .5, .75, 1]).tolist()))


def phase_counts(t, cells, n, edges):
    edges = np.asarray(edges, dtype=float)
    if edges[0] != 0 or edges[-1] != 1 or np.any(np.diff(edges) <= 0):
        raise ValueError('Increasing edges from zero to one required')
    binned(t, cells, n)
    phase = np.searchsorted(edges, t, side='right') - 1
    return sparse.csr_matrix((np.ones(len(t), dtype=np.int32), (phase, cells)),
                             shape=(len(edges)-1, n))


def run(followup, verified, out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    followup, verified, out = map(Path, (followup, verified, out))
    if out.exists():
        raise FileExistsError(out)
    check = read(verified / 'full_check.json')
    archive = ROOT / 'CCR_fine_results.zip'
    if check['status'] != 'complete' or digest(archive) != check['archive_sha256']:
        raise ValueError('Verified archive required')
    plan = read(followup / 'plan.json')
    if digest(followup / 'plan.json') != check['plan_sha256']:
        raise ValueError('Changed plan')
    ids = pd.Index(pd.read_csv(followup / 'neurons.csv', dtype=str).root_id)
    if not ids.is_unique:
        raise ValueError('Duplicate neuron IDs')
    jobs = [j for j in plan['jobs'] if j['stage'] == 'fine' and
            (j['variant'] != 'default' or j['dt_ms'] in (.0002, .0001))]
    out.mkdir(parents=True)
    write(out / 'protocol.json', {
        'purpose': 'Post-result descriptive analysis; does not replace frozen agreement criteria.',
        'default_steps_ms': [.0002, .0001], 'altered_steps_ms': plan['steps_ms'],
        'time_bins_ms': [1, 5, 10, 20],
        'response': 'Lesion minus same-seed baseline counts over one second; counts equal Hz.',
        'seed_comparison': 'Same-seed step L1 versus all distinct-seed finest-step response L1; no p-values. Pairs share seeds.',
        'contributors': 'Mean across seeds of absolute neuronwise differences; not absolute difference of means.',
        'burst': 'All recorded altered-weight trials; positive bin excess relative to finest same condition. Quantiles describe timing, not onset mechanism.',
        'burst_phases_s': [0, .6, .65, .7, .73, 1],
        'phase_selection': 'Chosen after first activity plot showed rise near 710-730 ms. These are descriptive windows, not predeclared endpoints.',
        'archive_sha256': check['archive_sha256'], 'script_sha256': digest(Path(__file__)),
        'analysis_environment': environment()})
    counts, traces, frames, inputs, specs = {}, {}, {}, {}, {}
    with zipfile.ZipFile(archive) as z:
        if (followup/'neurons.csv').read_bytes() != z.read('neurons.csv'):
            raise ValueError('Changed neuron table')
        for j in jobs:
            key = j['dt_ms'], j['variant'], j['condition'], j['seed']
            if key in specs:
                raise ValueError('Duplicate trial key')
            specs[key] = j
            d = followup / 'trials' / j['id']
            m = json.loads(z.read('trials/' + j['id'] + '/manifest.json'))
            if m['spec'] != j or m['status'] != 'complete':
                raise ValueError('Trial spec mismatch')
            for name in ['spikes.parquet', 'rates.parquet', 'delivered_events.parquet']:
                if digest(d / name) != m['outputs'][name]:
                    raise ValueError('Changed output: ' + str(d / name))
            frame = pd.read_parquet(d / 'spikes.parquet')
            cells = ids.get_indexer(frame.flywire_id)
            matrix = binned(frame.t.to_numpy(), cells, len(ids))
            c = np.asarray(matrix.sum(axis=0)).ravel()
            rates = pd.read_parquet(d / 'rates.parquet')
            if rates.root_id.duplicated().any() or not set(rates.root_id) <= set(ids):
                raise ValueError('Invalid rate IDs')
            if not np.array_equal(c, rates.set_index('root_id').rate_hz.reindex(ids, fill_value=0)):
                raise ValueError('Spike/rate mismatch')
            counts[key], traces[key], frames[key] = c, matrix, (frame.t.to_numpy(), cells)
            delivered = pd.read_parquet(d / 'delivered_events.parquet')
            # All four steps are integer multiples of 0.0001 ms, avoiding float-time equality.
            ticks = delivered.tick.to_numpy() * round(j['dt_ms'] / .0001)
            inputs[key] = set(zip(ticks.tolist(), delivered.flywire_id.tolist()))
    temporal, response, contributors, seed_rows, input_rows = [], [], [], [], []
    seeds = sorted({k[3] for k in specs if k[1] == 'default'})
    conditions = ['mode', 'motor_003', 'motor_004', 'motor_005']
    for condition in ['baseline'] + conditions:
        for seed in seeds:
            a, b = (.0002, 'default', condition, seed), (.0001, 'default', condition, seed)
            input_rows.append(dict(variant='default', condition=condition, seed=seed,
                                   coarse_ms=.0002, fine_ms=.0001, differing_delivered_events=len(inputs[a] ^ inputs[b])))
            for width in [1, 5, 10, 20]:
                ma = traces[a] if width == 10 else binned(*frames[a], len(ids), width)
                mb = traces[b] if width == 10 else binned(*frames[b], len(ids), width)
                diff = ma - mb
                per_cell = np.asarray(abs(diff).sum(axis=1)).ravel()
                population = np.asarray(diff.sum(axis=1)).ravel()
                temporal.append(dict(condition=condition, seed=seed, width_ms=width,
                    first_cell_count_difference_bin_start_ms=first_bin(per_cell, width),
                    first_population_difference_bin_start_ms=first_bin(population, width),
                    cell_count_L1=int(per_cell.sum()), population_L1=int(abs(population).sum())))
    fig, axes = plt.subplots(2, 2, figsize=(10, 7), constrained_layout=True)
    for condition, ax in zip(conditions, axes.ravel()):
        vectors = {}
        for step in [.0002, .0001]:
            vectors[step] = np.array([counts[step, 'default', condition, seed].astype(float) -
                                      counts[step, 'default', 'baseline', seed] for seed in seeds])
        a, b = vectors[.0002], vectors[.0001]
        within, between = distances(a, b)
        response.append(dict(condition=condition, same_seed_step_L1_hz=quantiles(within),
            different_seed_L1_hz=quantiles(between), median_ratio=float(np.median(within)/np.median(between))))
        for seed, value in zip(seeds, within):
            seed_rows.append(dict(condition=condition, kind='same_seed_different_step', seed1=seed, seed2=seed, L1_hz=value))
        for (i, j), value in zip(combinations(range(len(seeds)), 2), between):
            seed_rows.append(dict(condition=condition, kind='different_seed_finest_step', seed1=seeds[i], seed2=seeds[j], L1_hz=value))
        cell = np.abs(a-b).mean(axis=0)
        total = float(cell.sum())
        for i in np.flatnonzero(cell):
            contributors.append(dict(condition=condition, root_id=ids[i], mean_absolute_step_difference_hz=cell[i],
                fraction_of_total=cell[i]/total, in_selected_group=ids[i] in plan['mode_ids']))
        for label, values in [('Same seed, two steps', within), ('Different seeds, finest step', between)]:
            ax.step(np.sort(values), np.arange(1, len(values)+1)/len(values), where='post', label=label)
        ax.set(title=condition, xlabel='Response-vector L1 distance (Hz)', ylabel='Cumulative fraction')
    axes[0, 0].legend(fontsize=8)
    fig.savefig(out/'seed_comparison.png', dpi=170); plt.close(fig)

    burst, burst_cells = [], []
    fig, axes = plt.subplots(2, 2, figsize=(11, 7), sharex=True, constrained_layout=True)
    for row, (seed, lesion) in enumerate([(631430, 'mn9_only'), (631405, 'mode_without_mn9')]):
        for col, condition in enumerate(['baseline', lesion]):
            ax = axes[row, col]
            for step in plan['steps_ms']:
                key = step, 'w120_i080', condition, seed
                reference = .0001, 'w120_i080', condition, seed
                pop = np.asarray(traces[key].sum(axis=1)).ravel()
                ref = np.asarray(traces[reference].sum(axis=1)).ravel()
                excess = np.maximum(pop-ref, 0); total = int(excess.sum())
                rowdata = dict(seed=seed, condition=condition, step_ms=step, spikes=int(pop.sum()),
                    recruited=int(np.count_nonzero(counts[key])), peak_bin_spikes=int(pop.max()),
                    peak_bin_start_ms=int(np.argmax(pop)*10), positive_excess_over_finest=total,
                    differing_delivered_events=len(inputs[key] ^ inputs[reference]))
                for q in [.01, .05, .1, .5, .9]:
                    rowdata[f'excess_{q}_bin_start_ms'] = int(np.searchsorted(np.cumsum(excess), q*total)*10) if total else None
                burst.append(rowdata)
                for i in np.flatnonzero(counts[key] != counts[reference]):
                    burst_cells.append(dict(seed=seed, condition=condition, step_ms=step, root_id=ids[i],
                        spikes=int(counts[key][i]), finest_spikes=int(counts[reference][i]),
                        difference=int(counts[key][i])-int(counts[reference][i])))
                ax.plot(np.arange(100)*10, pop, label=str(step))
            ax.set(title=f'{seed}: {condition}', xlabel='Bin start (ms)', ylabel='Spikes / 10 ms')
    axes[0, 0].legend(title='Step (ms)', fontsize=8)
    fig.savefig(out/'altered_weight_activity.png', dpi=170); plt.close(fig)

    annotations = pd.read_csv(ROOT/'flywire_annotations.tsv', sep='\t', dtype=str, usecols=['root_id','cell_type','cell_class','top_nt'])
    if annotations.root_id.duplicated().any():
        raise ValueError('Duplicate annotation IDs')
    phases, phase_cells = [], []
    edges = [0, .6, .65, .7, .73, 1]
    for step in plan['steps_ms']:
        key = step, 'w120_i080', 'mn9_only', 631430
        t, cells = frames[key]
        matrix = phase_counts(t, cells, len(ids), edges)
        first = np.full(len(ids), np.inf)
        np.minimum.at(first, cells, t)
        for k, (start, end) in enumerate(zip(edges[:-1], edges[1:])):
            c = matrix[k].toarray().ravel()
            phases.append(dict(step_ms=step, start_ms=start*1000, end_ms=end*1000,
                spikes=int(c.sum()), active_cells=int(np.count_nonzero(c)),
                newly_active_cells=int(np.count_nonzero((first>=start)&(first<end)))))
            for i in np.flatnonzero(c):
                phase_cells.append(dict(step_ms=step, start_ms=start*1000, end_ms=end*1000,
                    root_id=ids[i], spikes=int(c[i]), first_spike_ms=float(first[i]*1000)))
    pd.DataFrame(phases).to_csv(out/'burst_phases.csv', index=False)
    pd.DataFrame(phase_cells).merge(annotations, how='left', on='root_id', validate='many_to_one').to_csv(out/'burst_phase_neurons.csv', index=False)
    pd.DataFrame(contributors).merge(annotations, how='left', on='root_id', validate='many_to_one').sort_values(
        ['condition','mean_absolute_step_difference_hz'], ascending=[True,False]).to_csv(out/'contributors.csv', index=False)
    pd.DataFrame(burst_cells).merge(annotations, how='left', on='root_id', validate='many_to_one').to_csv(out/'altered_neurons.csv', index=False)
    for name, rows in [('temporal',temporal),('distances',seed_rows),('inputs',input_rows),('altered_trials',burst)]:
        pd.DataFrame(rows).to_csv(out/(name+'.csv'), index=False)
    write(out/'response_summary.json',response)
    write(out/'complete.json',{'status':'complete','trials_read':len(jobs),
        'annotations_sha256':digest(ROOT/'flywire_annotations.tsv'),
        'outputs':{p.name:digest(p) for p in out.iterdir()}})


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ['followup','verified','out']:
        p.add_argument('--'+name, required=True)
    args = p.parse_args()
    run(args.followup, args.verified, args.out)
