"""Bounded partner searches conditional on two previously verified anchors."""
from collections import Counter
from pathlib import Path
import argparse
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.pcdr_ccr_transfer import read, write, digest, utc
from scripts.pcdr_bounded_process import run_bounded
from scripts.pcdr_matching_audit import FEATURES, SELECTION
from scripts.pcdr_verify_distribution_match import audit_members
from scripts.pcdr_verify_joint_family import classify


def anchor_references(pool, references, anchor, size=51, cap=30):
    if len(pool) != len(set(pool)) or any(type(v) is not str for v in pool):
        raise ValueError('Invalid exact pool IDs')
    if len(anchor) != size or len(set(anchor)) != size or any(type(v) is not str for v in anchor):
        raise ValueError('Invalid anchor IDs')
    if not set(anchor) <= set(pool): raise ValueError('Anchor outside pool')
    if 'fixed_anchor' in references: raise ValueError('Anchor key collision')
    for ids in references.values():
        if len(ids) != size or len(set(ids)) != size or not set(ids) <= set(pool):
            raise ValueError('Invalid old reference')
        if len(set(anchor) & set(ids)) > cap:
            raise ValueError('Anchor fails old-reference cap')
    return {**references, 'fixed_anchor':list(anchor)}


def check_case(case, frame, target, counts):
    p, process = read(case/'protocol.json'), read(case/'cap_30/process.json')
    for path, h in p['inputs'].items():
        if digest(path) != h: raise ValueError('Changed frozen input: '+path)
    if process['timed_out'] or process['returncode'] != 0:
        return dict(status='external_worker_failure', process=process)
    r = read(case/'cap_30/result.json')
    exists = (case/'cap_30/candidate.json').exists()
    if exists != r['candidate_verified']: raise ValueError('Candidate inventory mismatch')
    status = classify(r['status'], exists, r['objective'], r['dual_bound'])
    audit = None
    anchor = p['references']['fixed_anchor']
    refs = {k:v for k,v in p['references'].items() if k != 'fixed_anchor'}
    anchor_audit = audit_members(anchor, frame, target, counts, refs, 30)
    record = dict(status=status, anchor_audit=anchor_audit, companion_audit=audit,
                  worker_seconds=process['elapsed_seconds'], conditional_only=True)
    if exists:
        ids = read(case/'cap_30/candidate.json')['root_ids']
        if not set(ids) <= set(p['candidate_ids']): raise ValueError('Companion outside pool')
        audit = audit_members(ids, frame, target, counts, p['references'], 30)
        if audit['maximum_ecdf_gap'] > r['objective']+1e-7: raise ValueError('Understated objective')
        if r['status'] == 0 and abs(audit['maximum_ecdf_gap']-r['objective']) > 1e-7:
            raise ValueError('Optimal objective mismatch')
        record.update(companion_audit=audit, pairwise_overlap=audit['overlaps']['fixed_anchor'],
                      pair_maximum_cdf_gap=max(anchor_audit['maximum_ecdf_gap'],audit['maximum_ecdf_gap']))
    return record


def run(out):
    base = ROOT/'results/pcdr'
    expanded = base/'distribution_expand_20261008'
    original = base/'distribution_match_20261008'
    p = read(expanded/'protocol.json')
    inputs = dict(p['inputs'])
    for study in [original, expanded]:
        v = read(study/'verification.json')
        if v['status'] != 'verified': raise ValueError('Unverified prior study')
        for path, h in {**read(study/'protocol.json')['inputs'], **v['inputs']}.items():
            if digest(path) != h: raise ValueError('Changed prior evidence: '+path)
        for name in ['protocol.json', 'verification.json', 'cap_30/candidate.json']:
            inputs[str(study/name)] = digest(study/name)
    for path in [Path(__file__), ROOT/'scripts/pcdr_verify_distribution_match.py', ROOT/'scripts/pcdr_verify_joint_family.py']:
        inputs[str(path)] = digest(path)
    frame = pd.read_parquet(FEATURES)
    if not frame.root_id.is_unique or not frame.root_id.map(lambda v:type(v) is str).all():
        raise ValueError('Invalid feature IDs')
    frame = frame.set_index('root_id')
    target = read(SELECTION)['root_ids']; t = frame.loc[target]
    counts = Counter(zip(t.model_sign.astype(str),t.recruited.astype(bool),t.super_class.eq('motor')))
    cases = {}
    for name, study in [('anchor_538',original),('anchor_999',expanded)]:
        anchor = read(study/'cap_30/candidate.json')['root_ids']
        refs = anchor_references(p['candidate_ids'],p['references'],anchor)
        audit_members(anchor,frame,target,counts,p['references'],30)
        cases[name] = refs
    out.mkdir(parents=True, exist_ok=False)
    write(out/'protocol.json',dict(recorded_utc=utc(),inputs=inputs,cases=cases,
        question='Find partners for both existing verified old-reference-capped anchors while keeping the joint scientific constraints.',
        selection='Use both old-reference-capped distribution solutions; no anchor selected by a new outcome. Exclude uncapped solutions because they fail old-reference caps.',
        budget='Two serial workers, each sixty seconds internal and one hundred seconds external; no retries, pool changes or simulation.',
        objective='Minimize companion maximum CDF gap. The pair gap is the maximum of this and the fixed anchor gap; optimal companion implies conditional pair optimality, not global joint optimality.',
        limitation='Fixing an anchor restricts the joint feasible space. Failure cannot rule out other pairs. Any feasible pair supplies only an upper bound on the joint optimum.'))
    # Freeze both case protocols before either search, including the extra mask.
    for name, refs in cases.items():
        case = out/name; (case/'cap_30').mkdir(parents=True)
        write(case/'protocol.json',dict(recorded_utc=utc(),inputs=inputs,candidate_ids=p['candidate_ids'],
            references=refs,neighbors_per_target=50,solves=['cap_30'],
            purpose='Conditional partner search in frozen 999-cell pool, adding the fixed anchor as a sixteenth capped reference.'))
    for name in cases:
        case = out/name
        process = run_bounded([sys.executable,str(ROOT/'scripts/pcdr_distribution_match.py'),
            '--out',str(case),'--worker','cap_30'],case/'cap_30/logs',100,cwd=ROOT)
        write(case/'cap_30/process.json',process)
        record = check_case(case,frame,target,counts)
        write(case/'verification.json',record)
        print(name,record['status'],flush=True)
    write(out/'summary.json',dict(cases={name:read(out/name/'verification.json') for name in cases},completed_utc=utc()))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    run(parser.parse_args().out)
