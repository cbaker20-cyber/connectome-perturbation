"""Verify saved binary witnesses directly from original features and frozen IDs."""
from collections import Counter
import itertools
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from eigencircuits.common import atomic_json, now, sha256, sugar_ids
from eigencircuits.controls import FULL_FEATURES


def main():
    out = ROOT/'results/pcdr/fullpool_relaxation_20260922'
    dest = out/'binary_completion'
    for protocol_path in [out/'protocol.json', dest/'protocol.json']:
        for rel, digest in json.loads(protocol_path.read_text())['hashes'].items():
            assert sha256(ROOT/rel) == digest, rel
    summary = json.loads((dest/'summary.json').read_text())
    for name, digest in summary['outputs'].items():
        assert sha256(dest/name) == digest, name
    f = pd.read_parquet(ROOT/'results/pcdr/corrected_20260919/analysis/features.parquet')
    f.root_id = f.root_id.astype(str)
    f = f.set_index('root_id')
    assert f.index.is_unique
    ids = json.loads((ROOT/'results/pcdr/exploratory80_20260921/modes/selection.json').read_text())['root_ids']
    target = f.loc[ids]
    excluded = set(ids) | set(sugar_ids())
    def strata(frame):
        return Counter(zip(frame.model_sign.astype(str), frame.recruited.astype(bool), frame.super_class.eq('motor')))
    target_counts = strata(target)
    t = np.log1p(target[FULL_FEATURES].to_numpy(float))
    assignments = pd.read_csv(dest/'assignments.csv').set_index('assignment')
    members = pd.read_parquet(dest/'members.parquet')
    details, sets = [], []
    for assignment, frame in members.groupby('assignment'):
        chosen = frame.root_id.astype(str).tolist()
        assert len(chosen) == len(set(chosen)) == len(ids) == 51
        assert not set(chosen) & excluded
        selected = f.loc[chosen]
        assert strata(selected) == target_counts
        x = np.log1p(selected[FULL_FEATURES].to_numpy(float))
        diff = abs(x.mean(0)-t.mean(0))
        denom = np.sqrt((x.var(0)+t.var(0))/2)
        smd = np.divide(diff, denom, out=np.where(diff == 0, 0., np.inf), where=denom > 0)
        assert np.all(smd <= .1)
        np.testing.assert_allclose(smd, assignments.loc[assignment, FULL_FEATURES].to_numpy(float), atol=1e-12)
        assert assignments.loc[assignment, 'accepted_original_smd']
        details.append({'assignment': int(assignment), 'size': len(chosen),
                        'motor_count': int(selected.super_class.eq('motor').sum()),
                        'maximum_smd': float(smd.max()), 'smd': dict(zip(FULL_FEATURES, smd.tolist()))})
        sets.append(set(chosen))
    assert len(sets) == summary['original_smd_witness_count'] == int(assignments.accepted_original_smd.sum())
    assert len({frozenset(s) for s in sets}) == len(sets)
    shared = [len(a & b) for a, b in itertools.combinations(sets, 2)]
    record = {'verified_utc': now(), 'verified_witnesses': details,
              'pairwise_shared_cells_min': min(shared) if shared else None,
              'pairwise_shared_cells_max': max(shared) if shared else None,
              'all_set_intersection': len(set.intersection(*sets)) if sets else None,
              'claim': 'Original six-feature pooled-SMD matching with exact annotated motor/sign/recruitment counts is feasible for this target. These witnesses do not establish sampling validity or lesion effects.',
              'command': [sys.executable, str(Path(__file__))], 'verifier_sha256': sha256(Path(__file__)),
              'evidence_hashes': {str(p.relative_to(out)): sha256(p) for p in out.rglob('*') if p.is_file() and p.name != 'verification.json'}}
    atomic_json(dest/'verification.json', record)
    print(json.dumps(record))


if __name__ == '__main__':
    main()
