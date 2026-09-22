"""Necessary per-feature SMD bounds over all sets with fixed stratum counts."""
from pathlib import Path
from collections import Counter
import sys,json
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.pcdr_matching_audit import mean_bounds,FEATURES,SELECTION
from eigencircuits.controls import FULL_FEATURES
from eigencircuits.common import atomic_json,sha256,now,sugar_ids

def smd_lower_bounds(target,values,counts,pools):
 low,high=mean_bounds(values,counts,pools)
 _,qhigh=mean_bounds(values**2,counts,pools)
 vmax=np.maximum(0,qhigh-low**2)
 distance=np.maximum(np.maximum(low-target.mean(0),target.mean(0)-high),0)
 denom=np.sqrt((target.var(0)+vmax)/2)
 lower=np.divide(distance,denom,out=np.where(distance==0,0.,np.inf),where=denom>0)
 return low,high,vmax,lower

def main():
 out=ROOT/'results/pcdr/fullpool_motor_20260922'
 atomic_json(out/'bounds_protocol.json',{'recorded_utc':now(),'purpose':'Post-stop diagnostic: necessary coordinatewise lower bound on original pooled SMD for full eligible pool with exact motor/sign/recruitment counts. No optimizer or simulation.', 'method':'For nonnegative log1p features, compute exact stratum-constrained extrema L,U of mean and upper Q of second moment. Variance <= Q-L^2. SMD >= distance(target mean,[L,U])/sqrt((target variance + Q-L^2)/2). A lower bound >0.1 rules out that feature; otherwise no feasibility conclusion.', 'command':[sys.executable,str(Path(__file__))],'hashes':{str(p.relative_to(ROOT)):sha256(p) for p in [FEATURES,SELECTION,Path(__file__)]}})
 f=pd.read_parquet(FEATURES);f.root_id=f.root_id.astype(str);assert not f.root_id.duplicated().any()
 ids=json.loads(SELECTION.read_text())['root_ids'];ti=np.flatnonzero(f.root_id.isin(ids));assert len(ti)==len(ids)==len(set(ids))
 vals=f[FULL_FEATURES].to_numpy(float);assert np.isfinite(vals).all() and np.all(vals>=0)
 x=np.log1p(vals);strata=list(zip(f.model_sign.astype(str),f.recruited.astype(bool),f.super_class.eq('motor')))
 counts=Counter(strata[i] for i in ti);eligible=np.flatnonzero(~f.root_id.isin(set(ids)|set(sugar_ids())))
 pools={key:np.array([i for i in eligible if strata[i]==key]) for key in counts}
 low,high,vmax,lower=smd_lower_bounds(x[ti],x,counts,pools)
 rows=[{'feature':name,'target_mean':float(x[ti,j].mean()),'minimum_mean':float(low[j]),'maximum_mean':float(high[j]),'variance_upper_bound':float(vmax[j]),'smd_lower_bound':float(lower[j]),'rules_out_original_limit':bool(lower[j]>.1)} for j,name in enumerate(FULL_FEATURES)]
 atomic_json(out/'bounds.json',{'completed_utc':now(),'pool_count':sum(map(len,pools.values())),'features':rows,'interpretation':'Necessary bounds only; passing every bound does not prove joint feasibility.'})
 print(json.dumps(rows))
if __name__=='__main__':main()
