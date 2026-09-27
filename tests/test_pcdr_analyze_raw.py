import numpy as np
from scipy import sparse
from scripts.pcdr_analyze_raw import resampled_metrics, vector_comparison


def test_resamples_average_signed_vectors_before_absolute_values():
    delta = np.array([[2., -3., 0.], [-2., 1., 0.]])
    weights = np.array([[.5, .5], [1., 0.], [0., 1.]])
    a, f = resampled_metrics(sparse.csr_matrix(delta), [0], weights)
    np.testing.assert_allclose(a, [0., 2., 2.])
    np.testing.assert_allclose(f, [0., .4, 2/3])
    # Adding zero columns must not change either endpoint.
    extra = np.pad(delta, ((0, 0), (0, 10)))
    aa, ff = resampled_metrics(sparse.csr_matrix(extra), [0], weights)
    np.testing.assert_array_equal(a, aa)
    np.testing.assert_array_equal(f, ff)


def test_zero_responses_have_undefined_fraction():
    a, f = resampled_metrics(sparse.csr_matrix((2, 3)), [0, 1], np.array([[.5, .5]]))
    assert a[0] == 0 and np.isnan(f[0])


def test_shared_seed_weights_preserve_a_constant_paired_difference():
    weights = np.array([[1., 0.], [.5, .5], [0., 1.]])
    mode = sparse.csr_matrix([[3., 0.], [13., 0.]])
    comparison = sparse.csr_matrix([[1., 0.], [11., 0.]])
    a, _ = resampled_metrics(mode, [0], weights)
    b, _ = resampled_metrics(comparison, [0], weights)
    np.testing.assert_array_equal(a - b, [2., 2., 2.])


def test_signed_spatial_comparison_and_zero_norm():
    value = vector_comparison([2., -1., 0.], [1., -1., 3.], [0, 1])
    assert value['difference_total_abs_hz'] == 4.
    assert value['difference_mode_abs_hz'] == 1.
    assert value['difference_relative_to_first_l1'] == 4/3
    assert np.isclose(value['signed_cosine'], 3/np.sqrt(55))
    value = vector_comparison([0., 0.], [1., 0.], [0])
    assert value['signed_cosine'] is None and value['difference_relative_to_first_l1'] is None
