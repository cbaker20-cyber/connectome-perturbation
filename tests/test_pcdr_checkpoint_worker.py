import json
from types import SimpleNamespace
import pytest
from scripts import pcdr_checkpoint_worker as worker


def test_attempt_preserves_failure_and_allows_retry(tmp_path):
    with pytest.raises(RuntimeError):
        with worker.owned_attempt(tmp_path,'baseline',100) as (first,owner):
            (first/'failure.txt').write_text('preserved')
            raise RuntimeError('interrupted')
    with worker.owned_attempt(tmp_path,'baseline',100) as (second,owner):
        assert first != second and (first/'failure.txt').read_text()=='preserved'
    assert not (first.parent/'owner.lock').exists()


def test_conflicting_worker_refused(tmp_path):
    with worker.owned_attempt(tmp_path,'mode',100) as (stage,owner):
        with pytest.raises(FileExistsError):
            with worker.owned_attempt(tmp_path,'mode',100): pass
        assert json.loads((stage.parent/'owner.lock').read_text())==owner


def test_replaced_owner_preserved(tmp_path):
    with worker.owned_attempt(tmp_path,'mode',100) as (stage,owner):
        (stage.parent/'owner.lock').write_text('foreign owner')
    assert (stage.parent/'owner.lock').read_text()=='foreign owner'


@pytest.mark.parametrize('stop',[200,1000])
def test_missing_prior_checkpoint_refused(tmp_path,stop):
    with pytest.raises(ValueError,match='First segment'): worker.endpoint(tmp_path,stop)


def test_endpoint_order_and_final_recovery(tmp_path,monkeypatch):
    (tmp_path/'latest.json').write_text('{}')
    tick={'tick':8000000}
    monkeypatch.setattr(worker,'checked_generation',lambda p:(tick,None))
    assert worker.endpoint(tmp_path,200)==8000000
    for stop in [100,300,1000]:
        with pytest.raises(ValueError): worker.endpoint(tmp_path,stop)
    tick['tick']=80000000
    assert worker.endpoint(tmp_path,1000)==80000000


def test_output_writer_restores_functions_after_failure(tmp_path,monkeypatch):
    old_tape,old_sim=worker.resolution.input_tape,worker.resolution.simulate
    def fail(*args): raise RuntimeError('output validation failed')
    monkeypatch.setattr(worker.resolution,'worker',fail)
    with pytest.raises(RuntimeError): worker.write_outputs(tmp_path,{},[])
    assert worker.resolution.input_tape is old_tape
    assert worker.resolution.simulate is old_sim


@pytest.mark.parametrize('cpus,memory,host',[(1,64000,'cpn-test'),(4,32000,'cpn-test'),(4,64000,'login1')])
def test_allocation_guard_before_writes(tmp_path,monkeypatch,cpus,memory,host):
    from scripts import pcdr_ccr_capacity
    monkeypatch.setattr(pcdr_ccr_capacity,'allocation',lambda:(cpus,memory))
    monkeypatch.setattr(worker.socket,'gethostname',lambda:host)
    with pytest.raises(ValueError,match='compute allocation'): worker.run(tmp_path/'out','baseline',100)
    assert not (tmp_path/'out').exists()


def test_preparation_failure_recorded_and_lock_released(tmp_path,monkeypatch):
    from scripts import pcdr_ccr_capacity
    monkeypatch.setattr(pcdr_ccr_capacity,'allocation',lambda:(4,64000))
    monkeypatch.setattr(worker.socket,'gethostname',lambda:'cpn-test')
    def fail(*a): raise ValueError('changed package')
    monkeypatch.setattr(worker,'execute',fail)
    with pytest.raises(ValueError,match='changed package'): worker.run(tmp_path,'baseline',100)
    records=list(tmp_path.glob('segments/baseline/*/segment.json'))
    assert len(records)==1
    assert json.loads(records[0].read_text())['status']=='failed'
    assert not (records[0].parent.parent/'owner.lock').exists()

@pytest.fixture
def output_fixture(tmp_path,monkeypatch):
    import pandas as pd
    from eigencircuits.common import fingerprint
    ids=['720575940643867296','720575940630868793']
    source=tmp_path/'original/trials/source';source.mkdir(parents=True)
    events=pd.DataFrame({'tick':[0,10],'flywire_id':[ids[0]]*2})
    events.to_parquet(source/'input_events.parquet',index=False)
    (source/'manifest.json').write_text('{}')
    (tmp_path/'original/jobs.json').write_text(json.dumps({'jobs':[dict(trial_id='source',seed=631401,
                    variant=dict(weight_scale=1.,inhibitory_scale=1.))]}))
    saved=dict(input_ids=[ids[0]],input_digest=fingerprint(events.to_dict('list')),
               spike_digest='unused',delivered_input_digest='unused')
    monkeypatch.setattr(worker,'ROOT',tmp_path)
    monkeypatch.setattr(worker.resolution,'validated',lambda *a:saved)
    monkeypatch.setattr(worker.resolution,'neuron_ids',lambda:ids)
    # A small tape exercises final readout checks without allocating the full input tape.
    import numpy as np
    monkeypatch.setattr(worker,'input_tape',lambda *a:np.zeros((80000000,0),dtype=np.int8))
    spec=dict(id='fixed',source_trial='source',seed=631401,condition='mode',lesion_ids=[ids[1]],
              dt_ms=.0000125,stage='fine')
    def frames():
        return (pd.DataFrame({'neuron_index':[1,1],'t':[.003,.006]}),
                pd.DataFrame({'neuron_index':[0,0],'tick':[0,80000]}),
                pd.DataFrame({'neuron_index':[0],'tick':[0]}))
    return tmp_path,spec,frames,ids


def test_real_output_validation_and_sparse_rates(output_fixture):
    import pandas as pd
    root,spec,frames,ids=output_fixture
    worker.write_outputs(root/'out',spec,frames())
    m=json.loads((root/'out/manifest.json').read_text())
    assert m['status']=='complete' and m['spike_count']==2 and m['recruited_noninput']==1
    rates=pd.read_parquet(root/'out/rates.parquet')
    assert rates.root_id.tolist()==[ids[1]] and rates.rate_hz.tolist()==[2.]
    population=json.loads((root/'out/population.json').read_text())
    assert len(population)==100 and population[0]==2 and sum(population)==2


@pytest.mark.parametrize('failure',['input','delivery','refractory'])
def test_real_output_validation_preserves_failure(output_fixture,failure):
    root,spec,frames,ids=output_fixture
    data=frames()
    if failure=='input': data[1].loc[1,'tick']=80001
    elif failure=='delivery': data[2].loc[0,'tick']=1
    else: data[0].loc[1,'t']=.0031
    with pytest.raises(ValueError):worker.write_outputs(root/'out',spec,data)
    assert json.loads((root/'out/manifest.json').read_text())['status']=='failed'


def test_production_run_with_real_bounded_simulator(output_fixture,monkeypatch):
    from test_pcdr_checkpoint import fixture_files
    from scripts.pcdr_checkpoint_sim import simulate as real_simulate
    from scripts.pcdr_fine_sim import input_tape as real_tape
    from scripts import pcdr_ccr_capacity
    root,spec,frames,ids=output_fixture
    fixture_files(root,dt=.0000125)
    # Dataset, six-ms duration, allocation and environment adapters keep this local test bounded.
    all_ids=ids+['720575940600000003']
    monkeypatch.setattr(worker,'neuron_ids',lambda:all_ids)
    monkeypatch.setattr(worker.resolution,'neuron_ids',lambda:all_ids)
    monkeypatch.setattr(worker,'package_plan',lambda:{'packages':{}})
    monkeypatch.setattr(worker,'select_pair',lambda p:(631401,.0000125,[(0,spec)]))
    monkeypatch.setattr(worker,'environment',lambda:{'packages':{}})
    monkeypatch.setattr(worker,'sys',SimpleNamespace(version_info=(3,11,5)))
    monkeypatch.setattr(worker,'endpoint',lambda *a:0)
    monkeypatch.setattr(pcdr_ccr_capacity,'allocation',lambda:(4,64000))
    monkeypatch.setattr(worker.socket,'gethostname',lambda:'cpn-fixture')
    for name in ('scripts/pcdr_checkpoint_worker.py','scripts/pcdr_checkpoint_sim.py','model.py'):
        p=root/name;p.parent.mkdir(exist_ok=True);p.write_text('fixture source')
    monkeypatch.setattr(worker,'input_tape',lambda events,inputs,dt:real_tape(events,inputs,dt,.006))
    def bounded(*args,**kwargs):
        kwargs.update(duration_s=.006,chunk_ms=1.,stop_after_ms=6,
                      completeness=root/'comp.csv',connectivity=root/'con.parquet')
        return real_simulate(*args,**kwargs)
    monkeypatch.setattr(worker,'simulate',bounded)
    out=root/'production'
    worker.run(out,'mode',1000)
    manifest=out/'trials/fixed/manifest.json'
    before=manifest.read_bytes()
    assert json.loads(before)['status']=='complete'
    records=list(out.glob('segments/mode/*/segment.json'))
    assert len(records)==1 and json.loads(records[0].read_text())['status']=='complete'
    assert json.loads(records[0].read_text())['peak_rss_bytes']>0
    with pytest.raises(FileExistsError,match='Existing trial preserved'):
        worker.run(out,'mode',1000)
    assert manifest.read_bytes()==before
    records=list(out.glob('segments/mode/*/segment.json'))
    assert sorted(json.loads(p.read_text())['status'] for p in records)==['complete','failed']
