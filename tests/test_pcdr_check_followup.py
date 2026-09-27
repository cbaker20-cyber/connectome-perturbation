import numpy as np
import pytest
from scripts.pcdr_check_followup import same


def test_nested_results_and_undefined_fraction():
    same({'result': {'A': 0., 'F': None}}, {'result': {'A': 0., 'F': None}, 'note': 'retained'})
    same({'F': None}, {'F': np.nan})
    with pytest.raises(ValueError): same({'F': None}, {'F': 0.})
    with pytest.raises(ValueError): same({'A': 1.}, {'A': 1.1})
    with pytest.raises(ValueError): same({'A': 1.}, {})
    with pytest.raises(ValueError): same({'A': 1.}, {'A': np.nan})
