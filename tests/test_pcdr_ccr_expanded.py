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
