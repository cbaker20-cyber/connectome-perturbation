import pytest
from scripts.pcdr_baseline_count_replay import select_event


def test_checkpoint_gap_and_ties():
    a = {'input': [1, 2, 3], 'a': [10, 20], 'b': [10, 20, 30]}
    b = {'a': [10], 'b': [10]}
    assert select_event(a, b, ['input']) == dict(target_id='b', end_ms=100,
        stop_tick=1000000, coarse_count=3, fine_count=1, absolute_gap=2)
    assert select_event({'b': [1, 2], 'a': [1, 2]}, {}, [])['target_id'] == 'a'


def test_half_open_boundary_and_absence():
    assert select_event({'a': [999999, 1000000]}, {}, [])['end_ms'] == 200
    assert select_event({'a': [1]}, {}, []) is None
    assert select_event({}, {}, []) is None


@pytest.mark.parametrize('ticks', [[3, 2], [2, 2], [-1], [1.5]])
def test_invalid(ticks):
    with pytest.raises(ValueError):
        select_event({'a': ticks}, {}, [])
