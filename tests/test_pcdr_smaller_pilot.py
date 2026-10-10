from datetime import datetime, timezone
import copy
import json
import sys

import numpy as np
import pandas as pd
import pytest

from scripts.pcdr_smaller_pilot import deadline_seconds, scientific_gate, compare_prefix
from scripts import pcdr_smaller_pilot as pilot
from scripts.pcdr_fine_sim import input_tape, ticks_for, simulate


def measurements():
    return [dict(status='complete',dt_ms=dt,duration_s=.01,seconds=s,peak_rss_bytes=3e9)
            for dt,s in [(.00005,10.),(.000025,20.)]]


def test_deadline_uses_earlier_limit_with_reserve():
    clock=datetime(2026,10,10,14,30,tzinfo=timezone.utc)
    assert deadline_seconds('2026-10-10T16:30:00+00:00',10000,clock)==6900
    assert deadline_seconds('2026-10-10T16:30:00+00:00',600,clock)==300
    assert deadline_seconds('2026-10-10T14:29:00+00:00',600,clock)==0


@pytest.mark.parametrize('deadline,left',[('2026-10-10T16:30:00',600),('2026-10-10T16:30:00+00:00',float('nan'))])
def test_invalid_deadline(deadline,left):
    with pytest.raises(ValueError):deadline_seconds(deadline,left)


def test_gate_counts_all_twelve_serial_trials():
    gate=scientific_gate(measurements(),36000,32000)
    assert gate['required_serial_seconds']==36000
    assert gate['allowed']
    assert not scientific_gate(measurements(),35999,32000)['allowed']
    assert not scientific_gate(measurements(),40000,23999)['allowed']


@pytest.mark.parametrize('change',['duplicate','missing','unfinished','duration','nan','negative_memory'])
def test_bad_measurements_never_launch(change):
    m=measurements()
    if change=='duplicate':m[1]=copy.deepcopy(m[0])
    if change=='missing':m.pop()
    if change=='unfinished':m[0]['status']='running'
    if change=='duration':m[0]['duration_s']=.001
    if change=='nan':m[0]['seconds']=float('nan')
    if change=='negative_memory':m[0]['peak_rss_bytes']=-1
    with pytest.raises(ValueError):scientific_gate(m,1e9,32000)


def test_later_memory_peak_can_prevent_launch():
    m=measurements();m[1]['peak_rss_bytes']=20e9
    assert not scientific_gate(m,1e9,32000)['allowed']


@pytest.mark.parametrize('dt',[.00005,.000025])
def test_new_steps_preserve_physical_input_times_and_delay(dt):
    ids=['720575940643867296','720575940630868793']
    events=pd.DataFrame({'tick':[0,1,29],'flywire_id':[ids[0],ids[1],ids[0]]})
    tape=input_tape(events,ids,dt,.003)
    t,c=np.nonzero(tape)
    np.testing.assert_allclose(t*dt,[0.,.1,2.9],rtol=0,atol=1e-12)
    assert c.tolist()==[0,1,0]
    assert ticks_for(1.8,dt)*dt==pytest.approx(1.8)
    assert ticks_for(2.2,dt)*dt==pytest.approx(2.2)


@pytest.mark.parametrize('kind',['unknown','duplicate','fraction','negative','outside'])
def test_new_input_grid_rejects_invalid_events(kind):
    ticks=[0];ids=['101']
    if kind=='unknown':ids=['999']
    if kind=='duplicate':ticks=[0,0];ids=['101','101']
    if kind=='fraction':ticks=[.5]
    if kind=='negative':ticks=[-1]
    if kind=='outside':ticks=[10]
    with pytest.raises(ValueError):input_tape(pd.DataFrame({'tick':ticks,'flywire_id':ids}),['101'],.000025,.001)


def test_reference_prefix_keeps_boundary_and_empty_cases(tmp_path):
    spikes=pd.DataFrame({'t':[.0000001,.01],'flywire_id':['720575940643867296']*2})
    delivered=pd.DataFrame({'tick':[0,100000],'flywire_id':['720575940643867296']*2})
    spikes.to_parquet(tmp_path/'spikes.parquet',index=False)
    delivered.to_parquet(tmp_path/'delivered_events.parquet',index=False)
    compare_prefix(spikes.iloc[:1],delivered.iloc[:1],tmp_path,.01,.0001)
    with pytest.raises(AssertionError):compare_prefix(spikes,delivered.iloc[:1],tmp_path,.01,.0001)
    changed=spikes.iloc[:1].copy();changed['t']=.0000002
    with pytest.raises(AssertionError):compare_prefix(changed,delivered.iloc[:1],tmp_path,.01,.0001)
    changed=delivered.iloc[:1].copy();changed['tick']=1
    with pytest.raises(AssertionError):compare_prefix(spikes.iloc[:1],changed,tmp_path,.01,.0001)
    spikes.iloc[:0].to_parquet(tmp_path/'spikes.parquet',index=False)
    delivered.iloc[:0].to_parquet(tmp_path/'delivered_events.parquet',index=False)
    compare_prefix(spikes.iloc[:0],delivered.iloc[:0],tmp_path,.01,.0001)


@pytest.mark.parametrize('dt',[.00005,.000025])
def test_new_steps_against_unwindowed_tiny_network(tmp_path,dt):
    from scripts.pcdr_followup_sim import simulate as reference
    comp=tmp_path/'comp.csv';con=tmp_path/'con.parquet'
    pd.DataFrame({'Completed':[1,1,1]},index=[101,102,103]).to_csv(comp)
    pd.DataFrame({'Presynaptic_Index':[0,1,2],'Postsynaptic_Index':[1,2,0],
                  'Excitatory x Connectivity':[200.,-30.,30.]}).to_parquet(con)
    ev=pd.DataFrame({'tick':[0,1,9,10,11,20,29],'flywire_id':['101']*7})
    args=dict(tape=input_tape(ev,['101'],dt,.003),dt_ms=dt,duration_s=.003,
              completeness=comp,connectivity=con,return_delivered=True)
    expected=reference(42,[0],[],**args)
    actual=simulate(42,[0],[],chunk_ms=1.,**args)
    assert actual[0].iloc[0].t==pytest.approx(dt/1000,abs=1e-15)
    assert 1 in actual[0].neuron_index.values
    for a,b in zip(actual,expected):
        pd.testing.assert_frame_equal(a.astype({'neuron_index':'int64'}),b.astype({'neuron_index':'int64'}),check_exact=True)


@pytest.mark.parametrize('dt',[.00005,.000025])
def test_linear_solution_new_steps(dt):
    import brian2 as b
    b.start_scope();b.prefs.codegen.target='numpy';b.defaultclock.dt=dt*b.ms
    g=b.NeuronGroup(1,'dv/dt = (-52*mV-v+x)/(20*ms) : volt\ndx/dt=-x/(5*ms) : volt',method='linear')
    g.v=-52*b.mV;g.x=3*b.mV
    b.Network(g).run(.05*b.ms)
    assert float(g.x[0]/b.mV)==pytest.approx(3*np.exp(-.05/5),abs=1e-9)
    expected=-52+3*5/(5-20)*(np.exp(-.05/5)-np.exp(-.05/20))
    assert float(g.v[0]/b.mV)==pytest.approx(expected,abs=1e-9)


def test_package_rejects_missing_and_corrupt_files(tmp_path,monkeypatch):
    monkeypatch.setattr(pilot,'ROOT',tmp_path)
    (tmp_path/'package_manifest.json').write_text(json.dumps({'missing':'0'*64}))
    with pytest.raises(ValueError,match='Missing or changed'):pilot.package_plan()
    (tmp_path/'missing').write_text('wrong')
    with pytest.raises(ValueError,match='Missing or changed'):pilot.package_plan()


def test_package_membership_order_duplicates_and_changed_cells(tmp_path,monkeypatch):
    monkeypatch.setattr(pilot,'ROOT',tmp_path)
    mode=[str(720575940600000000+i) for i in range(51)]
    jobs=[dict(id=f'{s}_{c}_{d}',seed=s,condition=c,dt_ms=d,variant='default',
               lesion_ids=[] if c=='baseline' else list(reversed(mode)))
          for s in (631401,631402,631403) for c in ('baseline','mode') for d in (.00005,.000025)]
    plan={'jobs':jobs,'mode_ids':mode,'criteria':{'test':'unchanged'}}
    (tmp_path/'package_manifest.json').write_text('{}')
    (tmp_path/'anchor_plan.json').write_text(json.dumps({'criteria':plan['criteria']}))
    def save(): (tmp_path/'smaller_plan.json').write_text(json.dumps(plan))
    save();assert pilot.package_plan()==plan
    job=next(j for j in jobs if j['condition']=='mode')
    job['lesion_ids'].append(job['lesion_ids'][0]);save()
    with pytest.raises(ValueError,match='support'):pilot.package_plan()
    job['lesion_ids']=mode[:-1]+['999'];save()
    with pytest.raises(ValueError,match='support'):pilot.package_plan()
    job['lesion_ids']=mode;plan['jobs'].pop();save()
    with pytest.raises(ValueError,match='panel'):pilot.package_plan()


def test_owned_worker_timeout_and_failure_keep_logs(tmp_path):
    record=pilot.run_owned([sys.executable,'-c','import time; time.sleep(30)'],tmp_path/'timeout',.2,tmp_path)
    assert record['timed_out'] and record['returncode']!=0
    assert (tmp_path/'timeout/process.json').exists()
    record=pilot.run_owned([sys.executable,'-c','raise ValueError("deliberate failure")'],tmp_path/'failure',10,tmp_path)
    assert not record['timed_out'] and record['returncode']!=0
    assert 'deliberate failure' in (tmp_path/'failure/stderr.txt').read_text()


def test_interrupted_worker_is_stopped_before_propagating(tmp_path,monkeypatch):
    class FakeProcess:
        pid=123456
        returncode=None
        calls=0
        def wait(self,timeout):
            self.calls+=1
            if self.calls==1:raise KeyboardInterrupt('test stop')
            self.returncode=-9
        def poll(self):return self.returncode
    process=FakeProcess();stops=[]
    monkeypatch.setattr(pilot.subprocess,'Popen',lambda *a,**k:process)
    if pilot.os.name=='nt':
        class Stopped: returncode=0;stderr=''
        monkeypatch.setattr(pilot.subprocess,'run',lambda command,**kwargs:stops.append(command) or Stopped())
    else:monkeypatch.setattr(pilot.os,'killpg',lambda pid,sig:stops.append(pid))
    with pytest.raises(KeyboardInterrupt):pilot.run_owned(['fake'],tmp_path/'interrupted',10,tmp_path)
    assert stops and process.returncode==-9
    assert 'interrupted' in json.loads((tmp_path/'interrupted/process.json').read_text())
