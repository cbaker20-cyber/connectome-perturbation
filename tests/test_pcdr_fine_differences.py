import numpy as np
import pytest
from scripts.pcdr_fine_differences import binned, distances, first_bin, phase_counts


def test_bins_preserve_neuron_identity_and_boundary():
    m = binned(np.array([0., .009, .010, .999]), np.array([0, 0, 1, 1]), 2)
    assert m[0, 0] == 2
    assert m[1, 1] == 1
    assert m[99, 1] == 1
    assert m.sum() == 4


def test_equal_population_can_hide_different_cells():
    a = binned(np.array([.1]), np.array([0]), 2)
    b = binned(np.array([.1]), np.array([1]), 2)
    assert (a-b).sum() == 0
    assert abs(a-b).sum() == 2


def test_empty_spikes_have_no_difference():
    assert binned(np.array([]), np.array([], dtype=int), 2).sum() == 0
    assert first_bin(np.zeros(100), 10) is None


@pytest.mark.parametrize('t,c', [([1.], [0]), ([-.1], [0]), ([np.nan], [0]), ([.1], [-1]), ([.1], [2]), ([.1], [0.5])])
def test_invalid_spikes_rejected(t,c):
    with pytest.raises(ValueError):
        binned(np.array(t), np.array(c), 2)


def test_distances_use_paired_rows_and_each_seed_pair_once():
    fine = np.array([[0., 0.], [3., -1.], [1., 1.]])
    coarse = fine + np.array([[1., 0.], [0., 2.], [-1., 0.]])
    within, between = distances(coarse, fine)
    np.testing.assert_array_equal(within, [1, 2, 1])
    np.testing.assert_array_equal(between, [4, 2, 4])
    with pytest.raises(ValueError):
        distances(coarse[:1], fine[:1])


def test_phase_boundary_belongs_to_following_window():
    result = phase_counts(np.array([0., .6, .65, .999]), np.array([0, 0, 1, 1]), 2, [0, .6, .65, 1])
    np.testing.assert_array_equal(result.toarray(), [[1, 0], [1, 0], [0, 2]])
    with pytest.raises(ValueError):
        phase_counts(np.array([]), np.array([], dtype=int), 2, [0, .6, .5, 1])
