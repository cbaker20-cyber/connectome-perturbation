import numpy as np
import pandas as pd
import pytest

from scripts.pcdr_fine_sim import simulate, input_tape
from scripts.pcdr_late_switch import LateSwitch


@pytest.mark.parametrize('target', [1,2])
def test_switch_preserves_prefix_input_and_other_connection(tmp_path,target):
    comp, con = tmp_path/'comp.csv', tmp_path/'con.parquet'
    pd.DataFrame({'Completed': [1, 1, 1]}, index=[101, 102, 103]).to_csv(comp)
    pd.DataFrame({'Presynaptic_Index': [0, 0], 'Postsynaptic_Index': [1, 2],
                  'Excitatory x Connectivity': [1000., 1000.]}).to_parquet(con)
    tape = input_tape(pd.DataFrame({'tick': [0, 50], 'flywire_id': ['101','101']}), ['101'], .1, .01)
    args = dict(tape=tape, dt_ms=.1, duration_s=.01, completeness=comp,
                connectivity=con, chunk_ms=1, return_delivered=True)
    original = simulate(42, [0], [], **args)
    for remove in [False, True]:
        recorder = LateSwitch([(0,target)], 1, remove, tmp_path)
        actual = simulate(42, [0], [], recorder=recorder, **args)
        assert recorder.applied
        for a,b in zip(original[1:], actual[1:]):
            pd.testing.assert_frame_equal(a,b)
        pd.testing.assert_frame_equal(original[0].loc[original[0].t < .001],
                                      actual[0].loc[actual[0].t < .001])
        if remove:
            assert target in set(original[0].neuron_index)
            assert target not in set(actual[0].neuron_index)
            pd.testing.assert_frame_equal(original[0].loc[original[0].neuron_index.eq(3-target)].reset_index(drop=True),
                                          actual[0].loc[actual[0].neuron_index.eq(3-target)].reset_index(drop=True))
        else:
            pd.testing.assert_frame_equal(original[0],actual[0])


@pytest.mark.parametrize('refractory', [False, True])
def test_delivery_time_weights_and_existing_state(tmp_path, refractory):
    import brian2 as b
    b.start_scope(); b.prefs.codegen.target='numpy'; b.defaultclock.dt=.1*b.ms
    source=b.SpikeGeneratorGroup(1,[0,0],[0,2]*b.ms)
    target=b.NeuronGroup(1,'dg/dt = 0*volt/second : volt (unless refractory)',threshold='True' if refractory else 'False',
                        reset='',refractory=10*b.ms)
    syn=b.Synapses(source,target,'w : volt',on_pre='g_post += w',delay=1.8*b.ms)
    syn.connect(); syn.w=2*b.mV
    network=b.Network(source,target,syn)
    recorder=LateSwitch([(0,0)],3,True,tmp_path)
    recorder.setup(network,target,.1,.005)
    network.run(3*b.ms)
    before=float(target.g[0]/b.mV)
    assert before == (0 if refractory else 2)
    recorder.monitors(30,20)
    network.run(2*b.ms)
    assert float(target.g[0]/b.mV) == before
    # First arrival was already delivered (or rejected); second was queued when the weight changed.
    assert recorder.applied


@pytest.mark.parametrize('pairs', [[], [(0,1),(0,1)], [(-1,2)], [(True,1)], [(0.,1)]])
def test_bad_pairs(pairs,tmp_path):
    with pytest.raises(ValueError): LateSwitch(pairs,1,True,tmp_path)


def test_missed_boundary(tmp_path):
    recorder=LateSwitch([(0,1)],1,True,tmp_path)
    recorder.switch_tick=10
    with pytest.raises(ValueError,match='boundary'): recorder.monitors(0,20)
