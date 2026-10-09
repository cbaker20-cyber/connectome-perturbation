import numpy as np
import pytest
from itertools import product
from scripts.pcdr_baseline_time import counts_at, measures


def test_boundaries_and_empty():
    result = counts_at([0, .1, .999], [0, 0, 1], 2, [100, 999, 1000], .0001)
    assert result.tolist() == [[1, 0], [2, 0], [2, 1]]
    assert not counts_at([], np.array([], dtype=int), 2, [1000], .0002).any()


def test_known_cancellation_and_bound():
    a = np.array([[2, 0], [2, 4]])
    b = np.array([[0, 1], [1, 4]])
    result = measures(a, b)
    assert result[0] == dict(prefix_L1=3, interval_L1=3, final_L1=1, tail_L1=2,
        residual_after_arbitrary_tail_deletion_lower_bound=0)
    assert result[1]['prefix_L1'] == result[1]['residual_after_arbitrary_tail_deletion_lower_bound'] == 1


@pytest.mark.parametrize('t,cuts', [([1], [1000]), ([-.1], [1000]),
    ([float('nan')], [1000]), ([.00000015], [1000]), ([0], [100, 100]), ([0], [0])])
def test_bad_times(t, cuts):
    with pytest.raises(ValueError):
        counts_at(t, [0], 1, cuts, .0001)


def test_bad_indices():
    with pytest.raises(ValueError):
        counts_at([0], [-1], 1, [1000], .0001)


def test_tail_bound_against_all_deletions():
    for pa, pb, ta, tb in product(range(3), repeat=4):
        a, b = np.array([[pa], [pa + ta]]), np.array([[pb], [pb + tb]])
        bound = measures(a, b)[0]['residual_after_arbitrary_tail_deletion_lower_bound']
        actual_minimum = min(abs(pa + ta - da - pb - tb + db)
            for da in range(ta + 1) for db in range(tb + 1))
        assert 0 <= bound <= actual_minimum
