import numpy as np
import pandas as pd
import pytest

from scripts.pcdr_review_pathway import spike_counts


def test_window_boundaries_and_prior_recruitment():
    frame = pd.DataFrame({'t': [.1, .1001, .649, .650, .652, .729, .730],
                          'flywire_id': ['input', 'input', 'a', 'b', 'a', 'b', 'c']})
    counts, _ = spike_counts(frame, ['input'], .0002, {'input', 'a', 'b', 'c'})
    assert counts == dict(noninput_spikes_650_730=3, newly_recruited_noninput_650_730=1)


@pytest.mark.parametrize('times,ids,message', [
    ([.1, .1], ['a', 'a'], 'Duplicate'),
    ([.1, .1001], ['a', 'a'], 'refractory'),
    ([.1000001], ['a'], 'Off-grid'),
    ([np.nan], ['a'], 'Invalid'),
    ([.75], ['a'], 'Invalid'),
    ([.2, .1], ['a', 'b'], 'Unsorted'),
    ([.1], ['unknown'], 'Unknown'),
    ([.1], [720575940628695043.0], 'strings'),
])
def test_invalid_spikes(times, ids, message):
    with pytest.raises(ValueError, match=message):
        spike_counts(pd.DataFrame({'t': times, 'flywire_id': ids}), [], .0002, {'a', 'b'})


def test_empty_spikes():
    counts, _ = spike_counts(pd.DataFrame({'t': pd.Series(dtype=float),
                                          'flywire_id': pd.Series(dtype=str)}), [], .0002, set())
    assert counts == dict(noninput_spikes_650_730=0, newly_recruited_noninput_650_730=0)
