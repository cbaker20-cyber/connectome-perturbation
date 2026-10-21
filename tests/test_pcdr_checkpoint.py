import json
from pathlib import Path
import subprocess
import sys

import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]
WORKER = r'''
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd
from scripts.pcdr_fine_sim import input_tape, simulate as reference
from scripts.pcdr_checkpoint_sim import simulate, CheckpointSaved
base=Path(sys.argv[1]); mode=sys.argv[2]; stop=float(sys.argv[3])
cfg=json.loads((base/'config.json').read_text())
inputs=[] if cfg['empty'] else [0]
events=pd.DataFrame({'tick':pd.Series([0,1,9,10,11,20,29,30,39,40,49,59] if inputs else [],dtype='int64'),
                     'flywire_id':['720575940643867296']*12 if inputs else []})
if cfg.get('changed_tape'): events.loc[0,'tick']=2
tape=input_tape(events,['720575940643867296'] if inputs else [],cfg['dt'],.006)
args=dict(tape=tape,dt_ms=cfg['dt'],duration_s=.006,chunk_ms=1.,
          completeness=base/'comp.csv',connectivity=base/'con.parquet',return_delivered=True)
try:
    result=(reference(631401,inputs,cfg['lesion'],**args) if mode=='reference' else
            simulate(631401,inputs,cfg['lesion'],checkpoint_dir=base/'checkpoint',
                     stop_after_ms=stop if stop else None,**args))
except CheckpointSaved:
    sys.exit(75)
for i,frame in enumerate(result): frame.to_parquet(base/f'{mode}_{i}.parquet',index=False)
'''


def fixture_files(path, dt=.0001, lesion=None, empty=False):
    pd.DataFrame({'Completed':[1,1,1]},index=[720575940643867296,720575940630868793,720575940600000003]).to_csv(path/'comp.csv')
    pd.DataFrame({'Presynaptic_Index':[0,1,2],'Postsynaptic_Index':[1,2,0],
                  'Excitatory x Connectivity':[200.,-30.,30.]}).to_parquet(path/'con.parquet')
    (path/'config.json').write_text(json.dumps(dict(dt=dt,lesion=lesion or [],empty=empty)))


def worker(path, mode='resume', stop=0, expected=0):
    result=subprocess.run([sys.executable,'-c',WORKER,str(path),mode,str(stop)],
                          cwd=ROOT,capture_output=True,text=True,timeout=600)
    assert result.returncode==expected, result.stdout+'\n'+result.stderr
    return result


@pytest.mark.parametrize('dt',[.0001,.0000125])
@pytest.mark.parametrize('lesion',[[],[0]])
def test_two_fresh_process_restarts_match_original(tmp_path,dt,lesion):
    fixture_files(tmp_path,dt,lesion)
    worker(tmp_path,'reference')
    # The first boundary precedes 1.8 ms arrivals; the second intersects later arrivals and resets.
    worker(tmp_path,stop=1,expected=75)
    worker(tmp_path,stop=3,expected=75)
    worker(tmp_path)
    for i in range(3):
        actual=pd.read_parquet(tmp_path/f'resume_{i}.parquet')
        expected=pd.read_parquet(tmp_path/f'reference_{i}.parquet')
        pd.testing.assert_frame_equal(actual,expected,check_exact=True)
    spikes=pd.read_parquet(tmp_path/'reference_0.parquet')
    assert len(spikes)>0
    if not lesion:
        assert 1 in spikes.neuron_index.values


def test_no_input_restart_matches_original(tmp_path):
    fixture_files(tmp_path,empty=True)
    worker(tmp_path,'reference')
    worker(tmp_path,stop=1,expected=75)
    worker(tmp_path)
    for i in range(3):
        actual=pd.read_parquet(tmp_path/f'resume_{i}.parquet')
        expected=pd.read_parquet(tmp_path/f'reference_{i}.parquet')
        pd.testing.assert_frame_equal(actual,expected,check_exact=True)
        assert actual.empty


@pytest.mark.parametrize('change',['lesion','changed_tape','connectivity'])
def test_restart_rejects_changed_scientific_configuration(tmp_path,change):
    fixture_files(tmp_path)
    worker(tmp_path,stop=1,expected=75)
    cfg=json.loads((tmp_path/'config.json').read_text())
    if change=='lesion': cfg['lesion']=[0]
    elif change=='changed_tape': cfg['changed_tape']=True
    else:
        con=pd.read_parquet(tmp_path/'con.parquet')
        con.loc[0,'Excitatory x Connectivity']=201.
        con.to_parquet(tmp_path/'con.parquet')
    (tmp_path/'config.json').write_text(json.dumps(cfg))
    result=worker(tmp_path,expected=1)
    assert 'ValueError' in result.stderr
    assert not (tmp_path/'resume_0.parquet').exists()


@pytest.mark.parametrize('member',['network.pkl','delivered.parquet'])
def test_corrupt_checkpoint_is_rejected_and_preserved(tmp_path,member):
    fixture_files(tmp_path)
    worker(tmp_path,stop=1,expected=75)
    checkpoint=tmp_path/'checkpoint'
    latest=json.loads((checkpoint/'latest.json').read_text())
    saved=checkpoint/latest['generation']/member
    content=saved.read_bytes()+b'corruption'
    saved.write_bytes(content)
    result=worker(tmp_path,expected=1)
    assert 'ValueError' in result.stderr
    assert saved.read_bytes()==content
    assert not (tmp_path/'resume_0.parquet').exists()


def test_other_owner_lock_is_preserved(tmp_path):
    fixture_files(tmp_path)
    checkpoint=tmp_path/'checkpoint'
    checkpoint.mkdir()
    lock=checkpoint/'owner.lock'
    lock.write_text('another worker')
    result=worker(tmp_path,expected=1)
    assert 'FileExistsError' in result.stderr
    assert lock.read_text()=='another worker'


@pytest.mark.parametrize('stop',[.5,7])
def test_stop_must_be_chunk_boundary_within_duration(tmp_path,stop):
    fixture_files(tmp_path)
    result=worker(tmp_path,stop=stop,expected=1)
    assert 'ValueError' in result.stderr
    assert not (tmp_path/'checkpoint/latest.json').exists()


def test_stop_cannot_replay_existing_interval(tmp_path):
    fixture_files(tmp_path)
    worker(tmp_path,stop=1,expected=75)
    latest=(tmp_path/'checkpoint/latest.json').read_bytes()
    result=worker(tmp_path,stop=1,expected=1)
    assert 'ValueError' in result.stderr
    assert (tmp_path/'checkpoint/latest.json').read_bytes()==latest


def test_orphan_save_preserved_and_completed_restart(tmp_path):
    fixture_files(tmp_path)
    worker(tmp_path,'reference')
    worker(tmp_path,stop=1,expected=75)
    orphan=tmp_path/'checkpoint'/'tick_60000_interrupted'
    orphan.mkdir()
    (orphan/'evidence').write_text('partial save retained')
    worker(tmp_path)
    before=(tmp_path/'checkpoint/latest.json').read_bytes()
    worker(tmp_path)
    assert (tmp_path/'checkpoint/latest.json').read_bytes()==before
    assert (orphan/'evidence').read_text()=='partial save retained'
    for i in range(3):
        pd.testing.assert_frame_equal(pd.read_parquet(tmp_path/f'resume_{i}.parquet'),
                                      pd.read_parquet(tmp_path/f'reference_{i}.parquet'),check_exact=True)


def test_pointer_write_failure_retains_previous_checkpoint(tmp_path):
    fixture_files(tmp_path)
    worker(tmp_path,'reference')
    worker(tmp_path,stop=1,expected=75)
    checkpoint=tmp_path/'checkpoint'
    before=(checkpoint/'latest.json').read_bytes()
    fault = '''
import scripts.pcdr_checkpoint_sim as checkpoint_module
def fail_replace(source, target):
    raise OSError('injected checkpoint pointer failure')
checkpoint_module.os.replace = fail_replace
'''
    script=WORKER.replace('base=Path(sys.argv[1]);', fault+'\nbase=Path(sys.argv[1]);')
    result=subprocess.run([sys.executable,'-c',script,str(tmp_path),'resume','3'],
                          cwd=ROOT,capture_output=True,text=True,timeout=600)
    assert result.returncode==1
    assert 'injected checkpoint pointer failure' in result.stderr
    assert (checkpoint/'latest.json').read_bytes()==before
    assert not (checkpoint/'owner.lock').exists()
    orphan_generations=set(checkpoint.glob('tick_30000_*'))
    assert len(orphan_generations)==1
    worker(tmp_path)
    assert all(path.exists() for path in orphan_generations)
    for i in range(3):
        pd.testing.assert_frame_equal(pd.read_parquet(tmp_path/f'resume_{i}.parquet'),
                                      pd.read_parquet(tmp_path/f'reference_{i}.parquet'),check_exact=True)


def test_abrupt_exit_preserves_checkpoint_and_refuses_stale_lock(tmp_path):
    fixture_files(tmp_path)
    worker(tmp_path,stop=1,expected=75)
    checkpoint=tmp_path/'checkpoint'
    before=(checkpoint/'latest.json').read_bytes()
    fault = '''
import scripts.pcdr_checkpoint_sim as checkpoint_module
def exit_before_replace(source, target):
    checkpoint_module.os._exit(86)
checkpoint_module.os.replace = exit_before_replace
'''
    script=WORKER.replace('base=Path(sys.argv[1]);', fault+'\nbase=Path(sys.argv[1]);')
    result=subprocess.run([sys.executable,'-c',script,str(tmp_path),'resume','3'],
                          cwd=ROOT,capture_output=True,text=True,timeout=600)
    assert result.returncode==86
    assert (checkpoint/'latest.json').read_bytes()==before
    lock=(checkpoint/'owner.lock').read_bytes()
    assert json.loads(lock)['pid']>0
    result=worker(tmp_path,expected=1)
    assert 'FileExistsError' in result.stderr
    assert (checkpoint/'owner.lock').read_bytes()==lock
    assert (checkpoint/'latest.json').read_bytes()==before


def test_replaced_owner_lock_is_not_removed(tmp_path, monkeypatch):
    from scripts import pcdr_checkpoint_sim as checkpoint_module
    lock=tmp_path/'owner.lock'
    def replaced(*args, **kwargs):
        lock.write_text('replacement owner')
        raise RuntimeError('injected owner replacement')
    monkeypatch.setattr(checkpoint_module, '_simulate', replaced)
    with pytest.raises(RuntimeError, match='injected owner replacement'):
        checkpoint_module.simulate(checkpoint_dir=tmp_path)
    assert lock.read_text()=='replacement owner'
