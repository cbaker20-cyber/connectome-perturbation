import numpy as np
import pytest
from scipy.integrate import quad
from scripts.pcdr_first_spike import kernel


@pytest.mark.parametrize('lag',[0.,.8212,2.1892,47.9524])
def test_kernel_against_integral(lag):
    expected=quad(lambda s: np.exp(-s/5)*np.exp(-(lag-s)/20)/20,0,lag)[0]
    assert float(kernel(lag))==pytest.approx(expected,abs=1e-14)


@pytest.mark.parametrize('lag',[-1.,np.nan,np.inf])
def test_invalid_lag(lag):
    with pytest.raises(ValueError):kernel(lag)
