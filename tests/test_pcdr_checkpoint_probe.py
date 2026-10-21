from types import SimpleNamespace
import json

import pandas as pd
import pytest

from scripts import pcdr_checkpoint_probe as probe
from test_pcdr_checkpoint import fixture_files


@pytest.mark.parametrize('args',[
    ('other','checkpoint',10),('baseline','checkpoint',100),
    ('baseline','reference',20),('mode','production',10)])
def test_undeclared_probe_refused(args):
    with pytest.raises(ValueError):
        probe.settings(*args)


def test_probe_requires_full_tape():
    assert probe.settings('mode','checkpoint',20)==(.0000125,1.)
    assert probe.settings('baseline','reference',10)==(.0001,.01)


def test_insufficient_allocation_refused_before_files(tmp_path,monkeypatch):
    from scripts import pcdr_ccr_capacity
    monkeypatch.setattr(pcdr_ccr_capacity,'allocation',lambda:(4,32000))
    with pytest.raises(ValueError,match='compute-node allocation'):
        probe.probe(tmp_path/'out',tmp_path/'checkpoint','baseline','checkpoint',10)
    assert not (tmp_path/'out').exists()


def test_login_host_refused_before_files(tmp_path,monkeypatch):
    from scripts import pcdr_ccr_capacity
    monkeypatch.setattr(pcdr_ccr_capacity,'allocation',lambda:(4,64000))
    monkeypatch.setattr(probe.os,'uname',lambda:SimpleNamespace(nodename='login1'),raising=False)
    with pytest.raises(ValueError,match='compute-node allocation'):
        probe.probe(tmp_path/'out',tmp_path/'checkpoint','baseline','checkpoint',10)
    assert not (tmp_path/'out').exists()


def test_worker_records_actual_checkpoint_and_failure(tmp_path,monkeypatch):
    from scripts import pcdr_ccr_capacity
    from scripts.pcdr_checkpoint_sim import simulate
    from eigencircuits.common import fingerprint
    fixture_files(tmp_path)
    trial='default_baseline_631401'
    source=tmp_path/'original/trials'/trial
    source.mkdir(parents=True)
    events=pd.DataFrame({'tick':[0,10,20,30,40,50],
                         'flywire_id':['720575940643867296']*6})
    events.to_parquet(source/'input_events.parquet',index=False)
    (tmp_path/'original/jobs.json').write_text(json.dumps({'jobs':[{
        'trial_id':trial,'variant':{'weight_scale':1.,'inhibitory_scale':1.}}]}))
    for name in ('scripts/pcdr_checkpoint_probe.py','scripts/pcdr_checkpoint_sim.py',
                 'scripts/pcdr_checkpoint_compare.py','model.py'):
        target=tmp_path/name
        target.parent.mkdir(exist_ok=True)
        target.write_text('fixture provenance')
    monkeypatch.setattr(probe,'ROOT',tmp_path)
    monkeypatch.setattr(pcdr_ccr_capacity,'allocation',lambda:(4,64000))
    monkeypatch.setattr(probe.os,'uname',lambda:SimpleNamespace(nodename='cpn-fixture'),raising=False)
    monkeypatch.setenv('SLURM_JOB_ID','fixture')
    monkeypatch.setattr(probe,'sys',SimpleNamespace(version_info=(3,11,5)))
    monkeypatch.setattr(probe,'environment',lambda:{'packages':{}})
    monkeypatch.setattr(probe,'package_plan',lambda:{'packages':{},'mode_ids':[]})
    saved={'input_ids':['720575940643867296'],'input_digest':fingerprint(events.to_dict('list'))}
    monkeypatch.setattr(probe.resolution,'validated',lambda *a:saved)
    monkeypatch.setattr(probe,'neuron_ids',lambda:['720575940643867296','720575940630868793','720575940600000003'])
    # Exercise the worker using six milliseconds on the actual three-cell fixture.
    monkeypatch.setattr(probe,'settings',lambda *a:(.0001,.006))
    def fixture_simulate(*args,**kwargs):
        kwargs.update(completeness=tmp_path/'comp.csv',connectivity=tmp_path/'con.parquet',chunk_ms=1.)
        return simulate(*args,**kwargs)
    monkeypatch.setattr(probe,'simulate',fixture_simulate)
    probe.probe(tmp_path/'out',tmp_path/'checkpoint','baseline','checkpoint',3)
    record=json.loads((tmp_path/'out/measurement.json').read_text())
    assert record['status']=='complete' and record['checkpoint_record']['tick']==30000
    assert record['timings']['store_seconds'][0]>0 and record['peak_rss_bytes']>0
    assert record['checkpoint_bytes']>0 and record['tape_bytes']==60000
    saved['input_digest']='changed'
    with pytest.raises(ValueError,match='Physical input digest'):
        probe.probe(tmp_path/'failed',tmp_path/'checkpoint2','baseline','checkpoint',3)
    failed=json.loads((tmp_path/'failed/measurement.json').read_text())
    assert failed['status']=='failed' and 'Physical input digest' in failed['error']
    assert not (tmp_path/'checkpoint2').exists()
