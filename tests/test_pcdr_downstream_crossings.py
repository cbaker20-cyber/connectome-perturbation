import numpy as np
import pytest
from scripts.pcdr_downstream_crossings import voltage


def test_single_impulse_and_current_tick_exclusion():
    expected=-52+2/3*(np.exp(-1/20)-np.exp(-1/5))
    assert voltage([0],[2],[],10,.1)==pytest.approx(expected)
    assert voltage([10],[2],[],10,.1)==-52


def test_reset_and_refractory_boundary():
    assert voltage([9,11],[2,2],[10],20,.1)==-52
    assert voltage([32],[2],[10],33,.1)>-52
    assert voltage([31],[2],[10],33,.1)==-52


def test_bad_inputs():
    with pytest.raises(ValueError):voltage([1],[np.nan],[],2,.1)
    with pytest.raises(ValueError):voltage([-1],[2],[],2,.1)
