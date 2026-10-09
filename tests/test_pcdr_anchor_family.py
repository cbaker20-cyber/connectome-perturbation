import pytest
import numpy as np
from scripts.pcdr_anchor_family import anchor_references
from scripts.pcdr_distribution_match import solve, validate


def test_anchor_addition_preserves_old_references():
    refs = {'old':['a','b']}
    new = anchor_references(['a','b','c','d'],refs,['c','d'],2,0)
    assert new == {'old':['a','b'],'fixed_anchor':['c','d']}
    assert refs == {'old':['a','b']}


@pytest.mark.parametrize('anchor', [['c','c'], ['c','missing'], ['a','b'], ['c',3]])
def test_invalid_anchor(anchor):
    with pytest.raises(ValueError):
        anchor_references(['a','b','c','d'],{'old':['a','b']},anchor,2,0)


def test_fixed_anchor_reduces_to_expected_partner():
    values = np.array([[0.],[1.],[1.],[2.]])
    target = np.array([[0.],[2.]])
    refs = [np.array([1,0,0,1])]
    result,_ = solve(values,['a']*4,{'a':2},target,np.ones(1),refs,0,5)
    selected,audit = validate(result.x,values,['a']*4,{'a':2},target,refs,0)
    assert result.success and selected.tolist() == [1,2]
    assert audit['maximum_ecdf_gap'] == .5
