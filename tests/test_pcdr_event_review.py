import numpy as np
import pandas as pd
import pytest
from scripts.pcdr_event_review import bins, first_difference


def test_bins_boundaries_and_empty():
    result = bins([0., .009, .01, .999])
    assert result[0] == 2 and result[1] == 1 and result[99] == 1
    assert result.sum() == 4 and bins([]).sum() == 0
    for invalid in [[1.], [-.1], [np.nan]]:
        with pytest.raises(ValueError): bins(invalid)


def test_first_difference_uses_ids_and_times_not_row_order():
    a = pd.DataFrame({'t': [.01, .02], 'flywire_id': ['720575940660219265', '2']})
    assert first_difference(a, a.iloc[::-1]) is None
    b = a.copy(); b.loc[1, 'flywire_id'] = '3'
    assert first_difference(a, b) == 20.
    assert first_difference(a, a.iloc[:0]) == 10.
    assert first_difference(a.iloc[:0], a.iloc[:0]) is None
    with pytest.raises(ValueError, match='Duplicate'):
        first_difference(pd.concat([a, a]), b)
    b.loc[1, 't'] = .020001
    with pytest.raises(ValueError, match='grid'): first_difference(a, b)
