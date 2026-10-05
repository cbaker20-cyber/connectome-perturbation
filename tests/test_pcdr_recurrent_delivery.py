import numpy as np
import pytest
from scripts.pcdr_recurrent_delivery import accepted


def test_arrivals_before_during_and_at_release():
    np.testing.assert_array_equal(accepted([0,10,11,31,32,33],[10],22),[True,False,False,False,True,True])


def test_zero_refractory_still_blocks_same_spike_tick():
    np.testing.assert_array_equal(accepted([9,10,11],[10],0),[True,False,True])


def test_latest_spike_controls_refractory_period():
    np.testing.assert_array_equal(accepted([39,40,41,62],[10,40],22),[True,False,False,True])


def test_empty_train_and_unsorted_train():
    assert accepted([0,10],[],22).all()
    assert len(accepted([],[],22))==0
    with pytest.raises(ValueError):accepted([15],[20,10],22)
