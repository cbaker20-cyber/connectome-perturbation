import json
from pathlib import Path
import pytest
from scripts import pcdr_pathway_run as runner


def test_existing_lock_is_not_removed(tmp_path):
    out=tmp_path/'out';out.mkdir();lock=out/'.controller.lock';lock.write_text('another worker')
    with pytest.raises(FileExistsError):runner.run(tmp_path/'plan',out,duration=2)
    assert lock.read_text()=='another worker'


@pytest.mark.parametrize('separate,total', [(False,4),(True,8)])
def test_worker_failure_is_recorded_and_owned_lock_released(tmp_path,monkeypatch,separate,total):
    def failed(command,directory,*args,**kwargs):
        Path(directory).mkdir(parents=True)
        return {'returncode':1,'timed_out':False}
    monkeypatch.setattr(runner,'run_bounded',failed)
    out=tmp_path/'out'
    with pytest.raises(RuntimeError,match='Trial failed'):
        runner.run(tmp_path/'plan',out,duration=2,separate=separate)
    assert not (out/'.controller.lock').exists()
    assert json.loads((out/'progress.json').read_text())['status']=='failed'
    assert len(list((out/'logs').glob('*/process.json')))==total
    assert not (tmp_path/'pathway_setup_results.zip').exists()


def test_incomplete_trial_prevents_new_launch(tmp_path,monkeypatch):
    out=tmp_path/'out';trial=out/runner.name(*runner.JOBS[0]);trial.mkdir(parents=True)
    (trial/'manifest.json').write_text('{}')
    plan=tmp_path/'plan';plan.write_text('{}')
    def unexpected(*args,**kwargs):raise AssertionError('Must not launch')
    monkeypatch.setattr(runner,'run_bounded',unexpected)
    with pytest.raises(ValueError,match='Incomplete'):
        runner.run(plan,out,duration=2)
    assert not (out/'.controller.lock').exists()
