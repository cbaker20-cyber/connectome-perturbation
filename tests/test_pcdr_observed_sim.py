import numpy as np
import pandas as pd
import pytest
from scripts.pcdr_followup_sim import simulate as original
from scripts.pcdr_observed_sim import simulate


@pytest.mark.parametrize('dt', [.0125, .00625])
@pytest.mark.parametrize('lesion', [[], [1]])
def test_recording_preserves_all_events_and_exposes_threshold_state(tmp_path, dt, lesion):
    comp, con = tmp_path / 'comp.csv', tmp_path / 'con.parquet'
    pd.DataFrame({'Completed': [1, 1, 1]}, index=[101, 102, 103]).to_csv(comp)
    pd.DataFrame({'Presynaptic_Index': [0, 1], 'Postsynaptic_Index': [1, 2],
                  'Excitatory x Connectivity': [150., -30.]}).to_parquet(con)
    tape = np.zeros((round(20/dt), 1), dtype=np.int8)
    tape[np.rint(np.array([1., 5., 9., 13.])/dt).astype(int), 0] = 1
    kwargs = dict(tape=tape, duration_s=.02, dt_ms=dt, completeness=comp,
                  connectivity=con, return_delivered=True)
    expected = original(42, [0], lesion, **kwargs)
    actual = simulate(42, [0], lesion, record_indices=[0, 1, 2], **kwargs)
    for a, b in zip(expected, actual[:3]): pd.testing.assert_frame_equal(a, b)
    trace = actual[3]
    for slot in ['before_thresholds', 'after_synapses']:
        assert trace[slot + '_v_mV'].shape == (3, len(tape))
        assert np.isfinite(trace[slot + '_g_mV']).all()
        np.testing.assert_allclose(trace[slot + '_t_s'], np.arange(len(tape))*dt/1000)
    spikes = actual[0]
    assert len(spikes) > 0
    for cell, t in zip(spikes.neuron_index, spikes.t):
        tick = round(t*1000/dt)
        assert trace['before_thresholds_v_mV'][cell, tick] > -45
        assert trace['before_thresholds_not_refractory'][cell, tick]


def test_duplicate_recording_indices_rejected_before_loading_model():
    with pytest.raises(ValueError, match='unique'):
        simulate(1, [], [], tape=[], record_indices=[0, 0])
