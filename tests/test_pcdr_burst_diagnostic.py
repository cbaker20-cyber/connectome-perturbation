import pandas as pd
import pytest
from scripts.pcdr_burst_diagnostic import exact_prefix, verified_trial
from scripts.pcdr_ccr_transfer import write,digest


def test_exact_prefix_excludes_endpoint_and_rejects_timing_change():
    expected=pd.DataFrame({'t':[0.,.01,.02],'flywire_id':['101','102','103']})
    actual=expected.iloc[:2].copy()
    exact_prefix(actual,expected,20,.0002,True)
    actual.loc[1,'t']+=1e-10
    with pytest.raises(AssertionError):exact_prefix(actual,expected,20,.0002,True)


def test_empty_delivery_prefix_and_changed_id():
    expected=pd.DataFrame({'tick':[100000],'flywire_id':['101']})
    exact_prefix(expected.iloc[:0],expected,20,.0002)
    actual=expected.copy();actual.flywire_id='102'
    with pytest.raises(AssertionError):exact_prefix(actual,expected,21,.0002)


def test_completed_flag_cannot_hide_missing_state(tmp_path):
    plan=tmp_path/'plan.json'
    write(plan,{'duration_ms':750,'record_window_ms':[600,750]})
    write(tmp_path/'manifest.json',{'status':'complete','dt_ms':.0004,'plan_sha256':digest(plan),
        'duration_ms':750,'record_window_ms':[600,750],'exact_spike_prefix':True,
        'exact_delivery_prefix':True,'sources':{},'outputs':{}})
    with pytest.raises(ValueError,match='recording files'):
        verified_trial(tmp_path,plan,.0004)


@pytest.mark.parametrize('failure',[False,True])
def test_controller_collects_or_records_failure_and_releases_owned_lock(tmp_path,monkeypatch,failure):
    import scripts.pcdr_burst_diagnostic as module
    import zipfile
    from pathlib import Path
    from scripts.pcdr_ccr_transfer import read
    monkeypatch.setattr(module,'ROOT',tmp_path)
    (tmp_path/'model.py').write_text('# fixture\n')
    plan=tmp_path/'plan.json';write(plan,{'dt_ms':[.0004,.0002]})
    launched=[]
    def fake_run(command,directory,timeout_seconds,cwd):
        directory.mkdir(parents=True)
        Path(command[command.index('--out')+1]).mkdir()
        launched.append(command[-1])
        return {'returncode':1 if failure else 0,'timed_out':False}
    monkeypatch.setattr(module,'run_bounded',fake_run)
    monkeypatch.setattr(module,'verified_trial',lambda *args:{'status':'complete'})
    out=tmp_path/'output'
    if failure:
        with pytest.raises(RuntimeError):module.run_all(plan,out,1)
        assert read(out/'progress.json')['status']=='failed'
        assert not (tmp_path/'CCR_diagnostic_results.zip').exists()
    else:
        module.run_all(plan,out,1)
        assert read(out/'progress.json')['completed']==2
        with zipfile.ZipFile(tmp_path/'CCR_diagnostic_results.zip') as z:assert z.testzip() is None
        module.run_all(plan,out,1)
        assert len(launched)==2
    assert not (out/'.controller.lock').exists()


def test_existing_controller_lock_is_preserved(tmp_path):
    from scripts.pcdr_burst_diagnostic import run_all
    out=tmp_path/'output';out.mkdir();lock=out/'.controller.lock';lock.write_text('other-owner')
    with pytest.raises(FileExistsError):run_all(tmp_path/'missing-plan.json',out,1)
    assert lock.read_text()=='other-owner'
