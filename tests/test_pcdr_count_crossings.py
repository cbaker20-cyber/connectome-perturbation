import numpy as np
import pytest
from scripts.pcdr_count_crossings import first_gap, state


def test_first_gap_and_simultaneous():
    assert first_gap([1, 2, 3], [2]) == dict(tick=3,coarse_minus_fine=2,leader='coarse')
    assert first_gap([2], [1, 2, 3])['leader'] == 'fine'
    assert first_gap([1, 3], [2, 4]) is None
    assert first_gap([], []) is None
    with pytest.raises(ValueError):first_gap([2,1], [])


def test_reset_release_and_current_arrival():
    arrivals=np.array([10,22009,22010,22011]);weights=np.array([100.,100.,3.,100.])
    r=state(arrivals,weights,[10],22011)
    assert r['accepted_since_reset']==1 and r['blocked_since_reset']==1
    assert r['ready'] and -52<r['voltage_mv']<-51
    assert state(arrivals,weights,[10],22009)['voltage_mv']==-52


def test_silent_initial_state():
    r=state(np.array([],dtype=int),np.array([]),[],0)
    assert r['voltage_mv']==-52 and r['ready'] and r['last_reset_tick'] is None
