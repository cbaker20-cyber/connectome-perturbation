"""Descriptive feasibility audit; reads selection features, never lesion outcomes."""
from pathlib import Path
import inspect
import json
import sys
import time

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from eigencircuits import controls
from eigencircuits.common import atomic_json, now, sha256, sugar_ids

OUT = ROOT / 'results/pcdr/matching_audit_20260921'
FEATURES = ROOT / 'results/pcdr/corrected_20260919/analysis/features.parquet'
SELECTION = ROOT / 'results/pcdr/exploratory80_20260921/modes/selection.json'


def mean_bounds(values, target_strata, pool_strata):
    """Exact coordinatewise extrema under fixed stratum counts, not joint bounds."""
    low = np.zeros(values.shape[1]); high = low.copy()
    for key, count in target_strata.items():
        a = np.sort(values[pool_strata[key]], axis=0)
        if len(a) < count:
            raise ValueError('Insufficient stratum capacity')
        low += a[:count].sum(0); high += a[-count:].sum(0)
    n = sum(target_strata.values())
    return low/n, high/n


def instrumented_sampler(observe):
    """Insert a read-only callback after SMD calculation, before rejection."""
    source = inspect.getsource(controls.matched_sets)
    anchor = '        balance = standardized_difference(target, transformed[indices])\n'
    assert source.count(anchor) == 1
    source = source.replace(anchor, anchor + '        observe(attempts, indices, balance)\n')
    namespace = dict(vars(controls), observe=observe)
    exec(compile(source, 'instrumented_matched_sets.py', 'exec'), namespace)
    return namespace['matched_sets'], source


def main():
    OUT.mkdir(exist_ok=False)
    atomic_json(OUT/'protocol.json', {
        'recorded_utc': now(), 'purpose': 'Explain prior matching failure using baseline-only data.',
        'fixed': 'Same 51 targets, input exclusions, model-sign/recruited strata, log1p six features, pooled population-variance SMD <=0.1.',
        'checks': ['ID/hash and finite feature checks', 'stratum capacity',
                   'coordinatewise attainable mean bounds for full pool and nearest-64 union',
                   'exact seeded sampler replay with rejected SMDs saved'],
        'replay_seed': 630600, 'replay_attempts': 50000,
        'limits': 'Marginal mean bounds do not prove joint feasibility. Sampler failure does not prove impossibility. No outcome data, simulation, threshold relaxation or alternative mode.',
        'command': [sys.executable, str(Path(__file__).resolve())],
        'inputs': {str(p.relative_to(ROOT)): sha256(p) for p in [FEATURES, SELECTION, Path(controls.__file__), Path(__file__)]}
    })
    start = time.monotonic()
    f = pd.read_parquet(FEATURES); f.root_id = f.root_id.astype(str)
    old = json.loads((ROOT/'results/pcdr/exploratory80_20260921/controls/manifest.json').read_text())
    assert sha256(FEATURES) == old['features_sha256']
    assert sha256(SELECTION) == old['selection_sha256']
    ids = json.loads(SELECTION.read_text())['root_ids']
    assert set(ids) == set(old['target_ids']) and len(ids) == len(set(ids))
    assert not f.root_id.duplicated().any()
    cols = controls.FULL_FEATURES
    raw = f[cols].to_numpy(float)
    assert np.isfinite(raw).all() and (raw >= 0).all()
    x = np.log1p(raw); scale = x.std(0); scale[scale == 0] = 1
    z = x/scale
    ti = np.flatnonzero(f.root_id.isin(ids)); pool_mask = ~f.root_id.isin(set(ids)|set(sugar_ids()))
    strata = list(zip(f.model_sign.astype(str), f.recruited.astype(bool)))
    counts = {k: sum(strata[i] == k for i in ti) for k in sorted(set(strata[i] for i in ti))}
    pools = {}; near = {}; capacity = []
    for k, n in counts.items():
        pool = np.array([i for i in np.flatnonzero(pool_mask) if strata[i] == k])
        pools[k] = pool
        targets = [i for i in ti if strata[i] == k]
        _, indices = cKDTree(z[pool]).query(z[targets], k=min(64, len(pool)))
        near[k] = np.unique(pool[np.asarray(indices).reshape(-1)])
        capacity.append({'model_sign': k[0], 'recruited': k[1], 'needed': n,
                         'available': len(pool), 'nearest64_union': len(near[k])})
    pd.DataFrame(capacity).to_csv(OUT/'strata.csv', index=False)
    bounds = []
    for name, groups in [('full_pool', pools), ('nearest64_union', near)]:
        low, high = mean_bounds(x, counts, groups)
        # Popoviciu's bound: any selected sample variance <= range**2/4.
        combined = np.concatenate(list(groups.values()))
        variance_upper = np.ptp(x[combined], axis=0)**2/4
        gap = np.maximum(np.maximum(low-x[ti].mean(0), x[ti].mean(0)-high), 0)
        denom = np.sqrt((x[ti].var(0)+variance_upper)/2)
        lower = np.divide(gap, denom, out=np.zeros_like(gap), where=denom>0)
        for j, col in enumerate(cols):
            bounds.append({'pool': name, 'feature': col, 'target_mean_log1p': x[ti,j].mean(),
                           'min_mean_log1p': low[j], 'max_mean_log1p': high[j],
                           'conservative_smd_lower_bound': lower[j]})
    pd.DataFrame(bounds).to_csv(OUT/'attainable_bounds.csv', index=False)
    rows = []; best = {'maximum_smd': float('inf')}
    def observe(attempt, indices, balance):
        rows.append([attempt, *balance])
        score = float(np.max(balance))
        if score < best['maximum_smd']:
            best.update(maximum_smd=score, attempt=int(attempt),
                        root_ids=f.iloc[indices].root_id.tolist(),
                        smd=dict(zip(cols, map(float,balance))))
    sampler, source = instrumented_sampler(observe)
    (OUT/'instrumented_matched_sets.py').write_text(source, encoding='utf-8')
    accepted, result = sampler(f, ids, sugar_ids(), n_sets=5, seed=630600, full=True, max_attempts=50000)
    assert result['accepted'] == old['accepted'] and result['attempts'] == old['attempts']
    frame = pd.DataFrame(rows, columns=['attempt', *cols])
    frame.to_parquet(OUT/'proposal_smd.parquet', index=False)
    feature_rows = []
    a = frame[cols].to_numpy()
    for j, col in enumerate(cols):
        feature_rows.append({'feature': col, 'failed_proposals': int((a[:,j]>.1).sum()),
                             'sole_failure_proposals': int(((a[:,j]>.1)&((a>.1).sum(1)==1)).sum()),
                             'min_smd': float(a[:,j].min()), 'median_smd': float(np.median(a[:,j])),
                             'p95_smd': float(np.quantile(a[:,j],.95))})
    pd.DataFrame(feature_rows).to_csv(OUT/'failure_summary.csv', index=False)
    atomic_json(OUT/'best_rejected.json', best)
    atomic_json(OUT/'summary.json', {'completed_utc':now(), 'elapsed_seconds':time.monotonic()-start,
        'target_size':len(ti), 'strata':capacity, 'replay':result, 'evaluated_proposals':len(rows),
        'failure_summary':feature_rows, 'best_maximum_smd':best['maximum_smd'],
        'interpretation':'Descriptive baseline-only audit; best rejected set is not an accepted control.',
        'outputs':{p.name:sha256(p) for p in OUT.iterdir() if p.is_file()}})
    print(json.dumps({'out':str(OUT),'best':best['maximum_smd'],'failures':feature_rows}))


if __name__ == '__main__':
    main()
