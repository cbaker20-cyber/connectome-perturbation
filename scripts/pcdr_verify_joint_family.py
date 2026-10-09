"""Audit a bounded joint-family attempt without treating a timeout as infeasibility."""
from collections import Counter
from pathlib import Path
import argparse
import sys
import math
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.pcdr_ccr_transfer import read, write, digest, utc
from scripts.pcdr_matching_audit import FEATURES, SELECTION
from scripts.pcdr_verify_distribution_match import audit_members


def classify(status, candidate, objective, bound):
    if status not in [0, 1, 2, 3, 4]:
        raise ValueError('Unknown solver status')
    if any(v is not None and not math.isfinite(v) for v in [objective, bound]):
        raise ValueError('Nonfinite objective record')
    if candidate:
        if status not in [0, 1] or objective is None or not 0 <= objective <= 1+1e-7:
            raise ValueError('Inconsistent incumbent status')
        if bound is not None and bound > objective+1e-7:
            raise ValueError('Dual bound exceeds objective')
        if status == 0 and (bound is None or abs(objective-bound) > 1e-7):
            raise ValueError('Optimality bounds do not agree')
        return 'verified_optimal_pair' if status == 0 else 'verified_feasible_pair_optimality_unresolved'
    if status == 0 or objective is not None:
        raise ValueError('Missing reported solution')
    return {1:'time_limit_without_incumbent', 2:'solver_reported_restricted_infeasibility',
            3:'solver_reported_unbounded', 4:'solver_failure'}[status]


def verify(study, out):
    if out.exists(): raise FileExistsError(out)
    p, process = read(study/'protocol.json'), read(study/'process.json')
    for path, h in p['inputs'].items():
        if digest(path) != h: raise ValueError('Changed frozen input: '+path)
    if p['family_size'] != 2 or p['cap'] != 30 or len(p['candidate_ids']) != 999:
        raise ValueError('Unexpected joint design')
    if process['timed_out'] or process['returncode'] != 0:
        raise ValueError('Worker incomplete; preserve logs and review external interruption')
    r = read(study/'result.json')
    exists = (study/'candidate.json').exists()
    if exists != r['candidate_verified']: raise ValueError('Inconsistent candidate inventory')
    status = classify(r['solver_status'], exists, r['objective'], r['dual_bound'])
    audits, overlap = [], None
    if exists:
        f = pd.read_parquet(FEATURES)
        if not f.root_id.is_unique or not f.root_id.map(lambda v:type(v) is str).all():
            raise ValueError('Invalid exact feature IDs')
        f = f.set_index('root_id')
        target = read(SELECTION)['root_ids']
        t = f.loc[target]
        counts = Counter(zip(t.model_sign.astype(str), t.recruited.astype(bool), t.super_class.eq('motor')))
        members = read(study/'candidate.json')['root_ids']
        if len(members) != 2: raise ValueError('Wrong family size')
        for ids in members:
            if not set(ids) <= set(p['candidate_ids']): raise ValueError('Member outside frozen pool')
            audits.append(audit_members(ids, f, target, counts, p['references'], p['cap']))
        overlap = len(set(members[0]) & set(members[1]))
        if overlap > p['cap']: raise ValueError('Pairwise overlap failed')
        gap = max(a['maximum_ecdf_gap'] for a in audits)
        if gap > r['objective']+1e-7: raise ValueError('Objective understates CDF gap')
        if r['solver_status'] == 0 and abs(gap-r['objective']) > 1e-7:
            raise ValueError('Optimal objective differs from measured gap')
    paths = [study/n for n in ['protocol.json', 'process.json', 'result.json']]
    if exists: paths.append(study/'candidate.json')
    write(out, dict(status=status, audits=audits, pairwise_overlap=overlap,
        checked_utc=utc(), inputs={str(path):digest(path) for path in paths},
        checker_sha256=digest(__file__),
        limitation='Algorithmically separate audit, with Codex assistance. No new lesion evidence; restricted design only.'))
    print(status)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--study', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    verify(args.study, args.out)
