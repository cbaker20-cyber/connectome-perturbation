"""Rebuild overlap LP rows and check dual bounds with rational arithmetic."""
from fractions import Fraction
from pathlib import Path
import argparse
import sys
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.pcdr_ccr_transfer import read, write, digest, utc
from scripts.pcdr_matching_audit import FEATURES, SELECTION
from eigencircuits.controls import FULL_FEATURES


def rational_bound(c,a,b,eq,rhs,y,z):
    f=lambda x:Fraction.from_float(float(x))
    if any(v>0 for v in y):raise ValueError('Positive inequality multiplier')
    yy,zz=list(map(f,y)),list(map(f,z))
    bound=sum((f(v)*w for v,w in zip(b,yy)),Fraction(0))+sum((f(v)*w for v,w in zip(rhs,zz)),Fraction(0))
    for j,coefficient in enumerate(c):
        residual=f(coefficient)-sum((f(row[j])*w for row,w in zip(a,yy)),Fraction(0))-sum((f(row[j])*w for row,w in zip(eq,zz)),Fraction(0))
        bound+=min(Fraction(0),residual)
    return bound


def verify(study,out):
    if out.exists():raise FileExistsError(out)
    p,r,process=read(study/'protocol.json'),read(study/'result.json'),read(study/'process.json')
    if process['timed_out'] or process['returncode']!=0:raise ValueError('Incomplete LP worker')
    for path,h in p['inputs'].items():
        if digest(path)!=h:raise ValueError('Changed input: '+path)
    frame=pd.read_parquet(FEATURES)
    if not frame.root_id.is_unique or not frame.root_id.map(lambda x:type(x) is str).all():raise ValueError('Invalid IDs')
    frame=frame.set_index('root_id')
    raw=frame[FULL_FEATURES].to_numpy(float)
    if not np.isfinite(raw).all() or (raw<0).any():raise ValueError('Invalid features')
    values=pd.DataFrame(np.log1p(raw),index=frame.index,columns=FULL_FEATURES)
    scale=values.to_numpy().std(axis=0);scale[scale==0]=1
    target_ids=read(SELECTION)['root_ids']
    target=values.loc[values.index.isin(target_ids)].to_numpy()
    target_frame=frame.loc[frame.index.isin(target_ids)]
    def keys(f):return list(zip(f.model_sign.astype(str),f.recruited.astype(bool),f.super_class.eq('motor')))
    from collections import Counter
    counts=Counter(keys(target_frame));checks={}
    source=Path(p['anchor_study'])
    for name,saved in r['cases'].items():
        case=read(source/name/'protocol.json');ids=case['candidate_ids']
        chosen=values.loc[ids].to_numpy();groups=keys(frame.loc[ids])
        rows=[];upper=[]
        for sign in [1,-1]:
            for j in range(len(FULL_FEATURES)):
                rows.append(sign*chosen[:,j]/51/scale[j])
                upper.append((sign*target[:,j].mean()+.099*np.sqrt(target[:,j].var()/2))/scale[j])
        for ref,members in case['references'].items():
            if ref!='fixed_anchor':rows.append(np.array([float(i in set(members)) for i in ids]));upper.append(30.)
        eq=np.array([[float(g==key) for g in groups] for key in sorted(counts)])
        rhs=np.array([counts[k] for k in sorted(counts)])
        c=np.array([float(i in set(case['references']['fixed_anchor'])) for i in ids])
        path=study/(name+'.npz')
        with np.load(path,allow_pickle=False) as data:
            for key,expected in [('a',rows),('b',upper),('eq',eq),('rhs',rhs),('c',c)]:
                np.testing.assert_allclose(data[key],expected,rtol=0,atol=1e-14)
            cert=saved['certificate']
            exact=rational_bound(data['c'],data['a'],data['b'],data['eq'],data['rhs'],cert['inequality_multipliers'],cert['equality_multipliers'])
            x=data['weights']
            violation=max(0,float((data['a']@x-data['b']).max()),float(np.abs(data['eq']@x-data['rhs']).max()),float((-x).max()),float((x-1).max()))
            if violation>1e-7:raise ValueError('Invalid saved primal')
        if abs(float(exact)-cert['raw_lower_bound'])>1e-8:raise ValueError('Bound arithmetic mismatch')
        checks[name]=dict(exact_encoded_lp_bound=str(exact),bound_decimal=float(exact),
            exceeds_30=exact>30,guarded_bound=cert['guarded_lower_bound'],primal_violation=violation,vector_sha256=digest(path))
    write(out,dict(status='verified',checks=checks,checked_utc=utc(),checker_sha256=digest(__file__),
        inputs={str(study/n):digest(study/n) for n in ['protocol.json','result.json','process.json']},
        scope='Exact rational dual evaluation applies to saved floating-point LP coefficients; independent feature-row reconstruction agrees within 1e-14. The guarded numerical conclusion is for the recorded fixed-anchor design, not all pairs or full-pool biological feasibility.'))
    print({k:v['bound_decimal'] for k,v in checks.items()})


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--study',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();verify(args.study,args.out)
