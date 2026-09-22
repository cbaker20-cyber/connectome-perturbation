"""Baseline-only LP diagnostics; fractional memberships are never lesion sets."""
import os
for name in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS']:
    os.environ[name] = '1'
from collections import Counter
import json
from pathlib import Path
import sys
import time
import warnings

import numpy as np
import pandas as pd
import scipy
from scipy.optimize import linprog
from scipy.sparse import csc_matrix, vstack

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from eigencircuits.common import atomic_json, now, sha256, sugar_ids
from eigencircuits.controls import FULL_FEATURES
from scripts.pcdr_matching_audit import FEATURES, SELECTION
from scripts.pcdr_fullpool_bounds import smd_lower_bounds
from scripts.pcdr_bounded_process import run_bounded

OUT = ROOT/'results/pcdr/fullpool_relaxation_20260922'


def solve_relaxation(values, groups, counts, mean, tolerance, scale, seconds=60):
    """Keep exact stratum mass but allow each membership to range from 0 to 1."""
    n = sum(counts.values())
    keys = sorted(counts)
    eq = csc_matrix(np.array([[g == key for g in groups] for key in keys], float))
    features = csc_matrix(values.T/n/scale[:, None])
    upper = np.r_[(mean+tolerance)/scale, -(mean-tolerance)/scale]
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter('always')
        result = linprog(np.zeros(len(values)), A_ub=vstack([features, -features]),
                         b_ub=upper, A_eq=eq, b_eq=[counts[k] for k in keys],
                         bounds=(0, 1), method='highs',
                         options={'time_limit': seconds, 'threads': 1})
    return result, [str(w.message) for w in captured]


def validate_fractional(weights, values, groups, counts, mean, tolerance, scale):
    weights = np.asarray(weights)
    if weights.shape != (len(values),) or not np.isfinite(weights).all():
        raise ValueError('Invalid fractional vector')
    mass_error = max(abs(sum(weights[i] for i, g in enumerate(groups) if g == key)-count)
                     for key, count in counts.items())
    selected_mean = weights @ values / sum(counts.values())
    feature_violation = np.maximum(abs(selected_mean-mean)-tolerance, 0)/scale
    bound_error = max(0., float(-weights.min()), float(weights.max()-1))
    if max(mass_error, bound_error, float(feature_violation.max())) > 1e-6:
        raise ValueError('Fractional solution fails independent primal check')
    return {'stratum_mass_error': float(mass_error), 'bound_error': bound_error,
            'maximum_scaled_feature_violation': float(feature_violation.max()),
            'fractional_count': int(np.count_nonzero((weights > 1e-7) & (weights < 1-1e-7))),
            'weighted_means': selected_mean.tolist()}


def load_design():
    f = pd.read_parquet(FEATURES)
    f.root_id = f.root_id.astype(str)
    ids = json.loads(SELECTION.read_text())['root_ids']
    frozen = json.loads((ROOT/'results/pcdr/exploratory80_20260921/controls/manifest.json').read_text())
    assert sha256(FEATURES) == frozen['features_sha256']
    assert sha256(SELECTION) == frozen['selection_sha256']
    assert f.root_id.is_unique and len(ids) == len(set(ids)) == 51
    ti = np.flatnonzero(f.root_id.isin(ids))
    assert len(ti) == len(ids)
    raw = f[FULL_FEATURES].to_numpy(float)
    assert np.isfinite(raw).all() and (raw >= 0).all()
    values = np.log1p(raw)
    groups = list(zip(f.model_sign.astype(str), f.recruited.astype(bool), f.super_class.eq('motor')))
    counts = Counter(groups[i] for i in ti)
    eligible = np.flatnonzero(~f.root_id.isin(set(ids) | set(sugar_ids())))
    pools = {k: np.array([i for i in eligible if groups[i] == k]) for k in counts}
    assert all(len(pools[k]) >= count for k, count in counts.items())
    pool = np.sort(np.concatenate(list(pools.values())))
    scale = values.std(0)
    scale[scale == 0] = 1.
    _, _, variance_bound, _ = smd_lower_bounds(values[ti], values, counts, pools)
    tolerances = {'conservative': .099*np.sqrt(values[ti].var(0)/2),
                  'necessary_outer': .1*np.sqrt((values[ti].var(0)+variance_bound)/2)}
    return f, values, ti, pool, groups, counts, scale, tolerances


def worker(kind):
    dest = OUT/kind
    protocol = json.loads((OUT/'protocol.json').read_text())
    for rel, digest in protocol['hashes'].items():
        assert sha256(ROOT/rel) == digest, rel
    f, values, ti, pool, groups, counts, scale, tolerances = load_design()
    pool_groups = [groups[i] for i in pool]
    start = time.monotonic()
    result, captured = solve_relaxation(values[pool], pool_groups, counts,
                                        values[ti].mean(0), tolerances[kind], scale)
    record = {'kind': kind, 'status': int(result.status), 'message': result.message,
              'solver_seconds': time.monotonic()-start, 'pool_count': len(pool),
              'warnings': captured, 'scipy': scipy.__version__, 'python': sys.version,
              'actual_control_sets_accepted': 0, 'fractional_validation': None}
    if result.x is not None:
        record['fractional_validation'] = validate_fractional(
            result.x, values[pool], pool_groups, counts, values[ti].mean(0), tolerances[kind], scale)
        pd.DataFrame({'root_id': f.iloc[pool].root_id.to_numpy(),
                      'fractional_weight': result.x}).to_parquet(dest/'fractional_weights.parquet', index=False)
    atomic_json(dest/'result.json', record)
    print(json.dumps(record))


def main():
    OUT.mkdir(exist_ok=False)
    paths = [FEATURES, SELECTION, Path(__file__), ROOT/'scripts/pcdr_bounded_process.py',
             ROOT/'scripts/pcdr_fullpool_bounds.py', ROOT/'scripts/pcdr_matching_audit.py',
             ROOT/'eigencircuits/common.py', ROOT/'eigencircuits/controls.py']
    atomic_json(OUT/'protocol.json', {
        'recorded_utc': now(), 'purpose': 'Joint baseline-only feasibility diagnosis following stopped full-pool MILP.',
        'fixed': '51-cell target, full eligible pool, exact model-sign/recruitment/annotated-motor mass; six log1p features; exclude targets and sugar inputs.',
        'conservative': 'Relax binary memberships to [0,1]; same sufficient mean tolerances 0.099 sqrt(target population variance/2). Infeasibility rules out this sufficient program only.',
        'necessary_outer': 'Relax binary memberships to [0,1]; abs(mean difference) <= 0.1 sqrt((target variance+Vmax)/2), using the existing nonnegative-feature order-statistic upper variance bound. Every original-SMD-valid binary set is included. Numerical infeasibility would rule those sets out, subject to solver accuracy; fractional feasibility leaves binary feasibility unresolved.',
        'objective': 'Zero; feasibility only. No rounding or automatic integer solve.',
        'budget': 'Exactly two serial LPs, each 60-second internal solver limit and 90-second external worker deadline, including startup/loading. Cleanup may take up to 30 additional seconds. No simulation.',
        'interpretation': 'Fractional weights are diagnostics, never neuronal control sets or a reference distribution. No p-values. No acceptance threshold is relaxed.',
        'references': ['https://arxiv.org/abs/1404.3584', 'https://docs.scipy.org/doc/scipy/reference/optimize.linprog-highs.html'],
        'command': [sys.executable, str(Path(__file__).resolve())],
        'hashes': {str(p.relative_to(ROOT)): sha256(p) for p in paths}})
    records = {}
    for kind in ['conservative', 'necessary_outer']:
        dest = OUT/kind
        records[kind] = run_bounded([sys.executable, str(Path(__file__).resolve()), '--worker', kind],
                                    dest, 90, cwd=ROOT)
        atomic_json(dest/'process.json', records[kind])
    atomic_json(OUT/'execution.json', {'completed_utc': now(), 'workers': records,
                                     'no_simulations': True, 'accepted_control_sets': 0})
    print(json.dumps(records))


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--worker':
        if sys.argv[2] not in ['conservative', 'necessary_outer']:
            raise ValueError('Unknown formulation')
        worker(sys.argv[2])
    else:
        main()
