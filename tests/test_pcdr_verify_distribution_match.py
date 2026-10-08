from itertools import combinations

import numpy as np
import pandas as pd
import pytest

from scripts.pcdr_verify_distribution_match import cdf_bounds, audit_members
from eigencircuits.controls import FULL_FEATURES


def test_bound_never_exceeds_exhaustive_optimum():
    values=np.array([[0.],[1.],[2.],[3.],[4.]])
    groups=['a','a','a','b','b'];counts={'a':1,'b':1}
    for target in [np.array([[0.],[1.]]),np.array([[1.],[3.]]),np.array([[5.],[5.]])]:
        result=cdf_bounds(values,groups,counts,target)[0]
        gaps=[]
        for a in range(3):
            for b in [3,4]:
                v=values[[a,b],0];t=target[:,0]
                gaps.append(max(abs((t<=p).mean()-(v<=p).mean()) for p in set(t)|set(v)))
        assert result['lower_bound'] <= min(gaps)+1e-12
    assert cdf_bounds(values,groups,counts,np.array([[5.],[5.]]))[0]['lower_bound']==1


def test_forced_members_and_tied_features():
    result=cdf_bounds([[0],[0],[2]],['a','a','b'],{'a':2,'b':1},[[1],[1],[2]])[0]
    assert result['lower_bound']==2/3
    assert result['threshold']==0


@pytest.mark.parametrize('values,groups,counts,target',[
    ([[0]],['a'],{'a':2},[[0],[1]]),
    ([[np.nan]],['a'],{'a':1},[[0]]),
    ([[0]],[],{'a':1},[[0]]),
    ([[0]],['a'],{'a':1},[]),
])
def test_invalid_bound_inputs(values,groups,counts,target):
    with pytest.raises(ValueError):cdf_bounds(values,groups,counts,target)


@pytest.mark.parametrize('fault',[None,'duplicate','target_member','float_id','wrong_stratum','overlap','mean'])
def test_independent_membership_rejections(fault):
    ids=[str(720575940100000000+i) for i in range(102)]
    frame=pd.DataFrame({name:np.tile(np.arange(51),2) for name in FULL_FEATURES},index=ids)
    frame['model_sign']='excitatory';frame['recruited']=True;frame['super_class']='central'
    candidate=ids[51:].copy();cap=51
    if fault=='duplicate':candidate[0]=candidate[1]
    elif fault=='target_member':candidate[0]=ids[0]
    elif fault=='float_id':candidate[0]=float(candidate[0])
    elif fault=='wrong_stratum':frame.loc[candidate[0],'model_sign']='inhibitory'
    elif fault=='overlap':cap=30
    elif fault=='mean':frame.loc[candidate,FULL_FEATURES]=10000
    if fault:
        with pytest.raises(ValueError):audit_members(candidate,frame,ids[:51],{('excitatory',True,False):51},{'test':ids[51:]},cap)
    else:
        result=audit_members(candidate,frame,ids[:51],{('excitatory',True,False):51},{'test':ids[51:]},cap)
        assert result['maximum_ecdf_gap']==0 and result['smd']==[0]*len(FULL_FEATURES)
