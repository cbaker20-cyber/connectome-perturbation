"""Replay the earliest fixed-checkpoint baseline count gap of at least two."""
import argparse
import json
from pathlib import Path
import sys
import zipfile
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.pcdr_ccr_transfer import read, write, digest, utc
from scripts.pcdr_local_replay import replay
from scripts.pcdr_bounded_process import run_bounded


def select_event(a, b, excluded):
    neurons = sorted((set(a) | set(b)) - set(excluded))
    for group in (a, b):
        for values in group.values():
            x = np.asarray(values)
            if (x.ndim != 1 or not np.issubdtype(x.dtype, np.integer)
                    or np.any(x < 0) or np.any(np.diff(x) <= 0)):
                raise ValueError('Expected sorted unique nonnegative integer ticks')
    for end_ms in range(100, 1001, 100):
        stop = end_ms * 10000
        candidates = []
        for neuron in neurons:
            ca = int(np.searchsorted(a.get(neuron, []), stop))
            cb = int(np.searchsorted(b.get(neuron, []), stop))
            if abs(ca - cb) >= 2:
                candidates.append((-abs(ca - cb), neuron, ca, cb))
        if candidates:
            gap, neuron, ca, cb = min(candidates)
            return dict(target_id=neuron, end_ms=end_ms, stop_tick=stop,
                coarse_count=ca, fine_count=cb, absolute_gap=-gap)
    return None


def worker(out):
    p = read(out / 'protocol.json')
    for path, expected in p['inputs'].items():
        if digest(path) != expected:
            raise ValueError('Changed input: ' + path)
    prior = ROOT / 'docs/pcdr/evidence/2026-10-09/baseline_counts'
    hashes = read(prior / 'summary.json')['input_hashes']
    source = ROOT / 'results/pcdr/fine_download_20261005'
    plan = read(source / 'plan.json')
    jobs = [j for j in plan['jobs'] if j['stage'] == 'fine' and j['condition'] == 'baseline'
            and j['variant'] == 'default' and j['dt_ms'] in (.0002, .0001)]
    keys = {(j['seed'], j['dt_ms']): j for j in jobs}
    seeds = sorted({j['seed'] for j in jobs})
    if len(seeds) != 30 or len(keys) != 60 or len(jobs) != 60:
        raise ValueError('Unexpected trial inventory')
    con = pd.read_parquet(ROOT / '2023_03_23_connectivity_630_final.parquet')
    con.Presynaptic_ID = con.Presynaptic_ID.astype(str)
    con.Postsynaptic_ID = con.Postsynaptic_ID.astype(str)
    con = con.set_index('Postsynaptic_ID', drop=False)
    results = []
    with zipfile.ZipFile(ROOT / 'CCR_fine_results.zip') as z:
        for seed in seeds:
            frames, groups = [], []
            original_path = ROOT / f'results/pcdr/results_ccr_20260927/raw_download/expanded_sensitivity/trials/default_baseline_{seed}/manifest.json'
            old = read(original_path)
            for dt in (.0002, .0001):
                j = keys[seed, dt]
                manifest = json.loads(z.read('trials/' + j['id'] + '/manifest.json'))
                if manifest['spec'] != j or manifest['status'] != 'complete' or digest(original_path) != manifest['source_manifest_sha256']:
                    raise ValueError('Changed source trial')
                path = source / 'trials' / j['id'] / 'spikes.parquet'
                if digest(path) != hashes[str(path)] or hashes[str(path)] != manifest['outputs']['spikes.parquet']:
                    raise ValueError('Changed spikes')
                f = pd.read_parquet(path)
                native = f.t.to_numpy() * 1000 / dt
                if not np.isfinite(native).all() or np.max(abs(native - np.rint(native)), initial=0) > 1e-6:
                    raise ValueError('Invalid spike times')
                f['tick'] = np.rint(native).astype(np.int64) * round(dt / .0001)
                frames.append(f)
                groups.append({neuron: np.sort(g.tick.to_numpy()) for neuron, g in f.groupby('flywire_id')})
            for name in ['model.py', '2023_03_23_connectivity_630_final.parquet']:
                expected = old['provenance']['sources' if name == 'model.py' else 'inputs'][name]
                if p['inputs'][str(ROOT / name)] != expected:
                    raise ValueError('Model/data differ from original provenance')
            selected = select_event(*groups, old['input_ids'])
            if selected is None:
                results.append(dict(seed=seed, selection=None))
                write(out / f'{seed}.json', results[-1])
                continue
            target = selected['target_id']
            # Use the recorded checkpoint without extending or optimizing the window.
            stop = selected['stop_tick']
            edges = con.loc[[target]]
            if edges.Presynaptic_ID.duplicated().any():
                raise ValueError('Duplicate incoming connections')
            weights = dict(zip(edges.Presynaptic_ID, edges['Excitatory x Connectivity'].to_numpy(float) * .275))
            predicted, actual, inputs = [], [], []
            for f, dt, g in zip(frames, (.0002, .0001), groups):
                selected_inputs = f[f.flywire_id.isin(weights)].copy()
                arrivals = selected_inputs.tick.to_numpy() + 18000
                w = selected_inputs.flywire_id.map(weights).to_numpy(float)
                mask = arrivals < stop
                inputs.append((arrivals[mask], w[mask]))
                factor = round(dt / .0001)
                predicted.append(replay(arrivals // factor, w, stop // factor, dt) * factor)
                actual.append(g[target][g[target] < stop])
            matched = [bool(np.array_equal(x, y)) for x, y in zip(predicted, actual)]
            record = dict(seed=seed, selection=selected, stop_tick=stop, exact_native_replays=matched,
                coarse_actual=actual[0].tolist(), fine_actual=actual[1].tolist(),
                coarse_predicted=predicted[0].tolist(), fine_predicted=predicted[1].tolist())
            np.savez(out / f'{seed}_inputs.npz', coarse_arrivals=inputs[0][0], coarse_weights=inputs[0][1],
                fine_arrivals=inputs[1][0], fine_weights=inputs[1][1])
            if all(matched):
                hybrid = replay(*inputs[0], stop, .0001)
                record.update(fine_grid_coarse_history=hybrid.tolist(),
                    input_history_changes_fine_grid_spikes=not np.array_equal(hybrid, predicted[1]),
                    input_history_changes_fine_grid_count=len(hybrid) != len(predicted[1]))
            write(out / f'{seed}.json', record)
            results.append(record)
    write(out / 'results.json', dict(completed_utc=utc(), records=results,
        selected=sum(r['selection'] is not None for r in results),
        failed_native_replay_seeds=[r['seed'] for r in results if r['selection'] is not None and not all(r['exact_native_replays'])]))


def run(out):
    archive = ROOT / 'CCR_fine_results.zip'
    check = ROOT / 'results/pcdr/fine_verified_20261005/full_check.json'
    if digest(archive) != read(check)['archive_sha256']:
        raise ValueError('Changed archive')
    prior = ROOT / 'docs/pcdr/evidence/2026-10-09/baseline_counts'
    for name, expected in read(prior / 'snapshot.json')['files'].items():
        if digest(prior / name) != expected:
            raise ValueError('Changed prior evidence')
    plan = ROOT / 'results/pcdr/fine_download_20261005/plan.json'
    if digest(plan) != read(check)['plan_sha256']:
        raise ValueError('Changed plan')
    out.mkdir(parents=True, exist_ok=False)
    paths = [Path(__file__), ROOT / 'scripts/pcdr_local_replay.py', archive, plan,
        prior / 'summary.json', ROOT / 'model.py', ROOT / '2023_03_23_connectivity_630_final.parquet']
    write(out / 'protocol.json', dict(recorded_utc=utc(), inputs={str(p): digest(p) for p in paths},
        selection='Amendment after early timing selection changed no short-prefix counts. For every default seed, use original 100,200,...,1000-ms checkpoints. At earliest checkpoint with a non-input neuron having absolute coarse-minus-fine cumulative count gap >=2, choose largest gap then lowest root ID. Preserve no-selection seeds. Two spikes is a diagnostic selection rule, not a scientific acceptance threshold.',
        replay='All selected targets from initial rest to their selected half-open checkpoint. Original saved incoming histories at both native steps; require every saved target tick to match before fixed-fine-grid comparison. Then use coarse saved incoming history at fine dt, compare with fine history. No network feedback replay.',
        budget='One worker, 180-second external deadline, no automatic retry. Keep failed/missing native replays and do not interpret their hybrid.',
        limitations='Exploratory selection on a two-spike checkpoint gap is not a scientific tolerance; results are selected for count disagreement. Short local histories condition on archived network spikes. They do not establish the first network cause, explain full-second count error, demonstrate chaos, or alter convergence criteria.'))
    result = run_bounded([sys.executable, str(Path(__file__).resolve()), '--out', str(out), '--worker'], out / 'logs', 180, cwd=ROOT)
    write(out / 'process.json', result)
    print(result)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--worker', action='store_true')
    args = parser.parse_args()
    worker(args.out) if args.worker else run(args.out)
