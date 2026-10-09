import pytest
from scripts.pcdr_baseline_events import select_event


def test_threshold_exclusion_and_tie():
    a = {'input': [1], 'b': [10, 30], 'a': [10, 30], 'c': [4]}
    b = {'input': [8], 'b': [13, 30], 'a': [13, 30], 'c': [6]}
    assert select_event(a, b, ['input']) == dict(first_tick=10, target_id='a', ordinal=0, coarse_tick=10, fine_tick=13)


def test_no_selection_and_unpaired_tail():
    assert select_event({'a': [2, 20]}, {'a': [3]}, []) is None
    assert select_event({}, {}, []) is None


@pytest.mark.parametrize('ticks', [[3, 2], [2, 2], [-1], [1.5]])
def test_invalid(ticks):
    with pytest.raises(ValueError):
        select_event({'a': ticks}, {'a': [1]}, [])
