import numpy as np
import pytest
from scripts.pcdr_history_parts import split_events


def test_two_matching_rules():
    assert [x.tolist() for x in split_events([1, 5, 9], [2, 7], 'first')] == [[1, 5], [2, 7], [9], []]
    assert [x.tolist() for x in split_events([1, 5, 9], [2, 7], 'last')] == [[5, 9], [2, 7], [1], []]


def test_empty_and_reconstruction():
    for rule in ('first', 'last'):
        for a, b in [([], []), ([], [2]), ([1, 5], [3]), ([2], [1, 5])]:
            ca, fb, ec, ef = split_events(a, b, rule)
            assert sorted(np.r_[ca, ec].tolist()) == a
            assert sorted(np.r_[fb, ef].tolist()) == b
            assert len(ca) == len(fb)


@pytest.mark.parametrize('a,b,rule', [([2, 1], [], 'first'), ([1, 1], [], 'last'),
    ([-1], [], 'first'), ([1.5], [], 'first'), ([1], [], 'unknown')])
def test_invalid(a, b, rule):
    with pytest.raises(ValueError):
        split_events(a, b, rule)
