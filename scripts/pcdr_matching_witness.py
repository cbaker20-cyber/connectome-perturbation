"""Find baseline-only feasibility witnesses, not a random control distribution."""
from pathlib import Path
import sys
import json
import numpy as np
import pandas as pd
from scipy.optimize import milp, Bounds, LinearConstraint
from scipy.spatial import cKDTree
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from eigencircuits.controls import FULL_FEATURES, standardized_difference
from eigencircuits.common import atomic_json, now, sha256, sugar_ids
from scripts.pcdr_matching_audit import FEATURES, SELECTION, OUT


def main():
    dest=OUT/'witness'; dest.mkdir(exist_ok=False)
    atomic_json(dest/'protocol.json',{'recorded_utc':now(), 'purpose':'Feasibility only; never used as Monte Carlo controls automatically.',
        'method':'Binary integer selection from union of original nearest-64 neighborhoods; exact size/sign/recruitment counts.',
        'sufficient_constraint':'abs(control mean - target mean) <= 0.099 * sqrt(target population variance / 2) on each log1p feature. This guarantees original pooled SMD <0.1 because sample variance is nonnegative.',
        'objective':'Five fixed independent uniform random linear objectives from seed 630610; exclude previous whole sets with no-good constraints.',
        'limits':'30 seconds per solve, five solves maximum; infeasibility here does not prove original criteria infeasible. These are optimized witnesses, not draws from the original sampler or a calibrated null.',
        'reference':'Zubizarreta, Paredes and Rosenbaum 2014, doi:10.1214/13-AOAS713 motivates direct balance constraints; this fixed-size feasibility program is not a reproduction of their cardinality-matching procedure.',
        'command':[sys.executable,str(Path(__file__).resolve())],
        'hashes':{str(p.relative_to(ROOT)):sha256(p) for p in [FEATURES,SELECTION,Path(__file__)]}})
    f=pd.read_parquet(FEATURES);f.root_id=f.root_id.astype(str)
    ids=json.loads(SELECTION.read_text())['root_ids']; ti=np.flatnonzero(f.root_id.isin(ids)); n=len(ti)
    x=np.log1p(f[FULL_FEATURES].to_numpy(float));scale=x.std(0);scale[scale==0]=1;z=x/scale
    strata=list(zip(f.model_sign.astype(str),f.recruited.astype(bool)))
    keys=sorted(set(strata[i] for i in ti)); poolmask=~f.root_id.isin(set(ids)|set(sugar_ids()))
    neighborhood=[]
    for key in keys:
        pool=np.array([i for i in np.flatnonzero(poolmask) if strata[i]==key])
        targets=[i for i in ti if strata[i]==key]
        _,ix=cKDTree(z[pool]).query(z[targets],k=min(64,len(pool)))
        neighborhood.extend(pool[np.asarray(ix).reshape(-1)])
    pool=np.unique(neighborhood); counts=np.array([sum(strata[i]==k for i in ti) for k in keys])
    a=np.array([[strata[i]==k for i in pool] for k in keys],float)
    # Normalize feature constraints for better numerical conditioning.
    feature_rows=x[pool].T/n/scale[:,None]
    mean=x[ti].mean(0)/scale;tol=.099*np.sqrt(x[ti].var(0)/2)/scale
    a=np.vstack([a,feature_rows]);lo=np.r_[counts,mean-tol];hi=np.r_[counts,mean+tol]
    rng=np.random.default_rng(630610); records=[];members=[];seen=[]
    for run in range(5):
        result=milp(rng.uniform(size=len(pool)),integrality=np.ones(len(pool)),bounds=Bounds(0,1),
                    constraints=LinearConstraint(a,lo,hi),options={'time_limit':30,'mip_rel_gap':0.01})
        rec={'run':run,'status':int(result.status),'message':result.message,'accepted_witness':False}
        if result.x is not None:
            bits=np.rint(result.x).astype(int);chosen=pool[bits==1]
            balance=standardized_difference(x[ti],x[chosen])
            valid=(np.max(np.abs(result.x-bits))<1e-5 and len(chosen)==n and
                   all(sum(strata[i]==k for i in chosen)==c for k,c in zip(keys,counts)) and
                   np.all(balance<=.1) and not set(f.iloc[chosen].root_id)&(set(ids)|set(sugar_ids())))
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
        'records':records,'overlap':overlap,'claim':'Feasible examples under original balance criteria only; no lesion effects or inferential p-values.',
        'outputs':{p.name:sha256(p) for p in dest.iterdir() if p.is_file()}})
    print(json.dumps({'witnesses':len(seen),'records':records}))


if __name__=='__main__':main()
