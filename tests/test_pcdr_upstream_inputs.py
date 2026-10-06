import numpy as np
import pytest
from scripts.pcdr_upstream_inputs import contribution
from scripts.pcdr_first_spike import kernel


def test_same_tick_event_cannot_change_prethreshold_voltage():
    assert contribution([10,11],2.,10,.1)==0


def test_duplicate_arrivals_sum_and_sign_is_preserved():
    assert contribution([0,0,10],-3.,10,.1)==pytest.approx(-6*kernel(1.))


def test_empty_and_invalid_inputs():
    assert contribution([],3.,10,.1)==0
    for arrivals,weight,tick,dt in [([-1],1,2,.1),([],np.nan,2,.1),([],1,-1,.1),([],1,2,0),([],1,2,np.nan)]:
        with pytest.raises(ValueError):contribution(arrivals,weight,tick,dt)
