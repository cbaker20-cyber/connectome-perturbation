"""Exhaust a small fractional support; retain every valid binary witness."""
import itertools
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from eigencircuits.common import atomic_json, now, sha256
from eigencircuits.controls import FULL_FEATURES, standardized_difference
from scripts.pcdr_fullpool_relaxation import OUT, load_design, validate_fractional


def completions(weights, groups, counts, maximum_fractional=12):
    weights = np.asarray(weights)
    if not np.isfinite(weights).all() or np.any(weights < -1e-7) or np.any(weights > 1+1e-7):
        raise ValueError('Invalid weights')
    fractional = np.flatnonzero((weights > 1e-7) & (weights < 1-1e-7))
    if len(fractional) > maximum_fractional:
        raise ValueError('Enumeration budget exceeded')
    fixed = np.flatnonzero(weights >= 1-1e-7)
    for bits in itertools.product([0, 1], repeat=len(fractional)):
        chosen = np.r_[fixed, fractional[np.array(bits, bool)]]
        if all(sum(groups[i] == key for i in chosen) == count for key, count in counts.items()):
            yield chosen


def main():
    dest = OUT/'binary_completion'
    dest.mkdir(exist_ok=False)
    source = OUT/'conservative/fractional_weights.parquet'
    paths = [source, OUT/'protocol.json', OUT/'conservative/result.json', Path(__file__),
             ROOT/'scripts/pcdr_fullpool_relaxation.py']
    atomic_json(dest/'protocol.json', {
        'recorded_utc': now(),
        'reason': 'Both LPs returned feasible; conservative solution has seven fractional memberships. Separately declared small enumeration following that baseline-only result.',
        'procedure': 'Use conservative LP only. Fix weights within 1e-7 of 0/1 to those endpoints. Enumerate ALL binary assignments of remaining variables, at most 12 (4096 assignments). No search if cap exceeded. Keep exact stratum counts, exclusions and size; compute original pooled population-variance SMD <=0.1 on all six log1p features. Also report stricter sufficient constraints separately. Retain all valid sets.',
        'scope': 'Baseline-only existence witnesses. No rounding is accepted without full validation. No random sampling, p-values, lesions or automatic larger optimization. Failure says nothing about other binary solutions.',
        'hashes': {str(p.relative_to(ROOT)): sha256(p) for p in paths}})
    original = json.loads((OUT/'protocol.json').read_text())
    for rel, digest in original['hashes'].items():
        assert sha256(ROOT/rel) == digest, rel
    f, values, ti, pool, groups, counts, scale, tolerances = load_design()
    frame = pd.read_parquet(source)
    assert frame.root_id.astype(str).tolist() == f.iloc[pool].root_id.tolist()
    weights = frame.fractional_weight.to_numpy()
    pool_groups = [groups[i] for i in pool]
    validation = validate_fractional(weights, values[pool], pool_groups, counts,
                                    values[ti].mean(0), tolerances['conservative'], scale)
    rows, members = [], []
    for attempt, indices in enumerate(completions(weights, pool_groups, counts)):
        selected = pool[indices]
        assert len(selected) == len(ti) == len(set(selected))
        balance = standardized_difference(values[ti], values[selected])
        sufficient = bool(np.all(abs(values[selected].mean(0)-values[ti].mean(0)) <= tolerances['conservative']+1e-12))
        valid = bool(np.all(balance <= .1))
        rows.append({'assignment': attempt, 'accepted_original_smd': valid,
                     'sufficient_constraints_pass': sufficient,
                     'maximum_smd': float(balance.max()),
                     **dict(zip(FULL_FEATURES, map(float, balance)))})
        if valid:
            members.extend({'assignment': attempt, 'root_id': rid} for rid in f.iloc[selected].root_id)
    pd.DataFrame(rows).to_csv(dest/'assignments.csv', index=False)
    pd.DataFrame(members, columns=['assignment', 'root_id']).to_parquet(dest/'members.parquet', index=False)
    atomic_json(dest/'summary.json', {'completed_utc': now(), 'fractional_validation': validation,
                'binary_assignments_total': 2**validation['fractional_count'],
                'exact_stratum_assignments': len(rows),
                'original_smd_witness_count': sum(row['accepted_original_smd'] for row in rows),
                'sufficient_witness_count': sum(row['sufficient_constraints_pass'] for row in rows),
                'interpretation': 'Existence witnesses only; overlapping optimized sets are not a random reference ensemble.',
                'outputs': {p.name: sha256(p) for p in dest.iterdir() if p.is_file()}})
    print((dest/'summary.json').read_text())


if __name__ == '__main__':
    main()
