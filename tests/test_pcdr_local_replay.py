import numpy as np
import pytest
from scripts.pcdr_local_replay import replay


def recurrence(arrivals,weights,stop,dt):
    drive=np.zeros(stop)
    for t,w in zip(arrivals,weights):
        if t<stop:drive[t]+=w
    v=-52.;g=0.;last=-100000;spikes=[]
    a,b=np.exp(-dt/20),np.exp(-dt/5)
    for t in range(stop):
        ready=t-last>=round(2.2/dt)
        if ready:
            v=-52+(v+52)*a+g*(a-b)/3;g*=b
            if v>-45:spikes.append(t);last=t;v=-52.;g=0.;ready=False
        if ready:g+=drive[t]
    return np.array(spikes,dtype=np.int64)


def test_matches_sequential_recurrence_and_refractory_events():
    arrivals=np.array([0,0,2,5,20,30,51,90,91,120]);weights=np.array([40,40,-10,50,80,100,-20,90,10,80])
    for dt in [.1,.02]:
        np.testing.assert_array_equal(replay(arrivals,weights,200,dt),recurrence(arrivals,weights,200,dt))
    assert len(replay(np.array([],dtype=int),[],20,.1))==0


@pytest.mark.parametrize('arrivals,weights,dt',[([-1],[1],.1),([1.5],[1],.1),([1],[float('nan')],.1),([1],[1],0)])
def test_invalid_inputs(arrivals,weights,dt):
    with pytest.raises(ValueError):replay(np.array(arrivals),weights,20,dt)


def test_matches_installed_brian_schedule():
    import brian2 as b
    b.start_scope();b.prefs.codegen.target='numpy';b.defaultclock.dt=.1*b.ms
    ticks=np.array([0,2,5,20,30,51,90,91,120]);weights=np.array([80,-10,50,80,100,-20,90,10,80.])
    source=b.SpikeGeneratorGroup(len(ticks),np.arange(len(ticks)),ticks*.1*b.ms)
    target=b.NeuronGroup(1,'dv/dt=(-52*mV-v+g)/(20*ms):volt (unless refractory)\ndg/dt=-g/(5*ms):volt (unless refractory)',
        threshold='v > -45*mV',reset='v=-52*mV; g=0*mV',refractory=2.2*b.ms,method='linear')
    target.v=-52*b.mV
    syn=b.Synapses(source,target,'w:volt',on_pre='g += w',delay=0*b.ms)
    syn.connect(i=np.arange(len(ticks)),j=np.zeros(len(ticks),dtype=int));syn.w=weights*b.mV
    monitor=b.SpikeMonitor(target)
    b.Network(source,target,syn,monitor).run(20*b.ms)
    actual=np.rint(np.asarray(monitor.t/b.ms)/.1).astype(np.int64)
    np.testing.assert_array_equal(replay(ticks,weights,200,.1),actual)
