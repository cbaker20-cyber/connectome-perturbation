import numpy as np
import pandas as pd
import pytest
from scripts.pcdr_fine_sim import simulate, input_tape
from scripts.pcdr_state_recorder import StateRecorder


@pytest.mark.parametrize('dt', [.1, .0004, .0002])
def test_recorder_preserves_spikes_and_delivery(tmp_path, dt):
    comp, con = tmp_path/'comp.csv', tmp_path/'con.parquet'
    pd.DataFrame({'Completed':[1,1,1]}, index=[101,102,103]).to_csv(comp)
    pd.DataFrame({'Presynaptic_Index':[0,1,2], 'Postsynaptic_Index':[1,2,0],
                  'Excitatory x Connectivity':[100.,-30.,50.]}).to_parquet(con)
    events = pd.DataFrame({'tick':[0,1,9,10,19,20,29], 'flywire_id':['101']*7})
    args = dict(tape=input_tape(events,['101'],dt,.003), duration_s=.003, dt_ms=dt,
                chunk_ms=1, completeness=comp, connectivity=con, return_delivered=True)
    expected = simulate(42,[0],[],**args)
    actual = simulate(42,[0],[],recorder=StateRecorder(tmp_path/'state',[0,1,2],[1,3]),**args)
    for a,b in zip(actual,expected):
        pd.testing.assert_frame_equal(a,b)
    files = sorted((tmp_path/'state').glob('*.npz'))
    assert len(files)==6
    for path in files:
        with np.load(path, allow_pickle=False) as values:
            assert values['v_mV'].shape==(3,round(1/dt))
            assert values['tick'][0]>=round(1/dt)
            assert values['tick'][-1]<round(3/dt)


def test_refractory_drive_is_discarded_and_reset_does_not_erase_synaptic_weights():
    import brian2 as b
    import model
    b.start_scope(); b.defaultclock.dt=.1*b.ms; b.prefs.codegen.target='numpy'
    group=b.NeuronGroup(1,model.default_params['eqs'],threshold='v>v_th',
        reset=model.default_params['eq_rst'],refractory='rfc',method='linear',namespace=model.default_params)
    group.v=-44*b.mV; group.g=0*b.mV; group.rfc=2.2*b.ms
    source=b.SpikeGeneratorGroup(1,[0,0],[1,3]*b.ms)
    syn=b.Synapses(source,group,'w:volt',on_pre='g+=w')
    syn.connect();syn.w=-2*b.mV
    mon=b.StateMonitor(group,['v','g','not_refractory'],record=True,when='end')
    spikes=b.SpikeMonitor(group)
    b.Network(group,source,syn,mon,spikes).run(4*b.ms)
    assert len(spikes.t)==1
    assert mon.g[0,10]/b.mV==0
    assert mon.g[0,30]/b.mV==pytest.approx(-2)
    assert float(syn.w[0]/b.mV)==-2


def test_invalid_recording_rejected(tmp_path):
    import brian2 as b
    b.start_scope()
    g=b.NeuronGroup(2,'v:1')
    for indices,window in [([], [0,1]),([0,0],[0,1]),([2],[0,1]),([0],[-1,1]),([0],[0,3])]:
        with pytest.raises(ValueError):
            StateRecorder(tmp_path/'unused',indices,window).setup(b.Network(g),g,.1,.002)
    recorder=StateRecorder(tmp_path/'window',[0],[.5,1.5])
    recorder.setup(b.Network(g),g,.1,.002)
    with pytest.raises(ValueError):recorder.monitors(0,10)
