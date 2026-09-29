import numpy as np
import pandas as pd
import pytest
from scripts.pcdr_fine_sim import input_tape, simulate, ticks_for


@pytest.mark.parametrize('dt', [.1, .00625, .0008, .0004, .0002, .0001])
def test_saved_input_times(dt):
    events = pd.DataFrame({'tick': [0, 1, 9], 'flywire_id': ['101', '102', '101']})
    tape = input_tape(events, ['101', '102'], dt, .001)
    tick, cell = np.nonzero(tape)
    np.testing.assert_allclose(tick * dt, [0, .1, .9], rtol=0, atol=1e-12)
    assert cell.tolist() == [0, 1, 0]


@pytest.mark.parametrize('duration,dt', [(1, 0), (1, np.nan), (-1, .1), (1, .3)])
def test_invalid_tick_units(duration, dt):
    with pytest.raises(ValueError): ticks_for(duration, dt)


@pytest.mark.parametrize('ticks,ids', [([0,0],['101','101']),([10],['101']),([-1],['101']),([.5],['101']),([0],['999'])])
def test_invalid_saved_events(ticks, ids):
    with pytest.raises(ValueError):
        input_tape(pd.DataFrame({'tick':ticks,'flywire_id':ids}),['101'],.0001,.001)


@pytest.mark.parametrize('dt', [.1, .00625, .0001])
@pytest.mark.parametrize('lesion', [[], [0]])
def test_recording_chunks_preserve_all_events(tmp_path, dt, lesion):
    from scripts.pcdr_followup_sim import simulate as reference
    comp, con = tmp_path/'comp.csv', tmp_path/'con.parquet'
    pd.DataFrame({'Completed': [1, 1, 1]}, index=[101, 102, 103]).to_csv(comp)
    pd.DataFrame({'Presynaptic_Index': [0, 1, 2], 'Postsynaptic_Index': [1, 2, 0],
                  'Excitatory x Connectivity': [50., -30., 30.]}).to_parquet(con)
    events = pd.DataFrame({'tick': [0, 1, 9, 10, 11, 20, 29], 'flywire_id': ['101']*7})
    tape = input_tape(events, ['101'], dt, .003)
    args = dict(tape=tape, duration_s=.003, dt_ms=dt, completeness=comp,
                connectivity=con, return_delivered=True)
    expected = reference(42, [0], lesion, **args)
    actual = simulate(42, [0], lesion, chunk_ms=1., **args)
    assert actual[0].iloc[0].neuron_index == 0
    assert actual[0].iloc[0].t == pytest.approx(dt / 1000, abs=1e-15)
    for a, b in zip(actual, expected):
        # The older Windows recorder used platform int32 indices; compare exact int64 indices.
        pd.testing.assert_frame_equal(a.astype({'neuron_index': 'int64'}), b.astype({'neuron_index': 'int64'}))


def test_no_drive_stays_silent(tmp_path):
    comp, con = tmp_path/'comp.csv', tmp_path/'con.parquet'
    pd.DataFrame({'Completed': [1, 1]}, index=[101, 102]).to_csv(comp)
    pd.DataFrame({'Presynaptic_Index': [0], 'Postsynaptic_Index': [1],
                  'Excitatory x Connectivity': [50.]}).to_parquet(con)
    result = simulate(42, [], [], tape=np.zeros((1000, 0), dtype=np.int8), duration_s=.0001,
                      dt_ms=.0001, chunk_ms=.05, completeness=comp, connectivity=con, return_delivered=True)
    assert all(frame.empty for frame in result)


def test_linear_subthreshold_solution_at_fine_step():
    import brian2 as b
    b.start_scope()
    b.prefs.codegen.target = 'numpy'
    b.defaultclock.dt = .0001*b.ms
    group = b.NeuronGroup(1, 'dv/dt = (-52*mV-v+g)/(20*ms) : volt\ndg/dt=-g/(5*ms) : volt', method='linear')
    group.v = -52*b.mV
    group.g = 3*b.mV
    b.Network(group).run(.2*b.ms)
    expected_g = 3*np.exp(-.2/5)
    expected_v = -52 + 3*5/(5-20)*(np.exp(-.2/5)-np.exp(-.2/20))
    assert float(group.g[0]/b.mV) == pytest.approx(expected_g, abs=1e-9)
    assert float(group.v[0]/b.mV) == pytest.approx(expected_v, abs=1e-9)
