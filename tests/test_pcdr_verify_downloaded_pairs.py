import numpy as np
import pandas as pd
import pytest
from scripts.pcdr_verify_downloaded_pairs import compare, require


def test_known_response_difference_and_temporal_failure():
    a=pd.Series({'a':10.,'b':-10.})
    b=pd.Series({'a':10.,'b':-9.})
    pop=np.array([10,0])
    result=compare(a,b,['a'],[pop,pop],[pop,np.array([9,1])])
    assert result['A_difference_hz']==0
    assert result['response_relative_L1']==pytest.approx(1/19)
    assert result['F_difference']==pytest.approx(10/19-.5)
    assert result['population_relative_L1']==.2
    assert not result['passes']


def test_zero_response_does_not_pass_undefined_fraction():
    a=pd.Series({'a':0.})
    pop=np.zeros(100)
    assert not compare(a,a,['a'],[pop,pop],[pop,pop])['passes']
    with pytest.raises(ValueError,match='corrupted'):
        require(False,'corrupted')


def test_identical_nonzero_response_passes_with_sparse_ids():
    a=pd.Series({'a':10.})
    b=pd.Series({'a':10.,'b':0.})
    pop=np.array([10,0])
    assert compare(a,b,['a','c'],[pop,pop],[pop,pop])['passes']
