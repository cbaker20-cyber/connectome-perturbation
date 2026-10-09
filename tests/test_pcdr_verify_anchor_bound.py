from fractions import Fraction
import numpy as np
import pytest
from scripts.pcdr_verify_anchor_bound import rational_bound


def test_exact_residual_and_sign():
    c=np.array([1.,2.]);a=np.array([[1.,0.]]);eq=np.array([[1.,1.]])
    assert rational_bound(c,a,[1],eq,[1],[0],[1])==Fraction(1)
    assert rational_bound(c,a,[1],eq,[1],[0],[100])==Fraction(-97)
    with pytest.raises(ValueError):rational_bound(c,a,[1],eq,[1],[1],[1])
