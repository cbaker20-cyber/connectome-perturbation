from itertools import product
import numpy as np
import pytest
from scripts.pcdr_anchor_bound import box_dual_bound


def test_bound_against_all_feasible_box_vertices():
    c=np.array([1.,2.,3.]);a=np.array([[1.,0.,1.]]);b=np.array([1.])
    eq=np.array([[1.,1.,1.]]);rhs=np.array([1.])
    optimum=min(c@x for x in map(np.array,product([0,1],repeat=3)) if np.all(a@x<=b) and np.all(eq@x==rhs))
    for y,z in product([-100.,-1.,0.,1.],repeat=2):
        result=box_dual_bound(c,a,b,eq,rhs,[y],[z])
        assert result['guarded_lower_bound']<=optimum
    assert np.isclose(box_dual_bound(c,a,b,eq,rhs,[0],[1])['raw_lower_bound'],optimum)


def test_box_residual_correction_prevents_false_bound():
    r=box_dual_bound([1],np.empty((0,1)),[],[[1]],[1],[],[100])
    assert r['raw_lower_bound']==1 and r['guarded_lower_bound']<1


@pytest.mark.parametrize('y', [[float('nan')], [0,0]])
def test_rejects_bad_certificate(y):
    with pytest.raises(ValueError):box_dual_bound([1],[[1]],[1],[[1]],[1],y,[1])
