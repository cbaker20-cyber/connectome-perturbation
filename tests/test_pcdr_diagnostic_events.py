import numpy as np
import pytest
from scripts.pcdr_diagnostic_events import advance, compare


def test_undriven_relaxation_and_refractory_freeze():
    v,g=advance(np.array([-42.,-42.]),np.array([0.,3.]),np.array([True,False]),20.)
    np.testing.assert_allclose(v,[-52+10/np.e,-42])
    np.testing.assert_array_equal(g,[0,3])


def test_synaptic_drive_integral():
    v,g=advance(np.array([-52.]),np.array([3.]),np.array([True]),1.)
    # Independently integrate the exponentially decaying input contribution.
    from scipy.integrate import quad
    contribution=quad(lambda t: 3*np.exp(-t/5)*np.exp(-(1-t)/20)/20,0,1)[0]
    np.testing.assert_allclose(v,[-52+contribution],rtol=0,atol=1e-13)
    np.testing.assert_allclose(g,[3*np.exp(-.2)])


def test_mismatch_and_nonfinite_rejected():
    for value in [1.,np.nan,np.inf]:
        with pytest.raises(ValueError):compare(np.array([value]),np.array([0.]),'fixture')
