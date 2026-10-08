"""Bounded binary distribution matching on a declared baseline-only candidate pool."""
import os
for name in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS']:
    os.environ[name] = '1'
import argparse
from collections import Counter
from pathlib import Path
import sys

import numpy as np
import pandas as pd
from scipy.optimize import milp, Bounds, LinearConstraint
from scipy.sparse import csc_matrix

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.pcdr_fullpool_relaxation import load_design, FEATURES, SELECTION
from scripts.pcdr_verify_diverse import distribution_check
from scripts.pcdr_ccr_transfer import read, write, digest
from scripts.pcdr_bounded_process import run_bounded
from eigencircuits.common import environment, now


def solve(values, groups, counts, target, scale, references, cap, seconds=60):
    values, target = np.asarray(values, float), np.asarray(target, float)
    if values.ndim != 2 or target.ndim != 2 or values.shape[1] != target.shape[1]:
        raise ValueError('Invalid feature shapes')
    if not len(values) or not len(target) or not np.isfinite(values).all() or not np.isfinite(target).all():
        raise ValueError('Empty or nonfinite features')
    n, m = len(target), len(values)
    if len(groups) != m or sum(counts.values()) != n or np.any(np.asarray(scale) <= 0):
        raise ValueError('Invalid design')
    rows, lower, upper = [], [], []
    for key, count in sorted(counts.items()):
        rows.append([float(g == key) for g in groups]+[0.])
        lower.append(count); upper.append(count)
    tolerance = .099*np.sqrt(target.var(axis=0)/2)
    for j in range(values.shape[1]):
        rows.append(np.r_[values[:, j]/n/scale[j], 0.])
        lower.append((target[:, j].mean()-tolerance[j])/scale[j])
        upper.append((target[:, j].mean()+tolerance[j])/scale[j])
        # Both empirical CDFs are constant between their combined observed values.
        for point in np.unique(np.r_[values[:, j], target[:, j]]):
            cdf = (target[:, j] <= point).mean()
            row = (values[:, j] <= point).astype(float)/n
            rows.extend([np.r_[row, -1.], np.r_[-row, -1.]])
            lower.extend([-np.inf, -np.inf]); upper.extend([cdf, -cdf])
    if cap is not None:
        if not 0 <= cap <= n: raise ValueError('Invalid overlap cap')
        for reference in references:
            if len(reference) != m: raise ValueError('Invalid reference mask')
            rows.append(np.r_[reference, 0.]); lower.append(-np.inf); upper.append(cap)
    matrix = csc_matrix(np.asarray(rows))
    result = milp(np.r_[np.zeros(m), 1.], integrality=np.r_[np.ones(m), 0],
        bounds=Bounds(np.zeros(m+1), np.ones(m+1)),
        constraints=LinearConstraint(matrix, lower, upper),
        options={'time_limit':seconds, 'mip_rel_gap':0.})
    return result, dict(variables=m+1, constraints=len(rows), matrix_nonzeros=matrix.nnz)


def validate(weights, values, groups, counts, target, references, cap):
    weights = np.asarray(weights)
    if weights.shape != (len(values)+1,) or not np.isfinite(weights).all():
        raise ValueError('Invalid solution')
    x = weights[:-1]
    if np.max(np.abs(x-np.rint(x))) > 1e-6 or np.any(x < -1e-7) or np.any(x > 1+1e-7):
        raise ValueError('Nonbinary candidate')
    selected = np.flatnonzero(x > .5)
    if Counter(groups[i] for i in selected) != Counter(counts): raise ValueError('Wrong strata')
    chosen = values[selected]
    if np.any(np.abs(chosen.mean(axis=0)-target.mean(axis=0)) > .099*np.sqrt(target.var(axis=0)/2)+1e-10):
        raise ValueError('Conservative mean constraint failed')
    smd, ratios, gaps = distribution_check(target, chosen)
    if np.any(smd > .1): raise ValueError('Original SMD failed')
    overlaps = [int(np.asarray(r)[selected].sum()) for r in references]
    if cap is not None and any(v > cap for v in overlaps): raise ValueError('Overlap constraint failed')
    if not 0 <= weights[-1] <= 1+1e-7 or max(gaps) > weights[-1]+1e-7:
        raise ValueError('CDF objective understates observed gap')
    return selected, dict(smd=smd.tolist(), variance_ratios=ratios, ecdf_gaps=gaps,
                         maximum_ecdf_gap=max(gaps), overlaps=overlaps)


def worker(out, kind):
    protocol = read(out/'protocol.json')
    for path, h in protocol['inputs'].items():
        if digest(path) != h: raise ValueError('Changed search input: '+path)
    f, values, ti, _, groups, counts, scale, _ = load_design()
    lookup = {v:i for i,v in enumerate(f.root_id)}
    pool = np.array([lookup[v] for v in protocol['candidate_ids']])
    pg = [groups[i] for i in pool]
    references = [np.isin(protocol['candidate_ids'], r).astype(float) for r in protocol['references'].values()]
    cap = None if kind == 'unconstrained_overlap' else 30
    result, dimensions = solve(values[pool], pg, counts, values[ti], scale, references, cap)
    dest = out/kind
    record = dict(status=int(result.status), success=bool(result.success), message=result.message,
        objective=None if result.fun is None else float(result.fun), dimensions=dimensions,
        dual_bound=None if getattr(result, 'mip_dual_bound', None) is None else float(result.mip_dual_bound),
        mip_gap=None if getattr(result, 'mip_gap', None) is None else float(result.mip_gap),
        environment=environment(), completed_utc=now(), candidate_verified=False)
    # A time-limited integer incumbent may be valid without being optimal.
    if result.x is not None:
        np.save(dest/'solution.npy', result.x)
        selected, audit = validate(result.x, values[pool], pg, counts, values[ti], references, cap)
        write(dest/'candidate.json', dict(root_ids=[protocol['candidate_ids'][i] for i in selected], audit=audit))
        record['candidate_verified'] = True
    write(dest/'result.json', record)
    print(record)


def run(out):
    study = ROOT/'results/pcdr/diverse_comparisons_20261008'
    verification = read(study/'verification.json')
    for path, h in verification['input_hashes'].items():
        if digest(path) != h: raise ValueError('Changed verified input')
    previous = read(study/'complete.json')
    if digest(study/'members.csv') != previous['outputs']['members.csv']: raise ValueError('Changed memberships')
    plan_path = ROOT/'results/pcdr/fine_download_20261005/plan.json'
    if digest(plan_path) != read(ROOT/'results/pcdr/fine_verified_20261005/full_check.json')['plan_sha256']:
        raise ValueError('Changed fine plan')
    plan = read(plan_path)
    references = {}
    for j in plan['jobs']:
        if j['stage']=='fine' and j['variant']=='default' and j['condition'] in ['motor_003','motor_004','motor_005']:
            references[j['condition']] = j['lesion_ids']
    for key,g in pd.read_csv(study/'members.csv',dtype={'root_id':str}).groupby('assignment'):
        references['new_'+str(key)] = g.root_id.tolist()
    f, values, ti, eligible, groups, _, scale, _ = load_design()
    chosen = set(v for r in references.values() for v in r)
    # Per-target sorting is bounded by 51 scans and uses root IDs to break ties.
    for i in ti:
        pool = np.array([j for j in eligible if groups[j]==groups[i]])
        distance = np.sum(((values[pool]-values[i])/scale)**2, axis=1)
        order = np.lexsort((f.iloc[pool].root_id.to_numpy(), distance))
        chosen.update(f.iloc[pool[order[:20]]].root_id)
    candidate_ids = sorted(chosen)
    if not set(candidate_ids) <= set(f.iloc[eligible].root_id): raise ValueError('Ineligible candidate')
    out.mkdir(parents=True, exist_ok=False)
    paths = [FEATURES, SELECTION, plan_path, study/'members.csv', study/'verification.json', Path(__file__),
             ROOT/'scripts/pcdr_fullpool_relaxation.py',ROOT/'scripts/pcdr_verify_diverse.py',ROOT/'scripts/pcdr_bounded_process.py']
    write(out/'protocol.json',dict(recorded_utc=now(),
        purpose='Minimize maximum six-feature empirical CDF gap while retaining original sufficient mean and exact-count constraints.',
        pool_rule='Union of all 15 old/new comparison memberships and 20 nearest eligible cells per target in its exact stratum; squared distance in six log1p features divided by full-feature-table standard deviations; ties by exact root ID.',
        candidate_ids=candidate_ids, references=references,
        solves=['unconstrained_overlap','cap_30'],
        overlap_rule='Second solve shares at most 30/51 cells with each of the 15 references. Chosen as a design contrast requiring at least 21 changed members; not a biological standard.',
        budget='Two serial binary MILPs, each 60-second internal and 100-second external deadline. No retries or enlarged pool in this run.',
        limitations='Restricted pool. Failure does not establish full-pool infeasibility; conservative mean constraints are stricter than original pooled SMD. Optimize distributions without a retrospective acceptance cutoff. Optimized candidates are not random controls.',
        incumbent_rule='Independently check integer membership, exact counts, mean/SMD, overlap and CDF. A valid time-limited incumbent is feasible but not proven optimal.',
        inputs={str(p):digest(p) for p in paths}))
    for kind in ['unconstrained_overlap','cap_30']:
        dest=out/kind;dest.mkdir()
        process=run_bounded([sys.executable,str(Path(__file__).resolve()),'--out',str(out),'--worker',kind],dest/'logs',100,cwd=ROOT)
        write(dest/'process.json',process)
        print(kind,process,flush=True)
    write(out/'execution.json',dict(finished_utc=now(),workers={k:read(out/k/'process.json') for k in ['unconstrained_overlap','cap_30']}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--worker',choices=['unconstrained_overlap','cap_30'])
    args=parser.parse_args()
    if args.worker: worker(args.out,args.worker)
    else: run(args.out)
