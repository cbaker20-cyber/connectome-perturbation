import numpy as np
import pytest
from scripts.pcdr_verify_diverse import distribution_check


def test_distribution_differences_despite_equal_means():
    smd,ratio,gap=distribution_check([[0],[2]],[[1],[1]])
    assert smd.tolist()==[0] and ratio==[0] and gap==[.5]


def test_constant_equal_and_different_features():
    smd,ratio,gap=distribution_check([[1],[1]],[[2],[2]])
    assert np.isinf(smd[0]) and ratio==[None] and gap==[1]
    assert distribution_check([[1],[1]],[[1],[1]])[0].tolist()==[0]


@pytest.mark.parametrize('candidate',[[],[[np.nan],[1]],[[1],[2],[3]]])
def test_invalid_feature_tables(candidate):
    with pytest.raises(ValueError):distribution_check([[0],[2]],candidate)
