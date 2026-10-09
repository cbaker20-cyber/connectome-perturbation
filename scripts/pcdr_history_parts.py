"""Sensitivity of local replays to paired event times and surplus histories."""
import argparse
from pathlib import Path
import sys
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.pcdr_ccr_transfer import read, write, digest, utc
from scripts.pcdr_local_replay import replay
from scripts.pcdr_bounded_process import run_bounded


def split_events(a, b, rule):
    a, b = np.asarray(a), np.asarray(b)
    if rule not in ('first', 'last'):
        raise ValueError('Unknown matching rule')
    for x in (a, b):
        if x.ndim != 1 or (len(x) and (not np.issubdtype(x.dtype, np.integer)
                or np.any(x < 0) or np.any(np.diff(x) <= 0))):
            raise ValueError('Sorted unique nonnegative integer events required')
    a, b = a.astype(np.int64), b.astype(np.int64)
    n = min(len(a), len(b))
    if rule == 'first' or n == 0:
        return a[:n], b[:n], a[n:], b[n:]
    return a[-n:], b[-n:], a[:-n], b[:-n]


def worker(out):
    p = read(out / 'protocol.json')
    for path, expected in p['inputs'].items():
        if digest(path) != expected:
            raise ValueError('Changed input: ' + path)
    previous = ROOT / 'docs/pcdr/evidence/2026-10-09/baseline_count_replay'
    prior = read(previous / 'results.json')['records']
    spike_hashes = read(ROOT / 'docs/pcdr/evidence/2026-10-09/baseline_counts/summary.json')['input_hashes']
    source = ROOT / 'results/pcdr/fine_download_20261005'
    jobs = read(source / 'plan.json')['jobs']
    con = pd.read_parquet(ROOT / '2023_03_23_connectivity_630_final.parquet')
    con.Presynaptic_ID = con.Presynaptic_ID.astype(str)
    con.Postsynaptic_ID = con.Postsynaptic_ID.astype(str)
    con = con.set_index('Postsynaptic_ID')
    records, sources = [], []
    for r in prior:
        seed = r['seed']
        if r['selection'] is None:
            records.append(dict(seed=seed, selection=None))
            continue
        if not all(r['exact_native_replays']):
            raise ValueError('Unverified native replay')
        target, stop = r['selection']['target_id'], r['stop_tick']
        edges = con.loc[[target]]
        if edges.Presynaptic_ID.duplicated().any():
            raise ValueError('Duplicate connections')
        weights = dict(zip(edges.Presynaptic_ID, edges['Excitatory x Connectivity'].to_numpy(float) * .275))
        frames = []
        for dt in (.0002, .0001):
            matches = [j for j in jobs if j['stage'] == 'fine' and j['condition'] == 'baseline'
                and j['variant'] == 'default' and j['seed'] == seed and j['dt_ms'] == dt]
            if len(matches) != 1:
                raise ValueError('Unexpected trial inventory')
            path = source / 'trials' / matches[0]['id'] / 'spikes.parquet'
            if digest(path) != spike_hashes[str(path)]:
                raise ValueError('Changed spike file')
            f = pd.read_parquet(path)
            f = f[f.flywire_id.isin(weights)].copy()
            f['arrival'] = np.rint(f.t.to_numpy() * 10000000).astype(np.int64) + 18000
            frames.append({key: np.sort(g.arrival.to_numpy()) for key, g in f[f.arrival < stop].groupby('flywire_id')})
        # Verify the ID reconstruction against the previously checked input arrays.
        input_path = ROOT / 'results/pcdr/baseline_count_replay_20261009' / f'{seed}_inputs.npz'
        expected = read(previous / 'snapshot.json')['local_input_array_hashes'][input_path.name]
        if digest(input_path) != expected:
            raise ValueError('Changed prior arrivals')
        with np.load(input_path) as z:
            for group, label in zip(frames, ('coarse', 'fine')):
                actual = sorted((int(t), weights[key]) for key, times in group.items() for t in times)
                if actual != sorted(zip(z[label + '_arrivals'].tolist(), z[label + '_weights'].tolist())):
                    raise ValueError('Input reconstruction mismatch')
        for rule in ('first', 'last'):
            histories = {key: [] for key in ('cc', 'cf', 'fc', 'ff')}
            shifts = []
            for neuron in sorted(set(frames[0]) | set(frames[1])):
                a, b = frames[0].get(neuron, []), frames[1].get(neuron, [])
                ca, fb, extra_c, extra_f = split_events(a, b, rule)
                shifts.extend((ca - fb).tolist())
                sources.append(dict(seed=seed, rule=rule, source_id=neuron, weight_mv=weights[neuron],
                    coarse_events=len(a), fine_events=len(b), paired_events=len(ca),
                    shifted_pairs=int(np.count_nonzero(ca != fb)), surplus_coarse=len(extra_c), surplus_fine=len(extra_f)))
                for key, matched, extra in [('cc', ca, extra_c), ('cf', ca, extra_f), ('fc', fb, extra_c), ('ff', fb, extra_f)]:
                    histories[key].extend((int(t), weights[neuron], neuron) for t in np.r_[matched, extra])
            results = {}
            for key, events in histories.items():
                events.sort()
                # Constructed histories can collide; retain their multiplicities and report them.
                duplicates = len(events) - len(set((t, neuron) for t, w, neuron in events))
                arrivals = np.array([t for t, w, neuron in events], dtype=np.int64)
                w = np.array([w for t, w, neuron in events])
                spikes = replay(arrivals, w, stop, .0001)
                results[key] = dict(count=len(spikes), spikes=spikes.tolist(), duplicate_source_ticks=duplicates, incoming_events=len(events))
                np.savez(out / f'{seed}_{rule}_{key}.npz', arrivals=arrivals, weights=w)
            if results['cc']['spikes'] != r['fine_grid_coarse_history'] or results['ff']['spikes'] != r['fine_actual']:
                raise ValueError('Reconstructed original-history replay differs')
            records.append(dict(seed=seed, selection=r['selection'], rule=rule, histories=results,
                paired_events=len(shifts), median_absolute_shift_ms=None if not shifts else float(np.median(np.abs(shifts)) * .0001)))
            write(out / f'{seed}_{rule}.json', records[-1])
    pd.DataFrame(sources).to_csv(out / 'sources.csv', index=False)
    write(out / 'results.json', dict(completed_utc=utc(), records=records))


def run(out):
    previous = ROOT / 'docs/pcdr/evidence/2026-10-09/baseline_count_replay'
    for name, expected in read(previous / 'snapshot.json')['files'].items():
        if digest(previous / name) != expected:
            raise ValueError('Changed previous evidence')
    old_protocol = read(previous / 'protocol.json')
    paths = [Path(__file__), ROOT / 'scripts/pcdr_local_replay.py', previous / 'results.json', previous / 'snapshot.json',
        ROOT / 'results/pcdr/fine_download_20261005/plan.json', ROOT / '2023_03_23_connectivity_630_final.parquet',
        ROOT / 'docs/pcdr/evidence/2026-10-09/baseline_counts/summary.json']
    for path in paths[1:]:
        if str(path) in old_protocol['inputs'] and digest(path) != old_protocol['inputs'][str(path)]:
            raise ValueError('Changed original provenance')
    out.mkdir(parents=True, exist_ok=False)
    write(out / 'protocol.json', dict(recorded_utc=utc(), inputs={str(p): digest(p) for p in paths},
        design='Keep prior 26 count-selected cases and four absent cases. Within each presynaptic ID, pair first min(nc,nf) arrivals by order, then repeat pairing last min(nc,nf) as sensitivity. Paired timestamps and remaining surplus histories define a 2x2: cc=coarse paired/coarse surplus; cf=coarse paired/fine surplus; fc=fine paired/coarse surplus; ff=fine paired/fine surplus. All replay at .0001 ms through original checkpoint.',
        interpretation='Timing contrasts hold per-source counts fixed; surplus contrasts change unmatched event counts AND their times. Surplus is matching-rule dependent, not proof of inserted/deleted physical spikes. Hybrids may duplicate same-source times or violate source refractoriness: retain and report duplicate events, never call them realizable network activity. No claim of a unique causal timing/count decomposition.',
        budget='One local worker with 180-second deadline, no network simulation or automatic retry. Require both original endpoint histories to match prior validated replay exactly.',
        outputs='Per-source partition, all spike lists and local input arrays. Report both rules including opposing/null effects, not only desired results.'))
    process = run_bounded([sys.executable, str(Path(__file__).resolve()), '--out', str(out), '--worker'], out / 'logs', 180, cwd=ROOT)
    write(out / 'process.json', process)
    if process['returncode'] != 0 or process['timed_out']:
        raise RuntimeError('History worker failed; inspect retained process/logs')
    print(process)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--worker', action='store_true')
    args = parser.parse_args()
    worker(args.out) if args.worker else run(args.out)
