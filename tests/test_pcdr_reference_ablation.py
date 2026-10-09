import numpy as np
import pytest
from scipy.optimize import linprog
from scripts.pcdr_reference_ablation import reference_groups
from scripts.pcdr_anchor_bound import matrices


def test_complete_factorial_partition():
    refs={k:[str(i)] for i,k in enumerate(['motor_003','motor_004','motor_005']+['new_'+str(j) for j in range(12)])}
    groups=reference_groups(refs)
    assert list(map(len,groups.values()))==[0,3,12,15]
    assert set(groups['original_three']).isdisjoint(groups['newer_twelve'])
    assert groups['both']==refs


@pytest.mark.parametrize('change',['missing','extra'])
def test_rejects_wrong_inventory(change):
    refs={k:[] for k in ['motor_003','motor_004','motor_005']+['new_'+str(j) for j in range(12)]}
    if change=='missing':del refs['new_0']
    else:refs['unknown']=[]
    with pytest.raises(ValueError):reference_groups(refs)


def test_no_reference_matrix_retains_means_and_counts():
    values=np.array([[0.],[1.],[1.],[2.]])
    a,b,eq,rhs=matrices(values,['a']*4,{'a':2},np.array([[0.],[2.]]),np.ones(1),[])
    assert a.shape==(2,4) and eq.shape==(1,4)
    r=linprog([1,0,0,1],A_ub=a,b_ub=b,A_eq=eq,b_eq=rhs,bounds=(0,1),method='highs')
    assert r.success and r.fun==0
