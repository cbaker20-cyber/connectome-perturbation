"""Recheck binary candidates and bound CDF mismatch using stratum counts alone."""
from collections import Counter
from pathlib import Path
import argparse
import sys

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.pcdr_ccr_transfer import read, write, digest
from scripts.pcdr_matching_audit import FEATURES, SELECTION
from eigencircuits.controls import FULL_FEATURES
from eigencircuits.common import sugar_ids, environment


def cdf_bounds(values, groups, counts, target):
    values, target=np.asarray(values,float),np.asarray(target,float)
    if values.ndim!=2 or target.ndim!=2 or values.shape[1]!=target.shape[1] or not len(target):
        raise ValueError('Invalid feature dimensions')
    if not np.isfinite(values).all() or not np.isfinite(target).all() or sum(counts.values())!=len(target):
        raise ValueError('Invalid feature values or counts')
    if len(groups)!=len(values): raise ValueError('Wrong stratum length')
    pools={key:np.array([i for i,g in enumerate(groups) if g==key]) for key in counts}
    if any(len(pools[k])<v for k,v in counts.items()): raise ValueError('Insufficient stratum capacity')
    rows=[]
    for j in range(values.shape[1]):
        points=np.unique(np.r_[values[:,j],target[:,j]])
        target_cdf=np.searchsorted(np.sort(target[:,j]),points,side='right')/len(target)
        lower,upper=np.zeros(len(points),dtype=int),np.zeros(len(points),dtype=int)
        for key,k in counts.items():
            a=np.sort(values[pools[key],j])
            left=np.searchsorted(a,points,side='right')
            lower+=np.maximum(0,k-(len(a)-left))
            upper+=np.minimum(k,left)
        gaps=np.maximum.reduce([lower/len(target)-target_cdf,target_cdf-upper/len(target),np.zeros(len(points))])
        i=int(np.argmax(gaps))
        rows.append(dict(lower_bound=float(gaps[i]),threshold=float(points[i]),target_cdf=float(target_cdf[i]),
                         min_candidate_cdf=float(lower[i]/len(target)),max_candidate_cdf=float(upper[i]/len(target))))
    return rows


def audit_members(ids, frame, target_ids, counts, refs, cap):
    if len(ids)!=51 or len(set(ids))!=51 or any(type(v) is not str for v in ids):
        raise ValueError('Invalid exact membership IDs')
    if not set(ids)<=set(frame.index) or set(ids)&(set(target_ids)|set(sugar_ids())):
        raise ValueError('Ineligible member')
    chosen=frame.loc[ids]
    actual=Counter(zip(chosen.model_sign.astype(str),chosen.recruited.astype(bool),chosen.super_class.eq('motor')))
    if actual!=counts: raise ValueError('Stratum mismatch')
    a=np.log1p(frame.loc[target_ids,FULL_FEATURES].to_numpy(float))
    b=np.log1p(chosen[FULL_FEATURES].to_numpy(float))
    variance_a,variance_b=a.var(axis=0),b.var(axis=0)
    mean_gap=np.abs(a.mean(axis=0)-b.mean(axis=0))
    if np.any(mean_gap>.099*np.sqrt(variance_a/2)+1e-10): raise ValueError('Mean constraint mismatch')
    denom=np.sqrt((variance_a+variance_b)/2)
    smd=np.divide(mean_gap,denom,out=np.zeros_like(mean_gap),where=denom>0)
    if np.any((denom==0)&(mean_gap>0)) or np.any(smd>.1): raise ValueError('SMD mismatch')
    gaps=[]
    # Direct counts at each observed value use a different path from solver rows.
    for aa,bb in zip(a.T,b.T):
        gaps.append(max(abs(float((aa<=v).mean()-(bb<=v).mean())) for v in set(aa)|set(bb)))
    overlaps={name:len(set(ids)&set(r)) for name,r in refs.items()}
    if cap is not None and max(overlaps.values())>cap: raise ValueError('Overlap mismatch')
    return dict(smd=smd.tolist(),ecdf_gaps=gaps,maximum_ecdf_gap=max(gaps),
                variance_ratios=[None if x==0 else float(y/x) for x,y in zip(variance_a,variance_b)],overlaps=overlaps)


def verify(study,out):
    protocol=read(study/'protocol.json')
    for path,h in protocol['inputs'].items():
        if digest(path)!=h: raise ValueError('Frozen input changed: '+path)
    frame=pd.read_parquet(FEATURES)
    if not frame.root_id.is_unique or not frame.root_id.map(lambda v:isinstance(v,str)).all():
        raise ValueError('Invalid feature IDs')
    frame=frame.set_index('root_id')
    raw=frame[FULL_FEATURES].to_numpy(float)
    if not np.isfinite(raw).all() or (raw<0).any(): raise ValueError('Invalid raw features')
    values=np.log1p(raw)
    target_ids=read(SELECTION)['root_ids']
    index={v:i for i,v in enumerate(frame.index)}
    ti=[index[v] for v in target_ids]
    groups=list(zip(frame.model_sign.astype(str),frame.recruited.astype(bool),frame.super_class.eq('motor')))
    counts=Counter(groups[i] for i in ti)
    excluded=set(target_ids)|set(sugar_ids())
    eligible=[i for i,v in enumerate(frame.index) if v not in excluded and groups[i] in counts]
    if len(protocol['candidate_ids'])!=len(set(protocol['candidate_ids'])):raise ValueError('Duplicate pool IDs')
    restricted=[index[v] for v in protocol['candidate_ids']]
    if not set(restricted)<=set(eligible):raise ValueError('Ineligible pool member')
    # Rebuild the declared pool, including tie order, without the search loader.
    chosen=set(v for r in protocol['references'].values() for v in r)
    neighbors=protocol.get('neighbors_per_target',20)
    if type(neighbors) is not int or neighbors not in [20,50]:raise ValueError('Unsupported pool design')
    scale=values.std(axis=0);scale[scale==0]=1
    for i in ti:
        pool=np.array([j for j in eligible if groups[j]==groups[i]])
        distance=np.square((values[pool]-values[i])/scale).sum(axis=1)
        nearest=sorted(zip(distance,frame.index[pool]),key=lambda v:(v[0],v[1]))[:neighbors]
        chosen.update(v for _,v in nearest)
    if sorted(chosen)!=protocol['candidate_ids']:raise ValueError('Candidate pool reconstruction differs')
    records={}
    for kind in protocol['solves']:
        process=read(study/kind/'process.json');result=read(study/kind/'result.json')
        if process['returncode']!=0 or process['timed_out']:raise ValueError('Worker failed')
        if not result['candidate_verified']:raise ValueError('No candidate to verify')
        candidate=read(study/kind/'candidate.json')
        if not set(candidate['root_ids'])<=set(protocol['candidate_ids']):raise ValueError('Candidate outside pool')
        audit=audit_members(candidate['root_ids'],frame,target_ids,counts,protocol['references'],None if kind=='unconstrained_overlap' else 30)
        for name in ['smd','ecdf_gaps','variance_ratios']:
            np.testing.assert_allclose(audit[name],candidate['audit'][name],rtol=0,atol=1e-12)
        if abs(audit['maximum_ecdf_gap']-result['objective'])>1e-7:raise ValueError('Objective differs')
        if result['success'] and (result['mip_gap']!=0 or abs(result['dual_bound']-result['objective'])>1e-7):
            raise ValueError('Reported optimality bounds disagree')
        records[kind]=dict(audit=audit,solver_reported_optimal=result['success'],objective=result['objective'],
                          worker_seconds=process['elapsed_seconds'])
    bounds={name:cdf_bounds(values[pool],[groups[i] for i in pool],counts,values[ti])
            for name,pool in [('restricted',restricted),('full_eligible',eligible)]}
    result=dict(status='verified',candidate_pool_size=len(restricted),full_eligible_pool_size=len(eligible),
        candidates=records,stratum_only_bounds={name:dict(zip(FULL_FEATURES,rows)) for name,rows in bounds.items()},
        limitation='Solver optimality is numerical and restricted to the declared pool and constraints. Stratum bounds omit mean/overlap constraints. No simulated outcomes or random reference inference.',
        inputs={str(p):digest(p) for p in [study/'protocol.json',*[study/k/n for k in protocol['solves'] for n in ['candidate.json','result.json','process.json']]]},
        environment=environment(),script_sha256=digest(Path(__file__)))
    if out.exists():raise FileExistsError(out)
    write(out,result)
    print({name:{f:r['lower_bound'] for f,r in rows.items()} for name,rows in result['stratum_only_bounds'].items()})


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--study',type=Path,default=ROOT/'results/pcdr/distribution_match_20261008')
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();verify(args.study,args.out)
