"""Find baseline-only feasibility witnesses, not a random control distribution."""
import os
for name in ["OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"]:
    os.environ[name] = "1"
from pathlib import Path
import sys
import json
import numpy as np
import pandas as pd
from scipy.optimize import milp, Bounds, LinearConstraint
from scipy.sparse import csc_matrix
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from eigencircuits.controls import FULL_FEATURES, standardized_difference
from eigencircuits.common import atomic_json, now, sha256, sugar_ids
from scripts.pcdr_matching_audit import FEATURES, SELECTION, OUT


def main():
    dest=ROOT/'results/pcdr/fullpool_motor_20260922'; dest.mkdir(exist_ok=False)
    atomic_json(dest/'protocol.json',{'recorded_utc':now(), 'purpose':'Post-pilot motor-composition matching feasibility only; no simulation or automatic null inference. One 60-second solve maximum. Failure is not proof original pooled-SMD feasible region empty.',
        'method':'Binary integer selection from ALL eligible cells in target motor/sign/recruitment strata; exact size/sign/recruitment/motor counts.',
        'sufficient_constraint':'abs(control mean - target mean) <= 0.099 * sqrt(target population variance / 2) on each log1p feature. This guarantees original pooled SMD <0.1 because sample variance is nonnegative.',
        'objective':'One fixed uniform random linear objective from seed 631101. Feasibility witness only, not random sampling.',
        'limits':'60 seconds for one solve, one HiGHS thread; infeasibility here does not prove original criteria infeasible. These are optimized witnesses, not draws from the original sampler or a calibrated null.',
        'amendment':'User requested methodical refinement. Only candidate coverage changes from the previous nearest-64 attempt; all conservative bounds and biological strata stay fixed. No lesions follow automatically.',
        'reference':'Zubizarreta, Paredes and Rosenbaum 2014, doi:10.1214/13-AOAS713 motivates direct balance constraints; this fixed-size feasibility program is not a reproduction of their cardinality-matching procedure.',
        'command':[sys.executable,str(Path(__file__).resolve())],
        'hashes':{str(p.relative_to(ROOT)):sha256(p) for p in [FEATURES,SELECTION,Path(__file__)]}})
    f=pd.read_parquet(FEATURES);f.root_id=f.root_id.astype(str)
    ids=json.loads(SELECTION.read_text())['root_ids']; ti=np.flatnonzero(f.root_id.isin(ids)); n=len(ti)
    x=np.log1p(f[FULL_FEATURES].to_numpy(float));scale=x.std(0);scale[scale==0]=1;z=x/scale
    strata=list(zip(f.model_sign.astype(str),f.recruited.astype(bool),f.super_class.eq('motor')))
    keys=sorted(set(strata[i] for i in ti)); poolmask=~f.root_id.isin(set(ids)|set(sugar_ids()))
    pool=np.array([i for i in np.flatnonzero(poolmask) if strata[i] in keys]); counts=np.array([sum(strata[i]==k for i in ti) for k in keys])
    a=np.array([[strata[i]==k for i in pool] for k in keys],float)
    # Normalize feature constraints for better numerical conditioning.
    feature_rows=x[pool].T/n/scale[:,None]
    mean=x[ti].mean(0)/scale;tol=.099*np.sqrt(x[ti].var(0)/2)/scale
    a=np.vstack([a,feature_rows]);lo=np.r_[counts,mean-tol];hi=np.r_[counts,mean+tol]
    rng=np.random.default_rng(631101); records=[];members=[];seen=[]
    for run in range(1):
        result=milp(rng.uniform(size=len(pool)),integrality=np.ones(len(pool)),bounds=Bounds(0,1),
                    constraints=LinearConstraint(csc_matrix(a),lo,hi),options={'time_limit':60,'mip_rel_gap':0.01,'threads':1})
        rec={'run':run,'status':int(result.status),'message':result.message,'accepted_witness':False}
        if result.x is not None:
            bits=np.rint(result.x).astype(int);chosen=pool[bits==1]
            balance=standardized_difference(x[ti],x[chosen])
            valid=(np.max(np.abs(result.x-bits))<1e-5 and len(chosen)==n and
                   all(sum(strata[i]==k for i in chosen)==c for k,c in zip(keys,counts)) and
                   np.all(balance<=.1) and np.all(a@bits >= lo-1e-7) and np.all(a@bits <= hi+1e-7) and not set(f.iloc[chosen].root_id)&(set(ids)|set(sugar_ids())))
            if not valid:raise AssertionError('Independent witness validation failed')
            rec.update(accepted_witness=True,maximum_smd=float(max(balance)),smd=dict(zip(FULL_FEATURES,map(float,balance))))
            for i in chosen:members.append({'witness':run,'root_id':f.iloc[i].root_id})
            seen.append(set(map(int,chosen)))
            a=np.vstack([a,bits]);lo=np.r_[lo,-np.inf];hi=np.r_[hi,n-1]
        records.append(rec)
        atomic_json(dest/'progress.json',{'updated_utc':now(),'records':records})
        if not rec['accepted_witness']:break
    pd.DataFrame(members,columns=['witness','root_id']).to_parquet(dest/'members.parquet',index=False)
    overlap=[{'a':i,'b':j,'shared':len(u&v),'jaccard':len(u&v)/len(u|v)} for i,u in enumerate(seen) for j,v in enumerate(seen) if i<j]
    atomic_json(dest/'summary.json',{'completed_utc':now(),'candidate_pool':len(pool),'witness_count':len(seen),
        'records':records,'overlap':overlap,'claim':('Full-pool conservative feasibility witness found; no random-reference inference.' if seen else 'No full-pool conservative witness found. Solver status determines infeasible versus unresolved; original pooled-SMD feasibility remains untested.'),
        'outputs':{p.name:sha256(p) for p in dest.iterdir() if p.is_file()}})
    print(json.dumps({'witnesses':len(seen),'records':records}))


if __name__=='__main__':main()
