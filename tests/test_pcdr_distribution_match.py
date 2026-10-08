from itertools import combinations

import numpy as np
import pytest

from scripts.pcdr_distribution_match import solve, validate
from scripts.pcdr_verify_diverse import distribution_check


@pytest.mark.parametrize('cap,expected',[(None,0.),(0,.5),(1,.5)])
def test_matches_exhaustive_binary_optimum(cap, expected):
    values=np.array([[0.],[1.],[1.],[2.]])
    target=np.array([[0.],[2.]])
    refs=[np.array([1.,0.,0.,1.])]
    result,_=solve(values,['a']*4,{'a':2},target,np.ones(1),refs,cap,5)
    assert result.success
    selected,audit=validate(result.x,values,['a']*4,{'a':2},target,refs,cap)
    gaps=[]
    for ix in combinations(range(4),2):
        candidate=values[list(ix)]
        if cap is not None and refs[0][list(ix)].sum()>cap: continue
        if abs(candidate.mean()-target.mean())>.099*np.sqrt(target.var()/2):continue
        gaps.append(max(distribution_check(target,candidate)[2]))
    assert np.isclose(result.fun,min(gaps)) and np.isclose(result.fun,expected)
    assert audit['maximum_ecdf_gap']==expected and len(selected)==2


def test_infeasible_counts():
    result,_=solve(np.array([[0.],[2.]]),['a','b'],{'a':2},np.array([[0.],[2.]]),np.ones(1),[],None,5)
    assert result.status==2 and result.x is None


@pytest.mark.parametrize('fault',['fractional','wrong_count','wrong_mean','understated_cdf','overlap','nan'])
def test_rejects_invalid_incumbents(fault):
    values=np.array([[0.],[1.],[1.],[2.]])
    target=np.array([[0.],[2.]])
    refs=[np.array([1.,0.,0.,1.])]
    weights=np.array([0.,1.,1.,0.,.5]); cap=0
    if fault=='fractional':weights[:4]=.5
    elif fault=='wrong_count':weights[0]=1
    elif fault=='wrong_mean':weights[:4]=[0,0,1,1]
    elif fault=='understated_cdf':weights[-1]=.4
    elif fault=='overlap':weights[:4]=[1,0,0,1]
    else:weights[0]=np.nan
    with pytest.raises(ValueError):validate(weights,values,['a']*4,{'a':2},target,refs,cap)


def test_empty_and_nonfinite_rejected():
    for values in [np.empty((0,1)),np.array([[np.inf],[0.]])]:
        with pytest.raises(ValueError):solve(values,['a']*len(values),{'a':2},np.array([[0.],[2.]]),np.ones(1),[],None)
