import numpy as np
import pytest
from scripts.pcdr_source_resets import segment


def test_reset_excludes_old_events_and_refractory_release_accepts_boundary():
    last, selected, gate = segment([8, 10, 11, 12, 13, 20], [10, 20], 20, 3)
    assert last == 10
    np.testing.assert_array_equal(selected, [11, 12, 13])
    np.testing.assert_array_equal(gate, [False, False, True])


def test_empty_arrivals_and_missing_or_unsorted_history():
    assert len(segment([], [10], 20, 3)[1]) == 0
    for post in [[], [20], [10, 5], [-1, 10]]:
        with pytest.raises(ValueError):
            segment([], post, 20, 3)
