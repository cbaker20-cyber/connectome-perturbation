import pandas as pd
import pytest
from scripts.pcdr_pathway_trial import endpoints, worker


def test_window_boundaries_and_prior_recruitment():
    spikes = pd.DataFrame({'flywire_id': ['a','a','b','b','c','input'],
                           't': [.6499,.65,.65,.7299,.73,.7]})
    result = endpoints(spikes, ['input'], .0004)
    assert result['noninput_spikes_650_730'] == 3
    assert result['newly_recruited_noninput_650_730'] == 1
    assert endpoints(spikes.iloc[:0], [], .0004)['newly_recruited_noninput_650_730'] == 0


def test_floating_representation_does_not_move_boundary_tick():
    spikes = pd.DataFrame({'flywire_id': ['a', 'b'], 't': [.65-1e-16, .73-1e-16]})
    assert endpoints(spikes, [], .0004)['noninput_spikes_650_730'] == 1


def test_unplanned_trial_rejected_before_io(tmp_path):
    with pytest.raises(ValueError, match='declared'):
        worker(tmp_path/'missing', tmp_path/'out', .1, 'reference', 750)
    assert not (tmp_path/'out').exists()
