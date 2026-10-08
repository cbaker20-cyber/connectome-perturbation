"""One bounded baseline-only search for comparisons with less shared membership."""
import os
for name in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS']:
    os.environ[name] = '1'
import argparse
from pathlib import Path
import sys
import warnings

import numpy as np
import pandas as pd
from scipy.optimize import linprog
from scipy.sparse import csc_matrix, vstack

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.pcdr_fullpool_relaxation import load_design, validate_fractional, FEATURES, SELECTION
from scripts.pcdr_fractional_completion import completions
from scripts.pcdr_ccr_transfer import read, write, digest
from scripts.pcdr_bounded_process import run_bounded
from eigencircuits.common import environment, now
from eigencircuits.controls import standardized_difference, FULL_FEATURES


def solve(values, groups, counts, mean, tolerance, scale, old_members):
    n = sum(counts.values())
    keys = sorted(counts)
    eq = csc_matrix(np.array([[g == k for g in groups] for k in keys], float))
    features = csc_matrix(values.T/n/scale[:, None])
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter('always')
        result = linprog(np.asarray(old_members, float), A_ub=vstack([features, -features]),
            b_ub=np.r_[(mean+tolerance)/scale, -(mean-tolerance)/scale],
            A_eq=eq, b_eq=[counts[k] for k in keys], bounds=(0, 1), method='highs',
            options={'time_limit':60, 'threads':1})
    return result, [str(w.message) for w in captured]


def worker(out):
    protocol = read(out/'protocol.json')
    for path, h in protocol['inputs'].items():
        if digest(path) != h: raise ValueError('Changed frozen search input: '+path)
    f, values, ti, pool, groups, counts, scale, tolerances = load_design()
    old = set(protocol['old_union'])
    selected_ids = f.iloc[pool].root_id.to_numpy()
    old_members = np.isin(selected_ids, list(old))
    pg = [groups[i] for i in pool]
    result, warning_messages = solve(values[pool], pg, counts, values[ti].mean(0),
                                     tolerances['conservative'], scale, old_members)
    write(out/'solver.json', dict(status=int(result.status), success=bool(result.success),
        message=result.message, objective=None if result.fun is None else float(result.fun), warnings=warning_messages))
    if not result.success: raise RuntimeError('LP did not finish successfully; preserved solver record')
    validation = validate_fractional(result.x, values[pool], pg, counts, values[ti].mean(0),
                                     tolerances['conservative'], scale)
    pd.DataFrame({'root_id':selected_ids,'weight':result.x}).to_parquet(out/'fractional_weights.parquet',index=False)
    rows, members = [], []
    for attempt, indices in enumerate(completions(result.x, pg, counts, maximum_fractional=12)):
        chosen = pool[indices]
        balance = standardized_difference(values[ti], values[chosen])
        accepted = bool((balance <= .1).all())
        rows.append(dict(assignment=attempt, accepted_original_smd=accepted, maximum_smd=float(balance.max()),
            old_union_overlap=int(old_members[indices].sum()),
            **dict(zip(FULL_FEATURES, map(float, balance)))))
        if accepted:
            members.extend(dict(assignment=attempt, root_id=str(v)) for v in f.iloc[chosen].root_id)
    pd.DataFrame(rows).to_csv(out/'assignments.csv',index=False)
    pd.DataFrame(members,columns=['assignment','root_id']).to_csv(out/'members.csv',index=False)
    write(out/'complete.json',dict(status='complete',finished_utc=now(),fractional_validation=validation,
        total_binary_assignments=2**validation['fractional_count'], exact_count_assignments=len(rows),
        accepted_count=sum(r['accepted_original_smd'] for r in rows),
        accepted_overlaps=[r['old_union_overlap'] for r in rows if r['accepted_original_smd']],
        environment=environment(), outputs={p.name:digest(p) for p in out.iterdir() if p.is_file()},
        limitation='Optimized existence witnesses, not random controls. Feature-distribution audit and independent verification precede any simulation.'))


def run(out, plan_path):
    check = read(ROOT/'results/pcdr/fine_verified_20261005/full_check.json')
    if digest(plan_path) != check['plan_sha256']: raise ValueError('Changed plan')
    plan = read(plan_path)
    old = sorted({v for j in plan['jobs'] if j['stage']=='fine' and j['variant']=='default'
                  and j['condition'] in ['motor_003','motor_004','motor_005'] for v in j['lesion_ids']})
    out.mkdir(parents=True,exist_ok=False)
    paths = [FEATURES, SELECTION, plan_path, Path(__file__), ROOT/'scripts/pcdr_fullpool_relaxation.py',
             ROOT/'scripts/pcdr_fractional_completion.py', ROOT/'eigencircuits/controls.py']
    write(out/'protocol.json',dict(recorded_utc=now(),
        reason='Test whether baseline feature balance permits witnesses with less overlap than the existing 50/51 comparisons.',
        objective='Minimize fractional membership in the union of the three existing comparisons.',old_union=old,
        constraints='Unchanged 51-cell support, exclusions, exact model-sign/recruitment/motor counts and conservative sufficient six-feature mean bounds.',
        binary_rule='Enumerate every completion of at most 12 fractional cells; retain all sets passing original six pooled population-variance SMD <=0.1. Do not relax thresholds or extend search.',
        budget='One LP, 60 seconds internal, one worker with 90 seconds external deadline including enumeration. No automatic retry.',
        interpretation='Baseline-only feasibility. No lesion outcome enters selection; no random null or new convergence criterion.',
        inputs={str(p):digest(p) for p in paths}))
    process = run_bounded([sys.executable,str(Path(__file__).resolve()),'--worker','--out',str(out)],out/'logs',90,cwd=ROOT)
    write(out/'process.json',process)
    if process['timed_out'] or process['returncode']:
        raise RuntimeError('Search stopped or failed; preserve logs and inspect')
    print(read(out/'complete.json'))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--plan',type=Path,default=ROOT/'results/pcdr/fine_download_20261005/plan.json')
    parser.add_argument('--worker',action='store_true')
    args=parser.parse_args()
    if args.worker: worker(args.out)
    else: run(args.out,args.plan)
