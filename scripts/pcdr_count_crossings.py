"""Reconstruct actual target states when their saved cumulative counts first differ by two."""
import argparse
from pathlib import Path
import sys
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.pcdr_ccr_transfer import read, write, digest, utc
from scripts.pcdr_recurrent_delivery import accepted
from scripts.pcdr_first_spike import kernel


def first_gap(a, b):
    a, b = np.asarray(a, dtype=np.int64), np.asarray(b, dtype=np.int64)
    if any(np.any(np.diff(x) <= 0) or np.any(x < 0) for x in (a, b)):
        raise ValueError('Sorted unique nonnegative spikes required')
    times = np.union1d(a, b)
    delta = np.searchsorted(a, times, side='right') - np.searchsorted(b, times, side='right')
    found = np.flatnonzero(abs(delta) >= 2)
    if not len(found):
        return None
    i = int(found[0])
    return dict(tick=int(times[i]), coarse_minus_fine=int(delta[i]), leader='coarse' if delta[i] > 0 else 'fine')


def state(arrivals, weights, post, tick):
    arrivals, weights, post = np.asarray(arrivals), np.asarray(weights), np.asarray(post)
    previous = post[post < tick]
    last = int(previous[-1]) if len(previous) else -1
    ready = last < 0 or tick - last >= 22000
    in_segment = (arrivals > last) & (arrivals < tick)
    allow = accepted(arrivals, post, 22000)
    keep = in_segment & allow
    contribution = weights[keep] * kernel((tick - arrivals[keep]) * .0001)
    return dict(tick=int(tick), last_reset_tick=None if last < 0 else last, ready=bool(ready),
        voltage_mv=-52. + float(contribution.sum()), excitatory_voltage_mv=float(contribution[weights[keep] > 0].sum()),
        inhibitory_voltage_mv=float(contribution[weights[keep] < 0].sum()),
        accepted_since_reset=int(keep.sum()), blocked_since_reset=int((in_segment & ~allow).sum()),
        accepted_exc_jump_mv=float(weights[keep & (weights > 0)].sum()),
        accepted_inh_jump_magnitude_mv=float(-weights[keep & (weights < 0)].sum()),
        blocked_exc_jump_mv=float(weights[in_segment & ~allow & (weights > 0)].sum()),
        blocked_inh_jump_magnitude_mv=float(-weights[in_segment & ~allow & (weights < 0)].sum()))


def run(out):
    prior = ROOT / 'docs/pcdr/evidence/2026-10-09/baseline_count_replay'
    snap = read(prior / 'snapshot.json')
    for name, expected in snap['files'].items():
        if digest(prior / name) != expected:
            raise ValueError('Changed prior evidence')
    out.mkdir(parents=True, exist_ok=False)
    paths = [Path(__file__), ROOT / 'scripts/pcdr_first_spike.py', ROOT / 'scripts/pcdr_recurrent_delivery.py', prior / 'results.json', prior / 'snapshot.json']
    write(out / 'protocol.json', dict(recorded_utc=utc(), inputs={str(p): digest(p) for p in paths},
        selection='Keep prior 26 targets and their prefix bounds, four absent cases. At union of actual target spikes, find first post-event absolute cumulative count difference >=2. Simultaneous events processed together. Leading run evaluated immediately before threshold at that event; other run evaluated at latest native tick no later than event, with lag reported (0 or .0001 ms).',
        method='Analytical impulse response since last observed reset, accepted actual arrivals only, threshold before arrivals. Verify leading previous native tick <=threshold and event >threshold; compare other native state with saved spike/readiness. No fabricated arrivals, intervention or full-network simulation.',
        limitations='Conditional reconstructed states, no direct recordings for these targets. State difference may be consequence of earlier resets; it does not locate the initiating cause. Event states are at most one fine tick apart. Two-spike criterion is exploratory selection, not new convergence threshold.'))
    records = []
    for r in read(prior / 'results.json')['records']:
        seed = r['seed']
        if r['selection'] is None:
            records.append(dict(seed=seed, selected=False))
            continue
        if not all(r['exact_native_replays']):
            raise ValueError('Native replay unverified')
        gap = first_gap(r['coarse_actual'], r['fine_actual'])
        if gap is None:
            raise ValueError('Prior selected count gap absent')
        path = ROOT / 'results/pcdr/baseline_count_replay_20261009' / f'{seed}_inputs.npz'
        if digest(path) != snap['local_input_array_hashes'][path.name]:
            raise ValueError('Changed input arrays')
        row = dict(seed=seed, selected=True, target_id=r['selection']['target_id'], gap=gap, states={})
        with np.load(path) as z:
            for label, factor in [('coarse', 2), ('fine', 1)]:
                tick = gap['tick'] // factor * factor
                post = r[label + '_actual']
                result = state(z[label+'_arrivals'], z[label+'_weights'], post, tick)
                result['lag_from_event_tick'] = gap['tick'] - tick
                result['saved_spike'] = tick in post
                result['threshold_consistent'] = (result['ready'] and result['voltage_mv'] > -45) == result['saved_spike']
                row['states'][label] = result
                if label == gap['leader']:
                    previous = state(z[label+'_arrivals'], z[label+'_weights'], post, tick-factor)
                    row['previous_leader_state'] = previous
                    row['leading_crossing_check'] = previous['voltage_mv'] <= -45 < result['voltage_mv'] and result['ready'] and result['saved_spike']
        records.append(row)
    valid = all(r['leading_crossing_check'] and all(s['threshold_consistent'] for s in r['states'].values()) for r in records if r['selected'])
    write(out / 'results.json', dict(status='passed' if valid else 'failed', completed_utc=utc(), records=records))
    if not valid:
        raise ValueError('Crossing mismatch; preserve output')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    run(p.parse_args().out)
