"""Describe saved response timing and baseline balance without new simulations."""
from collections import Counter
from pathlib import Path
import sys
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from eigencircuits.common import sha256, atomic_json, now, sugar_ids
from eigencircuits.controls import FULL_FEATURES, standardized_difference
from scripts.pcdr_ccr_transfer import read
from scripts.pcdr_composition_audit import ecdf_gap


def bins(times):
    times = np.asarray(times, dtype=float)
    if not np.isfinite(times).all() or np.any(times < 0) or np.any(times >= 1):
        raise ValueError('Invalid event time')
    return np.bincount(np.floor((times + 1e-12) / .01).astype(int), minlength=100)


def first_difference(a, b):
    # All five tested clocks divide 0.00625 ms; compare neuron/time events exactly.
    def keys(frame):
        tick = np.rint(frame.t.to_numpy() * 160000).astype(np.int64)
        if not np.allclose(frame.t, tick / 160000, atol=1e-10, rtol=0):
            raise ValueError('Event outside shared time grid')
        index = pd.MultiIndex.from_arrays([tick, frame.flywire_id.astype(str)])
        if not index.is_unique: raise ValueError('Duplicate spike event')
        return index
    x, y = keys(a), keys(b)
    different = x.symmetric_difference(y)
    return float(different.get_level_values(0).min() / 160) if len(different) else None


def main(out=None):
    base = ROOT / 'results/pcdr/results_ccr_20260927'
    original = base / 'raw_download/expanded_sensitivity'
    resolution = base / 'resolution_download'
    previous = base / 'followup_download/followup_20260927'
    out = Path(out) if out is not None else ROOT / 'docs/pcdr/evidence/2026-09-27/event_review'
    out.mkdir(exist_ok=False)
    plan = read(resolution / 'plan.json')
    features_path = ROOT / 'results/pcdr/corrected_20260919/analysis/features.parquet'
    atomic_json(out / 'protocol.json', {'recorded_utc': now(),
        'method': 'All 12 previously selected lesion/seed pairs at all five steps. Compare first distinct neuron/time event, 10 ms counts, peak excess bin and first cumulative excess of 1000 spikes. The 1000 crossing is descriptive, chosen for timing this review, not a biological onset or exclusion rule. Refresh fixed-comparator baseline means and any-spike recruitment using all 30 default seeds at each of three steps. No membership selection or optimizer.',
        'script_sha256': sha256(Path(__file__)), 'plan_sha256': sha256(resolution / 'plan.json'),
        'features_sha256': sha256(features_path)})
    hashes = {}
    def load(directory, name):
        m = read(directory / 'manifest.json')
        if m['status'] != 'complete': raise ValueError('Incomplete trial')
        p = directory / name
        actual = sha256(p)
        if actual != m['outputs'][name]: raise ValueError('Changed trial output')
        hashes[str(p.relative_to(ROOT))] = actual
        return pd.read_parquet(p)
    old_plan = read(previous / 'plan.json')
    lookup = {(j['source_trial'], j['dt_ms']): (previous / 'trials' / j['id'])
              for j in old_plan['jobs'] if j['stage'] in ['replay', 'timestep']}
    lookup.update({(j['source_trial'], j['dt_ms']): resolution / 'trials' / j['id']
                   for j in plan['jobs'] if j['stage'] == 'finer'})
    cases = sorted({(j['source_trial'], j['seed']) for j in plan['jobs']
                    if j['stage'] == 'finer' and j['condition'] != 'baseline'})
    timing, traces = [], []
    for source, seed in cases:
        for dt in [.1, .05, .025, .0125, .00625]:
            lesion, baseline = lookup[source, dt], lookup[f'w120_i080_baseline_{seed}', dt]
            a, b = load(lesion, 'spikes.parquet'), load(baseline, 'spikes.parquet')
            ca, cb = bins(a.t), bins(b.t)
            da, db = load(lesion, 'delivered_events.parquet'), load(baseline, 'delivered_events.parquet')
            delivery_difference = first_difference(da.assign(t=da.tick * dt / 1000), db.assign(t=db.tick * dt / 1000))
            excess = ca - cb
            crossings = np.flatnonzero(np.cumsum(excess) >= 1000)
            peak = int(np.argmax(excess))
            timing.append({'source_trial': source, 'dt_ms': dt,
                'first_spike_difference_ms': first_difference(a, b),
                'first_delivered_difference_ms': delivery_difference,
                'lesion_spikes': len(a), 'baseline_spikes': len(b),
                'first_1000_cumulative_excess_bin_end_ms': int((crossings[0]+1)*10) if len(crossings) else None,
                'peak_excess_bin_start_ms': peak*10, 'peak_excess_spikes': int(excess[peak]),
                'lesion_second_half_spikes': int(ca[50:].sum())})
            traces.extend({'source_trial': source, 'dt_ms': dt, 'bin_start_ms': i*10,
                           'lesion_spikes': int(ca[i]), 'baseline_spikes': int(cb[i])} for i in range(100))
    pd.DataFrame(timing).to_csv(out / 'timing.csv', index=False)
    pd.DataFrame(traces).to_csv(out / 'population_bins.csv', index=False)
    features = pd.read_parquet(features_path).set_index('root_id')
    features.index = features.index.astype(str)
    if not features.index.is_unique: raise ValueError('Duplicate feature IDs')
    sets = {j['condition']: j['lesion_ids'] for j in plan['jobs']
            if j['stage'] == 'default' and j['condition'] in ['mode', 'motor_003', 'motor_004', 'motor_005']}
    sensory = set(sugar_ids())
    baseline_jobs = {(j['dt_ms'], j['seed']): j for j in plan['jobs']
                     if j['stage'] == 'default' and j['condition'] == 'baseline'}
    balance, composition, capacities, member_rates = [], [], [], []
    for dt in [.1, .05, .025]:
        counts = []
        for seed in plan['seeds']:
            directory = original / 'trials' / f'default_baseline_{seed}' if dt == .1 else resolution / 'trials' / baseline_jobs[dt, seed]['id']
            frame = load(directory, 'rates.parquet')
            if frame.root_id.duplicated().any() or not set(frame.root_id) <= set(features.index):
                raise ValueError('Invalid baseline IDs')
            values = frame.set_index('root_id').rate_hz.reindex(features.index, fill_value=0).to_numpy()
            if not np.isfinite(values).all() or np.any(values < 0): raise ValueError('Invalid rate')
            counts.append(values)
        current = features.copy()
        current['baseline_hz'] = np.mean(counts, axis=0)
        current['recruited'] = np.any(np.asarray(counts) > 0, axis=0)
        current['trials_active'] = (np.asarray(counts) > 0).sum(axis=0)
        target = current.loc[sets['mode']]
        def strata(f):
            return Counter(zip(f.model_sign.astype(str), f.recruited.astype(bool), f.super_class.eq('motor')))
        target_strata = strata(target)
        pool = current.loc[~current.index.isin(set(sets['mode']) | sensory)]
        available = strata(pool)
        for key, required in target_strata.items():
            capacities.append({'dt_ms': dt, 'model_sign': key[0], 'recruited': key[1], 'motor': key[2],
                               'required': required, 'available': available[key]})
        for condition, members in sets.items():
            sample = current.loc[members]
            member_rates.extend({'dt_ms': dt, 'condition': condition, 'root_id': rid,
                'baseline_hz': float(row.baseline_hz), 'trials_active': int(row.trials_active)}
                for rid, row in sample.iterrows())
            composition.append({'dt_ms': dt, 'condition': condition,
                'recruited_cells': int(sample.recruited.sum()), 'motor_cells': int(sample.super_class.eq('motor').sum()),
                'strata_match': strata(sample) == target_strata})
            for col in FULL_FEATURES:
                a, b = [np.log1p(f[col].to_numpy(float)) for f in [target, sample]]
                balance.append({'dt_ms': dt, 'condition': condition, 'feature': col,
                    'smd': float(standardized_difference(a[:, None], b[:, None])[0]),
                    'ecdf_gap': ecdf_gap(a, b), 'variance_ratio': float(b.var()/a.var()) if a.var() else None})
    pd.DataFrame(balance).to_csv(out / 'baseline_balance.csv', index=False)
    pd.DataFrame(composition).to_csv(out / 'composition.csv', index=False)
    pd.DataFrame(capacities).to_csv(out / 'stratum_capacity.csv', index=False)
    pd.DataFrame(member_rates).to_csv(out / 'member_baseline_rates.csv', index=False)
    atomic_json(out / 'record.json', {'completed_utc': now(), 'timing_pairs': len(timing),
        'baseline_trials': 90, 'inputs': hashes,
        'outputs': {p.name: sha256(p) for p in out.iterdir() if p.is_file()}})


if __name__ == '__main__':
    main()
