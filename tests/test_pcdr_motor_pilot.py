import numpy as np
from scripts.pcdr_verify_motor_pilot import contrast_interval


def test_contrast_bootstrap_uses_shared_seeds_and_averages_before_absolute():
    d = np.array([[3., -1., 0.], [-3., 1., 0.], [2., -4., 0.]])
    result = contrast_interval(d, d.copy(), [0], [0], n=100)
    assert result['A_difference_95pct'] == [0., 0.]
    assert result['F_difference_95pct'] == [0., 0.]
    constant = np.tile([2., -1., 3.], (3, 1))
    other = np.tile([1., -1., 0.], (3, 1))
    result = contrast_interval(constant, other, [0], [0], n=100)
    np.testing.assert_allclose(result['A_difference_95pct'], [1., 1.])
    np.testing.assert_allclose(result['F_difference_95pct'], [-1/6, -1/6])


def test_zero_response_concentration_is_undefined():
    result = contrast_interval(np.zeros((3, 4)), np.ones((3, 4)), [0], [1], n=100)
    assert result['F_difference_95pct'] is None
    assert result['undefined_F_resamples'] == 100


def test_opposite_signed_seed_responses_cancel_before_taking_absolute():
    mode = np.array([[2., 0.], [-2., 0.]])
    other = np.array([[1., 0.], [1., 0.]])
    result = contrast_interval(mode, other, [0], [0])
    # One copy of each mode seed gives A=0; two equal seeds give A=2.
    # Averaging absolute single-seed responses would incorrectly give A=2 always.
    np.testing.assert_allclose(result['A_difference_95pct'], [-1., 1.])
    assert 0 < result['undefined_F_resamples'] < result['resamples']
