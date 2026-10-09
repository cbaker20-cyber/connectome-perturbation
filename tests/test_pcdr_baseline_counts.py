import numpy as np
import pytest
from scripts.pcdr_baseline_counts import partition


def test_partition_known_counts():
    result = partition([0, 3, 0, 4, 2, 0], [0, 0, 5, 1, 2, 0])
    assert result == dict(coarse_active=3, fine_active=3, coarse_only_cells=1,
        fine_only_cells=1, shared_changed_cells=1, coarse_only_L1=3,
        fine_only_L1=5, shared_active_L1=3, total_L1=11)


def test_silent_and_unchanged():
    assert partition([0, 0], [0, 0])['total_L1'] == 0
    assert partition([2, 3], [2, 3])['shared_changed_cells'] == 0


def test_unsigned_subtraction_and_large_sum():
    a = np.array([0, 2**63], dtype=np.uint64)
    b = np.array([2**63, 0], dtype=np.uint64)
    assert partition(a, b)['total_L1'] == 2**64


@pytest.mark.parametrize('a,b', [([], []), ([1], [1, 2]), ([-1], [0]),
    ([1.5], [0]), ([float('nan')], [0]), ([[1]], [[1]])])
def test_invalid_counts(a, b):
    with pytest.raises(ValueError):
        partition(a, b)
