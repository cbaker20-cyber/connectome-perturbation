import numpy as np
import pandas as pd
import pytest
from scripts.pcdr_agreement_breakdown import components


def data():
    key = dict(variant='default', condition='mode', seed=1)
    agreement = pd.DataFrame([dict(**key, coarse_ms=.0002, fine_ms=.0001, A_difference_hz=1.,
        F_difference=.01, response_relative_L1=.05, population_relative_L1=.05,
        passes_response=True, passes=True)])
    pairs = pd.DataFrame([dict(**key, dt_ms=.0001, A=10.)])
    return agreement, pairs


def test_inclusive_boundaries_and_undefined_fraction():
    a, p = data()
    assert components(a, p)[0]['passes'] == 1
    a.loc[0, ['F_difference','passes_response','passes']] = [np.nan,False,False]
    assert components(a, p)[0]['F_pass'] == 0
    assert components(a, p)[0]['vector_pass'] == 1


def test_missing_duplicate_and_conflicting_evidence():
    a, p = data()
    for first, second in [(a,p.iloc[:0]), (pd.concat([a,a]),p), (a,pd.concat([p,p]))]:
        with pytest.raises(ValueError): components(first,second)
    a.loc[0,'passes'] = False
    with pytest.raises(ValueError, match='decisions'): components(a,p)
