import numpy as np
import pandas as pd
import pytest

from scripts.pcdr_review_pathway import spike_counts, validate_switch


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


@pytest.mark.parametrize('remove', [False, True])
def test_switch_record_and_invalid_changes(remove):
    from copy import deepcopy
    ids = ['720575940628695043','720575940629667639','720575940623862015']
    connections = pd.DataFrame({'Presynaptic_Index':[0,0], 'Postsynaptic_Index':[1,2],
                                'Excitatory x Connectivity':[286,237]})
    before = [94.38,78.21]
    valid = dict(switch_ms=600, remove=remove, pairs=[[0,1],[0,2]],
                 weights_before_mv=before, weights_after_mv=[0.,0.] if remove else before)
    validate_switch(valid, remove, ids, connections)
    for key, bad in [('switch_ms',599), ('remove',not remove), ('pairs',[[0,2],[0,1]]),
                     ('weights_before_mv',[94.,78.21]), ('weights_after_mv',[1.,1.]),
                     ('pairs',[[0.0,1],[0,2]])]:
        altered = deepcopy(valid); altered[key] = bad
        with pytest.raises(ValueError): validate_switch(altered, remove, ids, connections)
    with pytest.raises(ValueError):
        validate_switch(valid,remove,ids,pd.concat([connections,connections.iloc[:1]]))
