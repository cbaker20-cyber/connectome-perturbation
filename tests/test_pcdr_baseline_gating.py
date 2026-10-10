import pandas as pd
import pytest
from scripts.pcdr_baseline_gating import compare


def events(ticks):
    return pd.DataFrame({'source_id': ['9007199254740993']*len(ticks), 'tick': pd.Series(ticks, dtype='int64'), 'weight_mv': [1.]*len(ticks)})


def test_exact_match_release_and_spike_tick():
    joined, changed = compare(events([9,10,22009,22010]), events([9,10,22009,22010]), [10], [11])
    assert changed.tick.tolist() == [10,22010]
    assert changed.accept_coarse.tolist() == [False,True]
    assert changed.accept_fine.tolist() == [True,False]
    assert len(joined) == 4


def test_no_pairing_of_shifted_events_and_empty():
    joined, changed = compare(events([10]), events([11]), [10], [11])
    assert len(joined) == 2 and changed.empty
    assert compare(events([]), events([]), [], [])[0].empty


def test_bad_data():
    with pytest.raises(ValueError):compare(events([1,1]), events([1]), [], [])
    with pytest.raises(ValueError):compare(events([1]), events([1]), [2,1], [])
    altered=events([1]);altered['weight_mv']=2.
    with pytest.raises(ValueError):compare(events([1]), altered, [], [])
