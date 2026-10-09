import numpy as np
import pytest
from scripts.pcdr_expand_distribution_pool import nested_pool


def test_nested_pool_exact_ids_strata_and_ties():
    ids=np.array([str(720575940100000000+i) for i in [0,2,1,3,4]])
    values=np.array([[0.],[1.],[-1.],[2.],[0.]])
    args=(ids,values,[0],np.array([1,2,3,4]),['a','a','a','a','b'],np.ones(1),{'old':[ids[3]]})
    small=nested_pool(*args,1)
    large=nested_pool(*args,3)
    assert small==sorted([ids[2],ids[3]])
    assert set(small)<set(large)
    assert ids[4] not in large and ids[0] not in large


@pytest.mark.parametrize('count',[0,-1,True,2.5])
def test_invalid_count(count):
    with pytest.raises(ValueError):nested_pool(np.array(['1','2']),np.array([[0.],[1.]]),[0],np.array([1]),['a','a'],np.ones(1),{},count)


def test_rejects_ineligible_reference_and_duplicate_ids():
    args=[np.array(['1','2']),np.array([[0.],[1.]]),[0],np.array([1]),['a','a'],np.ones(1),{'old':['1']},1]
    with pytest.raises(ValueError,match='ineligible'):nested_pool(*args)
    args[0]=np.array(['1','1']);args[6]={}
    with pytest.raises(ValueError,match='IDs'):nested_pool(*args)
