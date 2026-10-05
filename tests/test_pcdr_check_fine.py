import numpy as np
import pytest

from scripts.pcdr_check_fine import comparison, same


def test_identical_nonzero_response_passes():
    result = comparison(np.array([2., -1.]), np.array([2., -1.]), [0])
    assert result['passes_response']
    assert result['response_relative_L1'] == 0


def test_equal_footprints_do_not_hide_changed_response():
    result = comparison(np.array([2., -1.]), np.array([-2., 1.]), [0])
    assert result['A_difference_hz'] == 0
    assert result['F_difference'] == 0
    assert result['response_relative_L1'] == 2
    assert not result['passes_response']


def test_zero_response_has_undefined_fraction_and_fails():
    result = comparison(np.zeros(2), np.zeros(2), [0])
    assert result['F_difference'] is None
    assert not result['passes_response']


def test_finer_response_sets_relative_denominator():
    result = comparison(np.array([4., 0.]), np.array([2., 0.]), [0])
    assert result['response_relative_L1'] == 1
    assert not result['passes_response']


@pytest.mark.parametrize('saved', [{}, {'A': 3.}, {'A': float('nan')}])
def test_missing_changed_or_nonfinite_result_rejected(saved):
    with pytest.raises(ValueError):
        same({'A': 2.}, saved)


def test_undefined_csv_value_is_accepted_but_defined_value_is_not():
    same({'F': None}, {'F': float('nan')})
    with pytest.raises(ValueError):
        same({'F': None}, {'F': 0.})
