import numpy as np
import pytest
from scipy.sparse import csr_matrix
from scripts.pcdr_input_reconstruction import delayed_input, eligibility


def test_delay_signed_sums_and_end_of_trial():
    weights=csr_matrix([[2.,-3.]])
    raster=csr_matrix([[1.,0.,1.,0.],[1.,1.,0.,1.]])
    np.testing.assert_array_equal(delayed_input(weights,raster,1),[[0.,-1.,-3.,2.]])
    np.testing.assert_array_equal(delayed_input(weights,raster,0),[[-1.,-3.,2.,-3.]])
    assert not delayed_input(weights,raster,4).any()
    with pytest.raises(ValueError):delayed_input(weights,raster,-1)


def test_refractory_mask_includes_spike_tick_but_not_recovery_tick():
    np.testing.assert_array_equal(eligibility([2,7],10,3),[1,1,0,0,0,1,1,0,0,0])
    assert eligibility([],5,2).all()
    with pytest.raises(ValueError):eligibility([5],5,2)
    with pytest.raises(ValueError):eligibility([],5,0)
