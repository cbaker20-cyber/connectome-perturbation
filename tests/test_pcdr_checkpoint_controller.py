import json
from pathlib import Path
import pytest
from scripts import pcdr_checkpoint_controller as controller
from eigencircuits.common import atomic_json,sha256


def test_saved_endpoint_and_corruption(tmp_path,monkeypatch):
    spec={'condition':'baseline','id':'trial'}
    assert controller.next_stop(tmp_path,spec)==100
    folder=tmp_path/'checkpoints/baseline';folder.mkdir(parents=True)
    (folder/'latest.json').write_text('{}')
    record=dict(tick=8000000,config=dict(seed=631401,dt_ms=.0000125,duration_s=1.))
    monkeypatch.setattr(controller,'checked_generation',lambda p:(record,None))
    assert controller.next_stop(tmp_path,spec)==200
    record['tick']=80000000
    assert controller.next_stop(tmp_path,spec)==1000
    record['tick']=1
    with pytest.raises(ValueError): controller.next_stop(tmp_path,spec)
    (folder/'owner.lock').write_text('foreign')
    with pytest.raises(ValueError,match='ownership'): controller.next_stop(tmp_path,spec)


def test_completed_trial_hash_checked(tmp_path):
    spec={'condition':'baseline','id':'trial'}
    p=tmp_path/'trials/trial';p.mkdir(parents=True)
    names=['spikes.parquet','rates.parquet','delivered_events.parquet','population.json']
    for n in names:(p/n).write_text('fixture')
    atomic_json(p/'manifest.json',dict(status='complete',spec=spec,outputs={n:sha256(p/n) for n in names}))
    assert controller.next_stop(tmp_path,spec) is None
    (p/names[0]).write_text('changed')
    with pytest.raises(ValueError,match='hash'):controller.next_stop(tmp_path,spec)


@pytest.fixture
def workflow(tmp_path,monkeypatch):
    from scripts import pcdr_ccr_capacity
    root=tmp_path/'package';root.mkdir();(root/'scripts').mkdir()
    for name in ('controller','worker','capacity','sim'):
        (root/f'scripts/pcdr_checkpoint_{name}.py').write_text('fixture')
    validation=tmp_path/'validation'
    for name in ('local_verification','provenance_verification'):
        atomic_json(validation/(name+'.json'),{'status':'passed'})
    monkeypatch.setattr(controller,'ROOT',root)
    monkeypatch.setattr(controller,'package_plan',lambda:{})
    monkeypatch.setattr(controller,'validation_binding',lambda *a:{})
    specs=[dict(condition=c,id=c) for c in ('baseline','mode')]
    monkeypatch.setattr(controller,'select_pair',lambda p:(631401,.0000125,list(enumerate(specs))))
    monkeypatch.setattr(pcdr_ccr_capacity,'allocation',lambda:(4,64000))
    monkeypatch.setattr(controller.socket,'gethostname',lambda:'cpn-fixture')
    monkeypatch.setenv('SLURM_JOB_ID','fixture')
    monkeypatch.setattr(controller,'allocation_seconds',lambda job:72*3600)
    monkeypatch.setattr(controller.signal,'signal',lambda *a:None)
    monkeypatch.setattr(controller,'segment_screen',lambda *a:dict(allowed=True,segment_screen_seconds=100))
    state={'baseline':100,'mode':100}; calls=[]
    monkeypatch.setattr(controller,'next_stop',lambda out,s:state[s['condition']])
    def execute(cmd,directory,budget,cwd):
        condition=cmd[cmd.index('--condition')+1];stop=int(cmd[-1]);calls.append((condition,stop))
        state[condition]=None if stop==1000 else stop+100
        return dict(returncode=0,timed_out=False)
    monkeypatch.setattr(controller,'run_owned',execute)
    return tmp_path/'out',validation,state,calls


def test_controller_advances_exactly_twenty_segments(workflow):
    out,validation,state,calls=workflow
    controller.run(out,validation)
    assert len(calls)==20 and len(set(calls))==20
    assert json.loads((out/'progress.json').read_text())['status']=='execution_complete'
    controller.run(out,validation)
    assert len(calls)==20


def test_budget_stop_and_next_allocation_resume(workflow,monkeypatch):
    out,validation,state,calls=workflow
    monkeypatch.setattr(controller,'segment_screen',lambda *a:dict(allowed=len(calls)<2,segment_screen_seconds=100))
    controller.run(out,validation)
    assert calls==[('baseline',100),('mode',100)]
    assert json.loads((out/'progress.json').read_text())['status']=='allocation_budget_stop'
    monkeypatch.setattr(controller,'segment_screen',lambda *a:dict(allowed=True,segment_screen_seconds=100))
    controller.run(out,validation)
    assert len(calls)==20 and len(set(calls))==20


def test_worker_failure_stops_controller(workflow,monkeypatch):
    out,validation,state,calls=workflow
    monkeypatch.setattr(controller,'run_owned',lambda *a:dict(returncode=1,timed_out=True))
    with pytest.raises(RuntimeError,match='Worker failed'):controller.run(out,validation)
    assert json.loads((out/'progress.json').read_text())['status']=='failed'
    assert not (out/'segments/controller/owner.lock').exists()


def test_changed_source_refused_on_resume(workflow,monkeypatch):
    out,validation,state,calls=workflow
    monkeypatch.setattr(controller,'segment_screen',lambda *a:dict(allowed=False))
    controller.run(out,validation)
    (controller.ROOT/'scripts/pcdr_checkpoint_worker.py').write_text('changed')
    with pytest.raises(ValueError,match='contract changed'):controller.run(out,validation)


def test_validation_binding_refuses_changed_simulator(tmp_path,monkeypatch):
    from types import SimpleNamespace
    current={'python':'3.11.5 fixture','packages':{'brian2':'2.9.0'}}
    monkeypatch.setattr(controller,'environment',lambda:current)
    monkeypatch.setattr(controller,'sys',SimpleNamespace(version_info=(3,11,5)))
    monkeypatch.setattr(controller,'ROOT',tmp_path)
    (tmp_path/'scripts').mkdir()
    for name in ('scripts/pcdr_checkpoint_sim.py','model.py'):(tmp_path/name).write_text('validated')
    hashes={n:sha256(tmp_path/n) for n in ('scripts/pcdr_checkpoint_sim.py','model.py')}
    atomic_json(tmp_path/'local_verification.json',dict(status='passed',
                archive_sha256='56c0352d3696dbc730f90d0f038ea6e5703746831b7f2103a105acf34c739339',
                comparisons={c:dict(exact_state=True,exact_delivered=True,tick=1600000) for c in ('baseline','mode')}))
    atomic_json(tmp_path/'provenance_verification.json',dict(status='passed'))
    for c in ('baseline','mode'):
        for branch,stop in [('reference',10),('uninterrupted',20),('restarted',10),('restarted',20)]:
            atomic_json(tmp_path/f'run/measurements/{c}_{branch}_{stop}/measurement.json',
                        dict(status='complete',environment=current,source_hashes=hashes,exact_reference=True))
    assert len(controller.validation_binding(tmp_path,{'packages':current['packages']}))==6
    (tmp_path/'scripts/pcdr_checkpoint_sim.py').write_text('changed')
    with pytest.raises(ValueError,match='validated source'):
        controller.validation_binding(tmp_path,{'packages':current['packages']})
    (tmp_path/'scripts/pcdr_checkpoint_sim.py').write_text('validated')
    monkeypatch.setattr(controller,'sys',SimpleNamespace(version_info=(3,11,9)))
    with pytest.raises(ValueError,match='environment'):
        controller.validation_binding(tmp_path,{'packages':current['packages']})


def test_controller_reserve_stops_before_launch(workflow,monkeypatch):
    out,validation,state,calls=workflow
    monkeypatch.setattr(controller,'allocation_seconds',lambda job:3599)
    controller.run(out,validation)
    assert calls==[]
    assert json.loads((out/'progress.json').read_text())['status']=='allocation_budget_stop'


def test_real_subprocess_handoff_and_hash_checked_resume(tmp_path,monkeypatch):
    from scripts import pcdr_ccr_capacity
    from scripts.pcdr_smaller_pilot import run_owned
    root=tmp_path/'package';(root/'scripts').mkdir(parents=True)
    child=r'''
import argparse,json,hashlib
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--out',type=Path);p.add_argument('--condition');p.add_argument('--stop-ms',type=int);a=p.parse_args()
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d))
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
if a.stop_ms==1000:
 t=a.out/'trials'/a.condition;t.mkdir(parents=True)
 names=['spikes.parquet','rates.parquet','delivered_events.parquet','population.json']
 for n in names:(t/n).write_text('subprocess fixture')
 write(t/'manifest.json',dict(status='complete',spec=dict(condition=a.condition,id=a.condition),outputs={n:digest(t/n) for n in names}))
else:
 tick=a.stop_ms*80000;folder=a.out/'checkpoints'/a.condition;g=folder/f'tick_{tick}_fixture';g.mkdir(parents=True)
 for n in ['network.pkl','delivered.parquet']:(g/n).write_text('fixture payload')
 write(folder/'latest.json',dict(tick=tick,generation=g.name,config=dict(seed=631401,dt_ms=.0000125,duration_s=1.),hashes={n:digest(g/n) for n in ['network.pkl','delivered.parquet']}))
'''
    (root/'scripts/pcdr_checkpoint_worker.py').write_text(child)
    for name in ('controller','capacity','sim'):(root/f'scripts/pcdr_checkpoint_{name}.py').write_text('fixture')
    validation=tmp_path/'validation'
    for name in ('local_verification','provenance_verification'):atomic_json(validation/(name+'.json'),{'status':'passed'})
    monkeypatch.setattr(controller,'ROOT',root)
    monkeypatch.setattr(controller,'package_plan',lambda:{})
    monkeypatch.setattr(controller,'validation_binding',lambda *a:{})
    specs=[dict(condition=c,id=c) for c in ('baseline','mode')]
    monkeypatch.setattr(controller,'select_pair',lambda p:(631401,.0000125,list(enumerate(specs))))
    monkeypatch.setattr(pcdr_ccr_capacity,'allocation',lambda:(4,64000))
    monkeypatch.setattr(controller.socket,'gethostname',lambda:'cpn-fixture')
    monkeypatch.setenv('SLURM_JOB_ID','fixture')
    monkeypatch.setattr(controller,'allocation_seconds',lambda job:72*3600)
    monkeypatch.setattr(controller.signal,'signal',lambda *a:None)
    monkeypatch.setattr(controller,'segment_screen',lambda *a:dict(allowed=True,segment_screen_seconds=30))
    monkeypatch.setattr(controller,'run_owned',run_owned)
    out=tmp_path/'out';controller.run(out,validation)
    records=list(out.glob('segments/controller/*/processes/*/process.json'))
    assert len(records)==20
    assert all(json.loads(p.read_text())['returncode']==0 for p in records)
    assert json.loads((out/'progress.json').read_text())['status']=='execution_complete'
    controller.run(out,validation)
    assert len(list(out.glob('segments/controller/*/processes/*/process.json')))==20
