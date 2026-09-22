"""Describe remaining baseline differences in all nine verified motor-matched sets."""
from collections import Counter
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from eigencircuits.common import atomic_json, now, sha256, sugar_ids, MN9
from eigencircuits.controls import FULL_FEATURES, standardized_difference
from scripts.pcdr_composition_audit import ecdf_gap

OUT = ROOT/'results/pcdr/motor_set_audit_20260922'
FEATURES = ROOT/'results/pcdr/corrected_20260919/analysis/features.parquet'
SELECTION = ROOT/'results/pcdr/exploratory80_20260921/modes/selection.json'
COMPLETION = ROOT/'results/pcdr/fullpool_relaxation_20260922/binary_completion'


def main():
    OUT.mkdir(exist_ok=False)
    paths = [FEATURES, SELECTION, COMPLETION/'members.parquet', COMPLETION/'verification.json',
             Path(__file__), ROOT/'scripts/pcdr_composition_audit.py', ROOT/'eigencircuits/controls.py']
    atomic_json(OUT/'protocol.json', {
        'recorded_utc': now(), 'purpose': 'Baseline distribution and annotation audit before any new motor-balanced lesions.',
        'method': 'Include all nine verified sets. Six log1p features: original SMD, ECDF gap, population variance ratio, min/quartiles/max. Composition: super_class, cell_type, top_nt, known_nt, annotation_available, model_sign and recruited. Missing labels are unavailable. Show complete counts; categorical total variation is descriptive.',
        'fixed': 'No new cutoff, exclusion, set ranking for selection, significance test or rematching. All nine sets retained irrespective of audit differences.',
        'interpretation': 'Matching mean and exact motor counts does not ensure matching distributions, motor identities or detailed cell types. These sets remain optimized and overlap.',
        'command': [sys.executable, str(Path(__file__))],
        'hashes': {str(p.relative_to(ROOT)): sha256(p) for p in paths}})
    verification = json.loads((COMPLETION/'verification.json').read_text())
    source_root = COMPLETION.parent
    for rel, digest in verification['evidence_hashes'].items():
        assert sha256(source_root/rel) == digest, rel
    f = pd.read_parquet(FEATURES)
    f.root_id = f.root_id.astype(str)
    f = f.set_index('root_id')
    ids = json.loads(SELECTION.read_text())['root_ids']
    target = f.loc[ids]
    members = pd.read_parquet(COMPLETION/'members.parquet')
    sets = {'mode': ids, **{f'motor_{int(a):03}': g.root_id.astype(str).tolist()
                          for a, g in members.groupby('assignment')}}
    assert len(sets) == 10 and f.index.is_unique
    def strata(frame):
        return Counter(zip(frame.model_sign.astype(str), frame.recruited.astype(bool), frame.super_class.eq('motor')))
    rows, classes, metrics, membership = [], [], [], []
    for condition, selected in sets.items():
        sample = f.loc[selected]
        assert len(selected) == len(set(selected)) == 51
        assert strata(sample) == strata(target)
        if condition != 'mode':
            assert not set(selected) & (set(ids) | set(sugar_ids()))
        for col in FULL_FEATURES:
            a, b = (np.log1p(frame[col].to_numpy(float)) for frame in [target, sample])
            smd = float(standardized_difference(a[:, None], b[:, None])[0])
            assert smd <= .1
            rows.append({'condition': condition, 'feature': col, 'smd': smd,
                         'ecdf_gap': ecdf_gap(a, b), 'variance_ratio': float(b.var()/a.var()) if a.var() else None,
                         **{f'target_q{q}': float(np.quantile(a, q/100)) for q in [0, 25, 50, 75, 100]},
                         **{f'sample_q{q}': float(np.quantile(b, q/100)) for q in [0, 25, 50, 75, 100]}})
        for label in ['super_class', 'cell_type', 'top_nt', 'known_nt', 'annotation_available', 'model_sign', 'recruited']:
            a = target[label].fillna('unavailable').astype(str).value_counts()
            b = sample[label].fillna('unavailable').astype(str).value_counts()
            values = sorted(set(a.index) | set(b.index))
            tv = .5*sum(abs(a.get(v, 0)/51-b.get(v, 0)/51) for v in values)
            metrics.append({'condition': condition, 'field': label, 'total_variation': float(tv)})
            classes.extend({'condition': condition, 'field': label, 'value': value,
                            'target_count': int(a.get(value, 0)), 'sample_count': int(b.get(value, 0))} for value in values)
        for rid, row in sample.iterrows():
            membership.append({'condition': condition, 'root_id': rid,
                               **row[['super_class', 'cell_type', 'known_nt', 'model_sign', 'recruited', 'baseline_hz', 'annotation_available']].to_dict()})
    pd.DataFrame(rows).to_csv(OUT/'distributions.csv', index=False)
    pd.DataFrame(classes).to_csv(OUT/'composition.csv', index=False)
    pd.DataFrame(metrics).to_csv(OUT/'composition_distances.csv', index=False)
    pd.DataFrame(membership).to_csv(OUT/'annotated_members.csv', index=False)
    comparisons = [r for r in rows if r['condition'] != 'mode']
    summary = {'completed_utc': now(), 'sets': 9, 'largest_ecdf_gap': max(comparisons, key=lambda r: r['ecdf_gap']),
               'variance_ratio_min': min(r['variance_ratio'] for r in comparisons if r['variance_ratio'] is not None),
               'variance_ratio_max': max(r['variance_ratio'] for r in comparisons if r['variance_ratio'] is not None),
               'class_distances': [r for r in metrics if r['condition'] != 'mode' and r['field'] in ['super_class', 'known_nt', 'cell_type']],
               'mn9_in_mode': MN9 in ids, 'mn9_in_any_comparison': any(MN9 in s for name, s in sets.items() if name != 'mode'),
               'all_set_intersection': verification['all_set_intersection'],
               'pairwise_shared_range': [verification['pairwise_shared_cells_min'], verification['pairwise_shared_cells_max']],
               'selection_changed': False,
               'outputs': {p.name: sha256(p) for p in OUT.iterdir() if p.is_file()}}
    atomic_json(OUT/'summary.json', summary)
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
