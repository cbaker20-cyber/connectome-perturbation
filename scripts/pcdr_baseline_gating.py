"""Compare refractory acceptance of exactly shared archived incoming events."""
import argparse
from pathlib import Path
import sys
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.pcdr_ccr_transfer import read, write, digest, utc
from scripts.pcdr_recurrent_delivery import accepted


def compare(a, b, post_a, post_b):
    for frame in (a, b):
        if frame.duplicated(['source_id', 'tick']).any():
            raise ValueError('Duplicate source event')
        if (not frame.source_id.map(lambda x: type(x) is str).all()
                or not np.issubdtype(frame.tick.dtype, np.integer)
                or (frame.tick < 0).any() or not np.isfinite(frame.weight_mv).all()):
            raise ValueError('Invalid incoming events')
    for post in (post_a, post_b):
        x = np.asarray(post)
        if x.ndim != 1 or (len(x) and (not np.issubdtype(x.dtype, np.integer)
                or (x < 0).any() or (np.diff(x) <= 0).any())):
            raise ValueError('Invalid target spikes')
    a, b = a.copy(), b.copy()
    a['accept'] = accepted(a.tick.to_numpy(), post_a, 22000)
    b['accept'] = accepted(b.tick.to_numpy(), post_b, 22000)
    joined = a.merge(b, on=['source_id', 'tick'], how='outer', suffixes=('_coarse', '_fine'), indicator=True)
    both = joined._merge.eq('both')
    if not (joined.loc[both, 'weight_mv_coarse'] == joined.loc[both, 'weight_mv_fine']).all():
        raise ValueError('Changed weight for common event')
    changed = joined[both & joined.accept_coarse.ne(joined.accept_fine)].copy()
    changed = changed.sort_values(['tick', 'source_id'])
    return joined, changed


def run(out):
    prior = ROOT / 'docs/pcdr/evidence/2026-10-09/baseline_count_replay'
    snap = read(prior / 'snapshot.json')
    for name, expected in snap['files'].items():
        if digest(prior / name) != expected:
            raise ValueError('Changed prior evidence')
    old = read(prior / 'protocol.json')
    con_path = ROOT / '2023_03_23_connectivity_630_final.parquet'
    plan_path = ROOT / 'results/pcdr/fine_download_20261005/plan.json'
    hash_path = ROOT / 'docs/pcdr/evidence/2026-10-09/baseline_counts/summary.json'
    for path in (con_path, plan_path, hash_path):
        if digest(path) != old['inputs'][str(path)]:
            raise ValueError('Changed original provenance')
    out.mkdir(parents=True, exist_ok=False)
    paths = [Path(__file__), ROOT / 'scripts/pcdr_recurrent_delivery.py', prior / 'results.json', prior / 'snapshot.json', con_path, plan_path, hash_path]
    write(out / 'protocol.json', dict(recorded_utc=utc(), inputs={str(p): digest(p) for p in paths},
        design='All prior 26 count-selected targets/checkpoints and four absent seeds. Reconstruct native arrival acceptance using saved target spikes and 2.2-ms refractory duration. Join only exact source-ID/common-tick matches; no ordinal pairing or mixed histories. Retain all unmatched events and shared-event acceptance changes.',
        limits='Conditional model reconstruction, not direct state recording. Exact shared-event restriction omits shifted arrivals and may hide much of the divergence. First changed acceptance is not necessarily the initiating cause; target spikes define gating. No new scientific tolerance, network run, or causal intervention.'))
    con = pd.read_parquet(con_path)
    con.Presynaptic_ID = con.Presynaptic_ID.astype(str)
    con.Postsynaptic_ID = con.Postsynaptic_ID.astype(str)
    con = con.set_index('Postsynaptic_ID')
    jobs = read(plan_path)['jobs']
    hashes = read(hash_path)['input_hashes']
    rows, changed_rows = [], []
    for r in read(prior / 'results.json')['records']:
        seed = r['seed']
        if r['selection'] is None:
            rows.append(dict(seed=seed, selected=False))
            continue
        if not all(r['exact_native_replays']):
            raise ValueError('Unverified native target replay')
        target, stop = r['selection']['target_id'], r['stop_tick']
        edge = con.loc[[target], ['Presynaptic_ID', 'Excitatory x Connectivity']]
        frames = []
        for dt, label in ((.0002, 'coarse'), (.0001, 'fine')):
            matches = [j for j in jobs if j['stage'] == 'fine' and j['condition'] == 'baseline' and j['variant'] == 'default' and j['seed'] == seed and j['dt_ms'] == dt]
            if len(matches) != 1:
                raise ValueError('Unexpected trial inventory')
            path = plan_path.parent / 'trials' / matches[0]['id'] / 'spikes.parquet'
            if digest(path) != hashes[str(path)]:
                raise ValueError('Changed spikes')
            f = pd.read_parquet(path)
            f = f.merge(edge, left_on='flywire_id', right_on='Presynaptic_ID', validate='many_to_one')
            ticks = f.t.to_numpy() * 10000000
            if not np.allclose(ticks, np.rint(ticks), atol=1e-6, rtol=0):
                raise ValueError('Off-grid events')
            frame = pd.DataFrame(dict(source_id=f.flywire_id, tick=np.rint(ticks).astype(np.int64) + 18000,
                weight_mv=f['Excitatory x Connectivity'] * .275))
            frame = frame[frame.tick < stop].reset_index(drop=True)
            arrays = ROOT / 'results/pcdr/baseline_count_replay_20261009' / f'{seed}_inputs.npz'
            if digest(arrays) != snap['local_input_array_hashes'][arrays.name]:
                raise ValueError('Changed prior arrival arrays')
            with np.load(arrays) as z:
                if sorted(zip(frame.tick, frame.weight_mv)) != sorted(zip(z[label+'_arrivals'], z[label+'_weights'])):
                    raise ValueError('Arrival mismatch')
            frames.append(frame)
        joined, changed = compare(*frames, r['coarse_actual'], r['fine_actual'])
        joined.to_parquet(out / f'{seed}_events.parquet', index=False)
        first_spike_difference = min(set(r['coarse_actual']) ^ set(r['fine_actual']), default=None)
        row = dict(seed=seed, selected=True, target_id=target, end_ms=stop*.0001,
            coarse_events=len(frames[0]), fine_events=len(frames[1]),
            shared_events=int(joined._merge.eq('both').sum()), coarse_only=int(joined._merge.eq('left_only').sum()),
            fine_only=int(joined._merge.eq('right_only').sum()), shared_acceptance_changes=len(changed),
            first_target_spike_difference_tick=first_spike_difference,
            first_shared_acceptance_change_tick=None if changed.empty else int(changed.tick.iloc[0]))
        rows.append(row)
        for x in changed.to_dict('records'):
            changed_rows.append(dict(seed=seed, source_id=x['source_id'], tick=int(x['tick']), weight_mv=x['weight_mv_coarse'],
                accepted_coarse=bool(x['accept_coarse']), accepted_fine=bool(x['accept_fine'])))
    pd.DataFrame(changed_rows).to_csv(out / 'changed_acceptance.csv', index=False)
    write(out / 'results.json', dict(completed_utc=utc(), records=rows))
    write(out / 'complete.json', dict(status='complete', outputs={p.name: digest(p) for p in out.iterdir() if p.is_file()}))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    run(p.parse_args().out)
