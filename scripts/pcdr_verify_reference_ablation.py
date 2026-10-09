"""Independent feature-row, dual-bound and binary-partner checks for cap ablation."""
from collections import Counter
from pathlib import Path
import argparse
import sys
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.pcdr_ccr_transfer import read, write, digest, utc
from scripts.pcdr_matching_audit import FEATURES, SELECTION
from scripts.pcdr_verify_anchor_bound import rational_bound
from scripts.pcdr_verify_distribution_match import audit_members
from scripts.pcdr_verify_joint_family import classify
from eigencircuits.controls import FULL_FEATURES


def expected_names(regime,references):
    original={'motor_003','motor_004','motor_005'}
    if regime=='neither':return []
    if regime=='original_three':return [k for k in references if k in original]
    if regime=='newer_twelve':return [k for k in references if k not in original]
    if regime=='both':return list(references)
    raise ValueError('Unknown regime')


def verify(study,out):
    if out.exists():raise FileExistsError(out)
    p=read(study/'protocol.json')
    for path,h in p['inputs'].items():
        if digest(path)!=h:raise ValueError('Changed frozen input: '+path)
    old=read(ROOT/'results/pcdr/distribution_expand_20261008/protocol.json')
    if p['candidate_ids']!=old['candidate_ids'] or p['references']!=old['references']:
        raise ValueError('Changed pool or references')
    for name in ['anchor_538','anchor_999']:
        previous=read(ROOT/'results/pcdr/anchor_family_20261008'/name/'protocol.json')
        if p['anchors'][name]!=previous['references']['fixed_anchor']:raise ValueError('Changed anchor')
    frame=pd.read_parquet(FEATURES)
    if not frame.root_id.is_unique or not frame.root_id.map(lambda v:type(v) is str).all():raise ValueError('Invalid IDs')
    frame=frame.set_index('root_id');raw=frame[FULL_FEATURES].to_numpy(float)
    if not np.isfinite(raw).all() or (raw<0).any():raise ValueError('Invalid features')
    values=pd.DataFrame(np.log1p(raw),index=frame.index,columns=FULL_FEATURES)
    target_ids=read(SELECTION)['root_ids'];target=values.loc[values.index.isin(target_ids)].to_numpy()
    def keys(f):return list(zip(f.model_sign.astype(str),f.recruited.astype(bool),f.super_class.eq('motor')))
    counts=Counter(keys(frame.loc[frame.index.isin(target_ids)]))
    ids=p['candidate_ids'];chosen=values.loc[ids].to_numpy();groups=keys(frame.loc[ids])
    scale=values.to_numpy().std(axis=0);scale[scale==0]=1
    eq=np.array([[float(g==key) for g in groups] for key in sorted(counts)])
    rhs=np.array([counts[k] for k in sorted(counts)])
    lp_process=read(study/'lp_process.json')
    if lp_process['returncode']!=0 or lp_process['timed_out']:raise ValueError('LP worker incomplete')
    lp=read(study/'lp_results.json')['cases']
    regimes=['neither','original_three','newer_twelve','both']
    if set(lp)!={a+'__'+r for a in p['anchors'] for r in regimes}:raise ValueError('Incomplete factorial inventory')
    checks={}
    for anchor,anchor_ids in p['anchors'].items():
        c=np.array([float(i in set(anchor_ids)) for i in ids])
        for regime in regimes:
            name=anchor+'__'+regime;record=lp[name]
            if record['status']!=0:raise ValueError('No completed LP certificate: '+name)
            rows=[];upper=[]
            for sign in [1,-1]:
                for j in range(len(FULL_FEATURES)):
                    rows.append(sign*chosen[:,j]/51/scale[j])
                    upper.append((sign*target[:,j].mean()+.099*np.sqrt(target[:,j].var()/2))/scale[j])
            for ref in expected_names(regime,p['references']):
                members=set(p['references'][ref]);rows.append([float(i in members) for i in ids]);upper.append(30.)
            path=study/(name+'.npz')
            with np.load(path,allow_pickle=False) as data:
                for key,expected in [('a',rows),('b',upper),('eq',eq),('rhs',rhs),('c',c)]:
                    np.testing.assert_allclose(data[key],expected,rtol=0,atol=1e-14)
                cert=record['certificate'];y=cert['inequality_multipliers'];z=cert['equality_multipliers']
                if len(y)!=len(upper) or len(z)!=len(rhs):raise ValueError('Wrong multiplier inventory')
                exact=rational_bound(c,data['a'],data['b'],data['eq'],data['rhs'],y,z)
                x=data['weights']
                if x.shape!=(len(ids),) or not np.isfinite(x).all():raise ValueError('Invalid primal')
                violation=max(0,float((data['a']@x-data['b']).max()),float(np.abs(eq@x-rhs).max()),float((-x).max()),float((x-1).max()))
                if violation>1e-7 or abs(float(c@x)-record['primal_objective'])>1e-8:raise ValueError('Primal failed')
            if abs(float(exact)-cert['raw_lower_bound'])>1e-8:raise ValueError('Bound failed')
            checks[name]=dict(bound_decimal=float(exact),exact_encoded_lp_bound=str(exact),guarded_bound=cert['guarded_lower_bound'],
                excludes_cap_30=cert['guarded_lower_bound']>30,primal_violation=violation,vector_sha256=digest(path))
        # Adding caps cannot improve a minimization optimum in this factorial design.
        scores={r:lp[anchor+'__'+r]['primal_objective'] for r in regimes}
        if min(scores['original_three'],scores['newer_twelve'])<scores['neither']-1e-7 or scores['both']<max(scores['original_three'],scores['newer_twelve'])-1e-7:
            raise ValueError('Constraint monotonicity failed')
    partners={}
    for anchor,anchor_ids in p['anchors'].items():
        case=study/anchor;protocol=read(case/'protocol.json')
        if protocol['references']!={'fixed_anchor':anchor_ids} or protocol['candidate_ids']!=ids:raise ValueError('Amendment mismatch')
        process=read(case/'cap_30/process.json');r=read(case/'cap_30/result.json')
        if process['returncode']!=0 or process['timed_out']:raise ValueError('Partner worker incomplete')
        exists=(case/'cap_30/candidate.json').exists()
        if exists!=r['candidate_verified']:raise ValueError('Candidate inventory mismatch')
        status=classify(r['status'],exists,r['objective'],r['dual_bound'])
        result=dict(status=status,worker_seconds=process['elapsed_seconds'],conditional_amended_design=True)
        aa=audit_members(anchor_ids,frame,target_ids,counts,p['references'],30)
        if exists:
            companion=read(case/'cap_30/candidate.json')['root_ids']
            if not set(companion)<=set(ids):raise ValueError('Companion outside pool')
            audit=audit_members(companion,frame,target_ids,counts,protocol['references'],30)
            if audit['maximum_ecdf_gap']>r['objective']+1e-7:raise ValueError('Understated CDF objective')
            if r['status']==0 and abs(audit['maximum_ecdf_gap']-r['objective'])>1e-7:raise ValueError('Optimality mismatch')
            overlaps={k:len(set(companion)&set(v)) for k,v in p['references'].items()}
            result.update(audit=audit,anchor_audit=aa,old_reference_overlaps=overlaps,
                pair_maximum_cdf_gap=max(aa['maximum_ecdf_gap'],audit['maximum_ecdf_gap']),
                conditional_pair_attains_fixed_anchor_floor=audit['maximum_ecdf_gap']<=aa['maximum_ecdf_gap']+1e-12)
        partners[anchor]=result
    files=list(study.rglob('*.json'))
    write(out,dict(status='verified',lp_checks=checks,partners=partners,checked_utc=utc(),
        checker_sha256=digest(__file__),inputs={str(f):digest(f) for f in files},
        scope='Complete declared eight-case diagnostic and two conditional amended searches; not exhaustive over all pools, anchors, matching rules or biological mechanisms. Exact rational arithmetic applies to saved floating-point LP coefficients.'))
    print({k:v['status'] for k,v in partners.items()})


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--study',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();verify(args.study,args.out)
