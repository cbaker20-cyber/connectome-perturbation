"""Independently check new comparison memberships and their feature distributions."""
from collections import Counter
from itertools import combinations
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
from eigencircuits.common import sugar_ids


def distribution_check(target, candidate):
    target, candidate = np.asarray(target,float), np.asarray(candidate,float)
    if target.ndim != 2 or candidate.shape != target.shape or not len(target):
        raise ValueError('Invalid feature dimensions')
    if not np.isfinite(target).all() or not np.isfinite(candidate).all():
        raise ValueError('Nonfinite features')
    tv, cv = target.var(axis=0), candidate.var(axis=0)
    difference = np.abs(target.mean(axis=0)-candidate.mean(axis=0))
    denominator = np.sqrt((tv+cv)/2)
    smd = np.divide(difference,denominator,out=np.zeros_like(difference),where=denominator>0)
    smd[(denominator==0)&(difference>0)] = np.inf
    gaps = []
    for a,b in zip(target.T,candidate.T):
        points=np.unique(np.r_[a,b])
        gaps.append(float(np.max(np.abs(np.searchsorted(np.sort(a),points,side='right')/len(a)-
                                       np.searchsorted(np.sort(b),points,side='right')/len(b)))))
    return smd, [None if a==0 else float(b/a) for a,b in zip(tv,cv)], gaps


def verify(study, out):
    complete, protocol = read(study/'complete.json'), read(study/'protocol.json')
    if complete['status']!='complete': raise ValueError('Incomplete search')
    for name,h in complete['outputs'].items():
        if digest(study/name)!=h: raise ValueError('Changed search output: '+name)
    for name,h in protocol['inputs'].items():
        if digest(name)!=h: raise ValueError('Changed search input: '+name)
    f=pd.read_parquet(FEATURES)
    if not f.root_id.map(lambda v:isinstance(v,str)).all() or not f.root_id.is_unique:
        raise ValueError('Invalid exact feature IDs')
    f=f.set_index('root_id')
    target_ids=read(SELECTION)['root_ids']
    if len(target_ids)!=len(set(target_ids)) or len(target_ids)!=51: raise ValueError('Invalid target')
    excluded=set(target_ids)|set(sugar_ids())
    raw=f[FULL_FEATURES].to_numpy(float)
    if not np.isfinite(raw).all() or (raw<0).any(): raise ValueError('Invalid raw features')
    values=pd.DataFrame(np.log1p(raw),index=f.index,columns=FULL_FEATURES)
    def strata(ids):
        sub=f.loc[ids]
        return Counter(zip(sub.model_sign.astype(str),sub.recruited.astype(bool),sub.super_class.eq('motor')))
    required=strata(target_ids)
    members=pd.read_csv(study/'members.csv',dtype={'root_id':str})
    assignments=pd.read_csv(study/'assignments.csv')
    expected=set(assignments.loc[assignments.accepted_original_smd,'assignment'])
    if set(members.assignment)!=expected or len(expected)!=complete['accepted_count']:
        raise ValueError('Accepted assignment coverage mismatch')
    rows,sets=[],{}
    for key,g in members.groupby('assignment'):
        ids=g.root_id.tolist()
        if len(ids)!=51 or len(set(ids))!=51 or not set(ids)<=set(f.index) or set(ids)&excluded:
            raise ValueError('Invalid candidate membership')
        if strata(ids)!=required: raise ValueError('Wrong candidate strata')
        sets[int(key)]=set(ids)
        smd,ratios,gaps=distribution_check(values.loc[target_ids],values.loc[ids])
        if (smd>.1).any(): raise ValueError('Original SMD rule failed')
        saved=assignments.loc[assignments.assignment.eq(key)]
        if len(saved)!=1 or not np.allclose(smd,saved[FULL_FEATURES].to_numpy()[0],atol=1e-12,rtol=0):
            raise ValueError('Saved balance differs')
        overlap=len(set(ids)&set(protocol['old_union']))
        if overlap!=saved.old_union_overlap.item(): raise ValueError('Saved overlap differs')
        rows.append(dict(assignment=int(key),old_union_overlap=overlap,maximum_smd=float(max(smd)),
            features={name:dict(smd=float(smd[i]),variance_ratio=ratios[i],ecdf_gap=gaps[i])
                      for i,name in enumerate(FULL_FEATURES)}))
    if len({frozenset(s) for s in sets.values()})!=len(sets): raise ValueError('Duplicate candidate sets')
    overlaps=[len(a&b) for a,b in combinations(sets.values(),2)]
    result=dict(status='verified',candidates=rows,shared_by_all=len(set.intersection(*sets.values())) if sets else 0,
        pairwise_overlap_min=min(overlaps) if overlaps else None,pairwise_overlap_max=max(overlaps) if overlaps else None,
        input_hashes={str(p):digest(p) for p in [FEATURES,SELECTION,study/'complete.json',study/'members.csv']},
        script_sha256=digest(Path(__file__)),
        limitation='Feature distributions are descriptions, not new retrospective rejection rules. No lesion outcomes or random-reference inference.')
    if out.exists(): raise FileExistsError(out)
    write(out,result)
    print(dict(count=len(rows),shared_by_all=result['shared_by_all'],pairwise_overlap=(result['pairwise_overlap_min'],result['pairwise_overlap_max']),
        max_variance_ratio=max((v['variance_ratio'] for r in rows for v in r['features'].values() if v['variance_ratio'] is not None),default=None),
        max_ecdf_gap=max((v['ecdf_gap'] for r in rows for v in r['features'].values()),default=None)))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--study',type=Path,default=ROOT/'results/pcdr/diverse_comparisons_20261008')
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();verify(args.study,args.out)
