from pathlib import Path
import pytest
from scripts.pcdr_ccr_transfer import read
from scripts.pcdr_ccr_sensitivity import planned_jobs
from scripts.pcdr_ccr_capacity import ceiling,check_certificate

ROOT=Path(__file__).resolve().parents[1]


def test_expanded_grid_pairing_and_complete_single_cell_map():
    design=read(ROOT/'docs/pcdr/CCR_EXPANDED_DESIGN.json')
    jobs=planned_jobs(design['conditions'],design['network_variants'],design['seeds'])
    assert len(jobs)==len({j['trial_id'] for j in jobs})==3390
    assert len(design['seeds'])==30
    assert {(v['weight_scale'],v['inhibitory_scale']) for v in design['network_variants']}=={
        (w,i) for w in [.8,1.,1.2] for i in [.8,1.,1.2]}
    for v in design['network_variants']:
        for seed in design['seeds']:
            group=[j for j in jobs if j['variant']==v and j['seed']==seed]
            assert len(group)==(57 if v['name']=='default' else 7)
            assert sum(not j['lesion_ids'] for j in group)==1
    mode=next(c['ids'] for c in design['conditions'] if c['name']=='mode')
    singles=[j['lesion_ids'][0] for j in jobs if j['variant']['name']=='default'
             and j['seed']==design['seeds'][0] and len(j['lesion_ids'])==1]
    assert len(singles)==51 and set(singles)==set(mode)


def test_capacity_reserves_cpu_and_memory():
    assert ceiling(32,128000,3_000_000_000)==24
    assert ceiling(8,128000,3_000_000_000)==6
    assert ceiling(32,32000,3_000_000_000)==4
    with pytest.raises(ValueError):ceiling(2,16000,3_000_000_000)
    with pytest.raises(ValueError):ceiling(32,12000,3_000_000_000)


def test_expanded_notebook_uses_measured_workers_and_dynamic_total():
    nb=read(ROOT/'notebooks/CCR_Expanded_Study.ipynb')
    code='\n'.join(''.join(c['source']) for c in nb['cells'] if c['cell_type']=='code')
    compile(code,'<notebook>','exec')
    assert 'capacity["selected_workers"]' in code and '== 3390' in code
    assert '"--workers", "2"' not in code


def test_capacity_certificate_rejects_other_allocation(tmp_path,monkeypatch):
    from scripts import pcdr_ccr_capacity as capacity
    from scripts.pcdr_ccr_transfer import write,digest
    write(tmp_path/'jobs.json',{'fixture':True})
    write(tmp_path/'capacity.json',{'jobs_sha256':digest(tmp_path/'jobs.json'),
          'slurm_job_id':'123','selected_workers':16,'peak_rss_bytes':3_000_000_000})
    monkeypatch.setattr(capacity,'allocation',lambda:(32,128000))
    monkeypatch.setenv('SLURM_JOB_ID','123')
    check_certificate(tmp_path,16)
    with pytest.raises(ValueError):check_certificate(tmp_path,24)
    monkeypatch.setenv('SLURM_JOB_ID','456')
    with pytest.raises(ValueError,match='Recalibrate'):check_certificate(tmp_path,16)


def test_calibration_chooses_measured_throughput_and_retains_job_indices(tmp_path,monkeypatch):
    from scripts import pcdr_ccr_capacity as capacity,pcdr_ccr_sensitivity as sensitivity
    from scripts import pcdr_ccr_transfer as transfer
    study=tmp_path/'study';study.mkdir()
    smoke=tmp_path/'smoke';smoke.mkdir()
    jobs=[{'index':i,'trial_id':f'job{i}'} for i in range(100)]
    transfer.write(study/'jobs.json',{'jobs':jobs})
    monkeypatch.setattr(capacity,'load_plan',lambda path:{'jobs':jobs if Path(path)==study else [jobs[0]]})
    monkeypatch.setattr(capacity,'allocation',lambda:(32,128000))
    monkeypatch.setenv('SLURM_JOB_ID','123')
    monkeypatch.setattr(transfer,'checked_trial',lambda *args:{'peak_rss_bytes':3_000_000_000})
    monkeypatch.setattr(sensitivity,'validated',lambda *args:{'peak_rss_bytes':3_000_000_000})
    monkeypatch.setattr(capacity,'run_bounded',lambda *args,**kwargs:{'returncode':0})
    # Equal 10-second waves make 24 workers fastest; no scientific outcome is read.
    ticks=iter(range(0,100,10))
    monkeypatch.setattr(capacity.time,'monotonic',lambda:next(ticks))
    capacity.calibrate(study,smoke)
    result=transfer.read(study/'capacity.json')
    assert result['selected_workers']==24
    indices=[i for wave in result['waves'] for i in wave['indices']]
    assert len(indices)==len(set(indices))==53
    assert not (study/'controller.lock').exists()


def test_completed_study_needs_no_new_calibration_or_worker(tmp_path,monkeypatch):
    from scripts import pcdr_ccr_capacity as capacity,pcdr_ccr_sensitivity as sensitivity
    from scripts import pcdr_ccr_transfer as transfer
    study=tmp_path/'study';study.mkdir();smoke=tmp_path/'smoke';smoke.mkdir()
    jobs=[{'index':0,'trial_id':'finished'}]
    plan={'jobs':jobs}
    transfer.write(study/'jobs.json',plan)
    transfer.write(study/'trials/finished/manifest.json',{'status':'complete'})
    monkeypatch.setattr(capacity,'load_plan',lambda _:plan)
    monkeypatch.setattr(sensitivity,'load_plan',lambda _:plan)
    monkeypatch.setattr(capacity,'allocation',lambda:(32,128000))
    monkeypatch.setenv('SLURM_JOB_ID','123')
    monkeypatch.setattr(transfer,'checked_trial',lambda *args:{'peak_rss_bytes':3_000_000_000})
    monkeypatch.setattr(sensitivity,'validated',lambda *args:{'peak_rss_bytes':3_000_000_000})
    def no_process(*args,**kwargs):raise AssertionError('Completed trial spawned a process')
    monkeypatch.setattr(capacity,'run_bounded',no_process)
    monkeypatch.setattr(sensitivity,'run_bounded',no_process)
    capacity.calibrate(study,smoke)
    assert transfer.read(study/'capacity.json')['waves']==[]
    sensitivity.run(study,workers=1,hours=.01)
    assert transfer.read(study/'progress.json')['results'][0]['reused'] is True


def test_notebook_install_targets_simulation_environment(tmp_path,monkeypatch):
    import os,sys,shutil,subprocess
    from types import SimpleNamespace
    nb=read(ROOT/'notebooks/CCR_Expanded_Study.ipynb')
    setup=next(''.join(c['source']) for c in nb['cells'] if c['cell_type']=='code' and ''.join(c['source']).startswith('BASE_PYTHON ='))
    (tmp_path/'requirements-ccr.txt').write_text('numpy==1.26.4\n')
    monkeypatch.setenv('PYTHONPATH','foreign-packages')
    monkeypatch.setenv('PIP_TARGET','foreign-target')
    calls=[]
    def run(args,**kwargs):calls.append((args,kwargs));return SimpleNamespace(returncode=0)
    fake=SimpleNamespace(run=run)
    namespace={'ROOT':tmp_path,'Path':Path,'os':os,'sys':sys,'shutil':shutil,'subprocess':fake}
    exec(compile(setup,'<setup>','exec'),namespace)
    installs=[(args,kw) for args,kw in calls if 'install' in args]
    assert len(installs)==1
    args,kw=installs[0]
    assert '.ccr-venv' in args[0] and args[1:4]==['-m','pip','install']
    assert 'PYTHONPATH' not in kw['env'] and 'PIP_TARGET' not in kw['env']
    assert kw['env']['PIP_CONFIG_FILE']==os.devnull
    assert '--force-reinstall' not in args
    assert any(args[-1]=='environment' for args,kw in calls)


def test_environment_preflight_rejects_foreign_import(monkeypatch):
    from scripts import pcdr_ccr_transfer as transfer
    from types import SimpleNamespace
    monkeypatch.setattr(transfer,'verify',lambda:{'packages':transfer.package_versions(),'dependency_versions':{}})
    monkeypatch.setattr(transfer.importlib,'import_module',lambda _:SimpleNamespace(__file__='C:/foreign/numpy/__init__.py'))
    with pytest.raises(ValueError,match='outside the simulation environment'):
        transfer.check_environment()
