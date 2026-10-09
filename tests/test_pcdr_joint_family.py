from itertools import combinations, product
import numpy as np
import pytest
from scripts.pcdr_joint_family import solve_pair, validate_pair
from scripts.pcdr_verify_diverse import distribution_check


@pytest.mark.parametrize('cap', [0, 1, 2])
def test_joint_optimum_against_exhaustive_pairs(cap):
    values = np.array([[0.], [1.], [1.], [2.]])
    target = np.array([[0.], [2.]])
    valid = [s for s in combinations(range(4), 2)
             if abs(values[list(s)].mean()-target.mean()) <= .099*np.sqrt(target.var()/2)]
    scores = [max(max(distribution_check(target, values[list(s)])[2]) for s in (a, b))
              for a, b in product(valid, repeat=2) if len(set(a) & set(b)) <= cap]
    result, _ = solve_pair(values, ['a']*4, {'a':2}, target, np.ones(1), [], cap, 5)
    assert result.success and np.isclose(result.fun, min(scores))
    _, audit = validate_pair(result.x, values, ['a']*4, {'a':2}, target, [], cap)
    assert audit['pairwise_overlap'] <= cap


def test_reference_constraints_can_make_joint_design_infeasible():
    result, _ = solve_pair(np.array([[0.], [1.], [1.], [2.]]), ['a']*4, {'a':2},
                           np.array([[0.], [2.]]), np.ones(1), [[1, 0, 0, 1]], 1, 5)
    assert result.status == 2 and result.x is None


@pytest.mark.parametrize('fault', ['fractional', 'intersection', 'overlap', 'cdf', 'nan'])
def test_invalid_joint_incumbents(fault):
    values = np.array([[0.], [1.], [1.], [2.]])
    x = np.array([1., 0, 0, 1, 0, 1, 1, 0, 0, 0, 0, 0, .5])
    if fault == 'fractional': x[0] = .5
    elif fault == 'intersection': x[8] = 1
    elif fault == 'overlap': x[4:8] = x[:4]
    elif fault == 'cdf': x[-1] = .4
    else: x[1] = np.nan
    with pytest.raises(ValueError):
        validate_pair(x, values, ['a']*4, {'a':2}, np.array([[0.], [2.]]), [], 0)


@pytest.mark.parametrize('fault', ['scale', 'reference', 'cap', 'strata', 'nonfinite'])
def test_invalid_design(fault):
    values = np.array([[0.], [2.]])
    scale, refs, cap, groups = np.ones(1), [], 1, ['a']*2
    if fault == 'scale': scale[0] = np.nan
    elif fault == 'reference': refs = [[1, .5]]
    elif fault == 'cap': cap = True
    elif fault == 'strata': groups = ['a', 'b']
    else: values[0, 0] = np.inf
    with pytest.raises(ValueError):
        solve_pair(values, groups, {'a':2}, np.array([[0.], [2.]]), scale, refs, cap, 5)
