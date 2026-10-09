import pytest
from scripts.pcdr_verify_joint_family import classify


@pytest.mark.parametrize('status,candidate,objective,bound,expected', [
    (0, True, .2, .2, 'verified_optimal_pair'),
    (1, True, .3, .1, 'verified_feasible_pair_optimality_unresolved'),
    (1, False, None, .1, 'time_limit_without_incumbent'),
    (2, False, None, None, 'solver_reported_restricted_infeasibility'),
    (4, False, None, None, 'solver_failure'),
])
def test_status_interpretation(status, candidate, objective, bound, expected):
    assert classify(status, candidate, objective, bound) == expected


@pytest.mark.parametrize('args', [
    (0, False, None, None), (0, True, .2, .1), (2, True, .2, .2),
    (1, False, .2, .1), (1, True, .2, .3), (1, True, float('nan'), .1),
    (0, True, .2, None), (7, False, None, None),
])
def test_rejects_inconsistent_records(args):
    with pytest.raises(ValueError): classify(*args)
