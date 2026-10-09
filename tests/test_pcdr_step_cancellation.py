import pytest
from scripts.pcdr_step_cancellation import decompose


def test_known_signed_components():
    r=decompose([2,-3,0,4,1],[2,1,5,0,3])
    assert r['baseline_L1']==10 and r['lesion_L1']==11
    assert r['response_L1']==15 and r['cancelled_L1']==6
    assert r['exact_cancellation_neurons']==1 and r['opposite_direction_neurons']==1
    assert r['baseline_only_neurons']==r['lesion_only_neurons']==1


def test_zero_and_complete_cancellation():
    assert decompose([0],[0])['cancelled_fraction'] is None
    assert decompose([2,-3],[2,-3])['cancelled_fraction']==1


@pytest.mark.parametrize('a,b',[([],[]),([1],[1,2]),([float('nan')],[1]),([[1]],[[1]])])
def test_invalid(a,b):
    with pytest.raises(ValueError):decompose(a,b)
