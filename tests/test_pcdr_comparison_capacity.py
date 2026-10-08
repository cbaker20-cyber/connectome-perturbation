from itertools import combinations

import pytest

from scripts.pcdr_comparison_capacity import overlap_bounds


def test_overlap_bounds_against_all_small_subsets():
    for n in range(7):
        for k in range(n+1):
            candidates = [set(v) for v in combinations(range(n), k)]
            for r in range(n+1):
                reference = set(range(r))
                bounds = overlap_bounds(n, k, r)
                assert bounds['minimum_with_reference'] == min(len(s & reference) for s in candidates)
                assert bounds['minimum_between_two_sets'] == min(len(a & b) for a in candidates for b in candidates)


@pytest.mark.parametrize('args', [(-1,0,0),(2,3,1),(2,1,3),(2,-1,0),(2.,1,1),(2,True,1)])
def test_invalid_counts(args):
    with pytest.raises(ValueError): overlap_bounds(*args)
