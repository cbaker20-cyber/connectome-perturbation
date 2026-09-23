"""Prospective baseline-only second-moment feasibility check, not a new null test."""
import os
for key in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS']:
    os.environ[key] = '1'
import json
from pathlib import Path
import sys
import numpy as np
from scipy.optimize import linprog
from scipy.sparse import csc_matrix, vstack
import warnings

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from eigencircuits.common import atomic_json, now, sha256
from eigencircuits.controls import FULL_FEATURES
from scripts.pcdr_fullpool_relaxation import load_design
from scripts.pcdr_matching_audit import FEATURES, SELECTION
from scripts.pcdr_bounded_process import run_bounded
OUT = ROOT/'results/pcdr/distribution_feasibility_20260922'


def worker():
    f, x, ti, pool, groups, counts, scale, tolerances = load_design()
    target = x[ti]
    mean, variance = target.mean(0), target.var(0)
    if (variance <= 0).any():
        raise ValueError('Zero target variance requires a separately specified design')
    n = len(ti)
    # Q is the average squared deviation from the TARGET mean, divided by target variance.
    q = (x[pool]-mean)**2/variance
    keys = sorted(counts)
    strata = np.array([[groups[i] == k for i in pool] for k in keys], float)
    lower_q = sum(np.sort(q[strata[j].astype(bool)], axis=0)[:counts[k]].sum(0)
                  for j, k in enumerate(keys))/n
    mean_rows = csc_matrix(x[pool].T/n/scale[:, None])
    q_rows = csc_matrix(q.T/n)
    a = vstack([mean_rows, -mean_rows, q_rows, -q_rows]).tocsc()
    tol = tolerances['conservative']
    b = np.r_[(mean+tol)/scale, -(mean-tol)/scale, np.full(6, 2.), np.full(6, -.505)]
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        result = linprog(np.zeros(len(pool)), A_ub=a, b_ub=b,
                         A_eq=csc_matrix(strata), b_eq=[counts[k] for k in keys],
                         bounds=(0, 1), method='highs', options={'time_limit':60, 'threads':1})
    record = {'recorded_utc': now(), 'status':int(result.status), 'message':result.message,
              'pool_size':len(pool), 'coordinatewise_minimum_Q':dict(zip(FULL_FEATURES, lower_q.tolist())),
              'warnings':[str(w.message) for w in caught], 'binary_sets_accepted':0}
    if result.x is not None:
        weights = result.x
        error = max(float(np.maximum(a@weights-b, 0).max()),
                    float(abs(strata@weights-np.array([counts[k] for k in keys])).max()),
                    float(max(0, -weights.min(), weights.max()-1)))
        if error > 1e-6:
            raise ValueError('Independent primal validation failed')
        record.update(maximum_constraint_violation=error,
                      fractional_count=int(((weights>1e-7)&(weights<1-1e-7)).sum()),
                      Q=(weights@q/n).tolist())
        import pandas as pd
        pd.DataFrame({'root_id':f.iloc[pool].root_id, 'weight':weights}).to_parquet(OUT/'weights.parquet',index=False)
    atomic_json(OUT/'result.json',record)
    print(json.dumps(record))


def main():
    OUT.mkdir(exist_ok=False)
    atomic_json(OUT/'protocol.json',{
        'recorded_utc':now(),
        'timing':'Specified after observing the motor-composition pilot imbalance; prospective for this baseline-only diagnostic, not the original preregistration.',
        'fixed':'Same 51 targets, full eligible pool, input/target exclusions and exact sign/recruitment/motor strata. Same six log1p features.',
        'guard':'For each feature require abs(mean difference)<=0.099 sqrt(target population variance/2), and 0.505<=Q<=2 where Q is mean squared deviation from target mean divided by target variance.',
        'derivation':'Variance ratio = Q - (mean difference)^2/target variance. These bounds imply ratio in [0.5000995,2] and original pooled SMD<0.1. This is an investigator-chosen sensitivity guard, not a biological cutoff or a test of distribution equality.',
        'procedure':'One zero-objective continuous LP, 60 seconds internal and 90 seconds external. Independently validate primal constraints. Calculate coordinatewise minimum Q under exact strata. Do not change bounds, round solutions, simulate, or claim binary feasibility.',
        'interpretation':'Infeasibility excludes only this stricter program. Feasibility leaves binary feasibility, diversity, cell-type balance and random-reference validity unresolved.',
        'references':['https://pmc.ncbi.nlm.nih.gov/articles/3472075/','https://pmc.ncbi.nlm.nih.gov/articles/PMC2943670/'],
        'hashes':{str(p.relative_to(ROOT)):sha256(p) for p in [FEATURES,SELECTION,Path(__file__),ROOT/'scripts/pcdr_fullpool_relaxation.py',ROOT/'scripts/pcdr_bounded_process.py']}})
    result=run_bounded([sys.executable,str(Path(__file__)),'--worker'],OUT/'worker',90,cwd=ROOT)
    atomic_json(OUT/'execution.json',result)
    if result['returncode'] != 0:
        raise RuntimeError('Worker did not finish; inspect retained logs')


if __name__=='__main__':
    worker() if '--worker' in sys.argv else main()
