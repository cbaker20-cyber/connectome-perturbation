import pytest
import json
from pathlib import Path
from types import SimpleNamespace
from scripts.pcdr_checkpoint_validation import stages, run


def test_only_declared_short_prefixes():
    rows=stages()
    assert len(rows)==8 and len(set(rows))==8
    for condition in ('baseline','mode'):
        assert [r[1:] for r in rows if r[0]==condition]==[
            ('reference','reference',10),('checkpoint','uninterrupted',20),
            ('checkpoint','restarted',10),('checkpoint','restarted',20)]


def test_no_allocation_cannot_start(tmp_path,monkeypatch):
    monkeypatch.delenv('SLURM_JOB_ID',raising=False)
    with pytest.raises(ValueError,match='allocation'):
        run(tmp_path/'out')
    assert not (tmp_path/'out').exists()


@pytest.mark.parametrize('fail',[False,True])
def test_controller_stops_on_failure_and_records_scope(tmp_path,monkeypatch,fail):
    from scripts import pcdr_checkpoint_validation as module, pcdr_ccr_capacity
    monkeypatch.setenv('SLURM_JOB_ID','fixture')
    monkeypatch.setattr(pcdr_ccr_capacity,'allocation',lambda:(4,64000))
    monkeypatch.setattr(module.os,'uname',lambda:SimpleNamespace(nodename='cpn-fixture'),raising=False)
    monkeypatch.setattr(module,'allocation_seconds',lambda job:43200)
    monkeypatch.setattr(module.signal,'signal',lambda *a:None)
    calls=[]
    def owned(command,*args):
        calls.append(command)
        out=Path(command[command.index('--out')+1])
        out.mkdir(parents=True)
        (out/'measurement.json').write_text(json.dumps({'status':'complete','exact_reference':True}))
        return {'returncode':1 if fail else 0,'timed_out':False}
    monkeypatch.setattr(module,'run_owned',owned)
    monkeypatch.setattr(module,'compare',lambda *a:{'exact_state':True,'exact_delivered':True})
    if fail:
        with pytest.raises(RuntimeError,match='process failed'):
            run(tmp_path/'out')
    else:
        run(tmp_path/'out')
    record=json.loads((tmp_path/'out/progress.json').read_text())
    assert len(calls)==(1 if fail else 8)
    assert record['status']==('failed' if fail else 'validation_complete')
    assert record['scientific_trials_launched']==0
