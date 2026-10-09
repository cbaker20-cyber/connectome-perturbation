from itertools import combinations

import numpy as np
import pytest

from scripts.pcdr_family_capacity import capacity, clique_capacity


def test_every_threshold_against_direct_subsets():
    sets = [{1, 2, 3}, {2, 3, 4}, {4, 5, 6}, {1, 5, 6}]
    gaps = np.array([0, 1, 2, 3])
    overlap = np.array([[len(a & b) for b in sets] for a in sets])
    best, witnesses = capacity(gaps, overlap, 3)
    for g in range(4):
        for cap in range(4):
            valid = [subset for n in range(5) for subset in combinations(range(4), n)
                     if all(gaps[i] <= g for i in subset)
                     and all(overlap[i, j] <= cap for i, j in combinations(subset, 2))]
            expected = max(map(len, valid))
            assert best[g, cap] == expected == clique_capacity(gaps, overlap, g, cap)
            witness = tuple(i for i in range(4) if int(witnesses[g, cap]) & (1 << i))
            assert witness in valid and len(witness) == expected


def test_empty_and_singleton():
    best, _ = capacity(np.array([], dtype=int), np.empty((0, 0), dtype=int), 3)
    assert not best.any()
    best, _ = capacity(np.array([2]), np.array([[3]]), 3)
    assert best[1, 3] == 0 and best[2, 0] == 1


@pytest.mark.parametrize('gaps,overlap', [
    ([1.5], [[3]]), ([4], [[3]]), ([-1], [[3]]), ([1], [[2]]),
    ([1, 2], [[3, 1], [2, 3]]), ([1, 2], [[3, 4], [4, 3]]),
    ([1, 2], [[3]]), ([1]*21, np.eye(21, dtype=int)*3),
])
def test_invalid_counts_and_budget(gaps, overlap):
    with pytest.raises(ValueError):
        capacity(np.array(gaps), np.array(overlap), 3)
