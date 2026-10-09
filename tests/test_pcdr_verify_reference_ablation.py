import pytest
from scripts.pcdr_verify_reference_ablation import expected_names


def test_regime_reconstruction():
    refs={'motor_003':[], 'new_7':[], 'motor_005':[], 'motor_004':[]}
    assert expected_names('neither',refs)==[]
    assert expected_names('original_three',refs)==['motor_003','motor_005','motor_004']
    assert expected_names('newer_twelve',refs)==['new_7']
    assert expected_names('both',refs)==list(refs)
    with pytest.raises(ValueError):expected_names('unknown',refs)
