"""Checks for unattended execution and explicit reduced-pilot labeling."""
import subprocess
import sys
import pandas as pd
import pytest
from eigencircuits.common import atomic_json, atomic_parquet, read_json, sha256
from scripts import pcdr_local_followthrough as follow
from scripts.pcdr_local_queue import execute


def test_status_replace_retries_transient_permission_error(tmp_path, monkeypatch):
    from scripts import pcdr_local_queue as queue
    actual = queue.os.replace
    calls = []
    def replace(src, dst):
        calls.append(1)
        if len(calls) < 3:
            raise PermissionError('temporary reader lock')
        return actual(src, dst)
    monkeypatch.setattr(queue.os, 'replace', replace)
    monkeypatch.setattr(queue.time, 'sleep', lambda _: None)
    path = tmp_path/'status.json'
    queue.write(path, {'completed': 485})
    assert read_json(path) == {'completed': 485}
    assert len(calls) == 3


def test_status_replace_stops_after_bounded_retries(tmp_path, monkeypatch):
    from scripts import pcdr_local_queue as queue
    calls = []
    def replace(src, dst):
        calls.append(1)
        raise PermissionError('persistent lock')
    monkeypatch.setattr(queue.os, 'replace', replace)
    monkeypatch.setattr(queue.time, 'sleep', lambda _: None)
    with pytest.raises(PermissionError):
        queue.write(tmp_path/'status.json', {'completed': 485})
    assert len(calls) == 61


def test_reduced_mode_queue_is_fresh_and_not_confirmation(tmp_path, monkeypatch):
    pilot, modes, controls, out = [tmp_path/name for name in ['baseline','modes','controls','study']]
    atomic_parquet(pilot/'analysis/features.parquet',pd.DataFrame({'root_id':['1','2']}))
    atomic_json(pilot/'analysis/selection.json',{'n_trials':5})
    atomic_json(modes/'selection.json',{'status':'selected','root_ids':['1','2']})
    atomic_parquet(controls/'controls.parquet',pd.DataFrame({'control':[i for i in range(5) for _ in range(2)],'root_id':[str(i) for i in range(10,20)]}))
    meta={'status':'ready','full_matching':True,'accepted':5,'target_ids':['1','2'],
          'features_sha256':sha256(pilot/'analysis/features.parquet'),
          'controls_sha256':sha256(controls/'controls.parquet')}
    atomic_json(controls/'manifest.json',meta)
    monkeypatch.setattr(follow,'provenance',lambda:{})
    follow.create_pilot(pilot,modes,controls,out)
    record=read_json(out/'jobs.json')
    assert record['phase']=='local_mode_pilot' and record['claim_status']=='exploratory_not_confirmation'
    assert record['n_jobs']==35
    assert set(record['seeds'])==set(range(630901,630906))
    assert all(len({j['seed'] for j in record['jobs'] if j['condition']==c['name']})==5 for c in record['conditions'])
    meta['full_matching']=False;atomic_json(controls/'manifest.json',meta)
    with pytest.raises(ValueError,match='strict fully matched'):
        follow.create_pilot(pilot,modes,controls,tmp_path/'bad')


def test_controller_propagates_worker_failure(tmp_path):
    import os
    with (tmp_path/'log.txt').open('w') as log:
        with pytest.raises(subprocess.CalledProcessError):
            execute([sys.executable,'-c','raise SystemExit(7)'],tmp_path,dict(os.environ),log,10)


def test_findings_refuses_incomplete_study(tmp_path):
    from scripts.pcdr_local_findings import report
    atomic_json(tmp_path/'summary.json',{'status':'running'})
    with pytest.raises(ValueError,match='incomplete'):
        report(tmp_path)
