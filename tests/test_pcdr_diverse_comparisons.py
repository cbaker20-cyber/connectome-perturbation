import numpy as np

from scripts.pcdr_diverse_comparisons import solve


def test_minimizes_overlap_subject_to_feature_balance():
    values = np.array([[0.], [1.], [2.], [3.]])
    result, _ = solve(values, ['a']*4, {'a':2}, np.array([1.5]), np.array([0.]), np.array([1.]), [1,1,0,0])
    assert result.success
    assert np.isclose(result.x.sum(),2)
    assert np.isclose(result.x @ values[:,0]/2,1.5)
    # The two new cells alone have mean 2.5 and cannot satisfy the fixed target.
    assert np.isclose(result.fun, 2/3)


def test_reports_infeasible_feature_requirement():
    result, _ = solve(np.zeros((4,1)), ['a']*4, {'a':2}, np.array([2.]), np.array([0.]), np.array([1.]), [1,1,0,0])
    assert not result.success and result.x is None
