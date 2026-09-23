"""Failure and resume checks for the portable smoke package; no scheduler emulation."""
import json
from pathlib import Path
import pytest
from scripts import pcdr_ccr_transfer as transfer


def test_snapshot_rejects_corruption_missing_and_escaping_paths(tmp_path):
    payload=tmp_path/'source.py'; payload.write_text('original')
    manifest={'files':{'source.py':transfer.digest(payload)}}
    transfer.write(tmp_path/'transfer_manifest.json',manifest)
    assert transfer.verify(tmp_path)==manifest
    payload.write_text('changed')
    with pytest.raises(ValueError,match='changed or missing'): transfer.verify(tmp_path)
    payload.unlink()
    with pytest.raises(ValueError,match='changed or missing'): transfer.verify(tmp_path)
    for bad in ['../outside','/absolute','C:/absolute','folder\\outside']:
        with pytest.raises(ValueError,match='Unsafe'): transfer.safe_path(tmp_path,bad)


def test_worker_refuses_lock_invalid_index_and_releases_owned_lock(tmp_path,monkeypatch):
    from eigencircuits import trials
    plan={'jobs':[{'trial_id':'baseline','seed':1,'context':'sugar','lesion_ids':[]}]}
    monkeypatch.setattr(transfer,'load_plan',lambda _:plan)
    calls=[]
    monkeypatch.setattr(trials,'trial',lambda *args,**kw:calls.append((args,kw)))
    for index in [-1,1]:
        with pytest.raises(ValueError,match='index'): transfer.worker(tmp_path,index)
    lock=tmp_path/'baseline.lock'; lock.write_text('another worker')
    with pytest.raises(FileExistsError): transfer.worker(tmp_path,0)
    assert lock.read_text()=='another worker' and not calls
    lock.unlink(); transfer.worker(tmp_path,0)
    assert len(calls)==1 and not lock.exists()
    def fail(*args,**kw): raise RuntimeError('failed simulation')
    monkeypatch.setattr(trials,'trial',fail)
    with pytest.raises(RuntimeError): transfer.worker(tmp_path,0)
    assert not lock.exists()


def test_real_trial_resume_rejects_output_corruption_and_changed_seed(tmp_path,monkeypatch):
    import pandas as pd
    from eigencircuits import trials
    monkeypatch.setattr(trials,'neuron_ids',lambda:['101','102'])
    monkeypatch.setattr(trials,'sugar_ids',lambda:['101'])
    monkeypatch.setattr(trials,'provenance',lambda:{'sources':{},'inputs':{},'environment':{}})
    calls=[]
    def simulate(*args,**kwargs):
        calls.append(True)
        spikes=pd.DataFrame({'neuron_index':[0,1],'t':[.01,.02]})
        inputs=pd.DataFrame({'neuron_index':[0],'tick':[100]})
        return spikes,inputs,inputs.copy()
    monkeypatch.setattr(trials,'simulate',simulate)
    first=trials.trial(tmp_path,'baseline',1)
    assert trials.trial(tmp_path,'baseline',1)==first and len(calls)==1
    with pytest.raises(ValueError,match='different inputs/code/config'):
        trials.trial(tmp_path,'baseline',2)
    (tmp_path/'rates.parquet').write_bytes(b'corrupt')
    with pytest.raises(ValueError,match='checksum mismatch'):
        trials.trial(tmp_path,'baseline',1)
    assert len(calls)==1


def test_checked_trial_requires_all_outputs_and_frozen_metadata(tmp_path):
    job={'trial_id':'baseline','seed':1,'context':'sugar','lesion_ids':[]}
    prov={'inputs':{},'sources':{},'environment':{}}
    for name in transfer.OUTPUTS: (tmp_path/name).write_bytes(b'fixture')
    m={**job,'status':'complete','provenance':prov,
       'outputs':{name:transfer.digest(tmp_path/name) for name in transfer.OUTPUTS},
       'backend':'numpy','input_protocol':'fixed_binomial_tape_v1',
       'duration_s':1.,'dt_ms':.1,'input_hz':150.,'weight_scale':1.,
       'inhibitory_scale':1.,'strong_fraction':None}
    transfer.write(tmp_path/'manifest.json',m)
    assert transfer.checked_trial(tmp_path,job,{'provenance':prov})==m
    for field,value in [('status','running'),('seed',2),('backend','cython')]:
        transfer.write(tmp_path/'manifest.json',{**m,field:value})
        with pytest.raises(ValueError): transfer.checked_trial(tmp_path,job,{'provenance':prov})
    bad=json.loads(json.dumps(m)); bad['outputs'].pop('rates.parquet')
    transfer.write(tmp_path/'manifest.json',bad)
    with pytest.raises(ValueError,match='Required outputs'): transfer.checked_trial(tmp_path,job,{'provenance':prov})
    transfer.write(tmp_path/'manifest.json',m)
    (tmp_path/'rates.parquet').write_bytes(b'changed')
    with pytest.raises(ValueError,match='Corrupt output'): transfer.checked_trial(tmp_path,job,{'provenance':prov})


def test_followup_has_350_unique_jobs_with_own_network_baselines():
    from scripts.pcdr_ccr_sensitivity import planned_jobs,VARIANTS
    design=transfer.read(Path(__file__).resolve().parents[1]/'docs/pcdr/CCR_SENSITIVITY_DESIGN.json')
    jobs=planned_jobs(design['conditions'])
    assert len(jobs)==len({j['trial_id'] for j in jobs})==350
    assert {j['seed'] for j in jobs}==set(range(631401,631411))
    for variant in VARIANTS:
        for seed in range(631401,631411):
            group=[j for j in jobs if j['variant']==variant and j['seed']==seed]
            assert len(group)==7 and sum(j['lesion_ids']==[] for j in group)==1
    conditions={c['name']:set(c['ids']) for c in design['conditions']}
    assert len(conditions['mode'])==51 and len(conditions['mode_without_mn9'])==50
    assert conditions['mode_without_mn9']|conditions['mn9_only']==conditions['mode']
    assert not conditions['mode_without_mn9']&conditions['mn9_only']


def test_notebook_code_compiles_and_environment_is_excluded():
    root=Path(__file__).resolve().parents[1]
    notebook=transfer.read(root/'notebooks/CCR_Preliminary_Followup.ipynb')
    for cell in notebook['cells']:
        if cell['cell_type']=='code': compile(''.join(cell['source']),'<notebook>','exec')
    assert '.ccr-venv/' in (root/'scripts/pcdr_ccr_transfer.py').read_text()


def test_missing_optional_packages_are_recorded(monkeypatch):
    original=transfer.importlib.metadata.version
    def version(name):
        if name=='psutil': raise transfer.importlib.metadata.PackageNotFoundError(name)
        return original(name)
    monkeypatch.setattr(transfer.importlib.metadata,'version',version)
    assert transfer.package_versions()['psutil'] is None


def test_sensitivity_collection_known_answer_and_missing_job(tmp_path,monkeypatch):
    import pandas as pd
    from eigencircuits import common
    from scripts import pcdr_ccr_sensitivity as followup
    ids=[common.MN9,'102']
    monkeypatch.setattr(common,'neuron_ids',lambda:ids)
    conditions=[{'name':'baseline','ids':[]},{'name':'mn9_only','ids':[ids[0]]}]
    jobs=[j for j in followup.planned_jobs(conditions) if j['variant']['name']=='default']
    prov={'inputs':{},'sources':{s:'hash' for s in ['model.py','eigencircuits/trials.py',
                'eigencircuits/common.py','perturbation/baseline.py']},'environment':{}}
    plan={'jobs':jobs,'conditions':conditions,'variants':[followup.VARIANTS[0]],'provenance':prov}
    monkeypatch.setattr(followup,'load_plan',lambda _:plan)
    transfer.write(tmp_path/'jobs.json',plan)
    with pytest.raises(FileNotFoundError): followup.collect(tmp_path)
    assert not (tmp_path/'results.json').exists()
    for job in jobs:
        directory=tmp_path/'trials'/job['trial_id'];directory.mkdir(parents=True)
        counts=[4,2] if job['condition']=='baseline' else [3,4]
        pd.DataFrame({'root_id':ids,'spike_count':counts,'rate_hz':counts}).to_parquet(directory/'rates.parquet',index=False)
        pd.DataFrame({'flywire_id':[rid for rid,n in zip(ids,counts) for _ in range(n)]}).to_parquet(directory/'spikes.parquet',index=False)
        for name in transfer.OUTPUTS-{'rates.parquet','spikes.parquet'}: (directory/name).write_bytes(b'fixture')
        m={**job,**{k:v for k,v in job['variant'].items() if k!='name'},'status':'complete',
           'provenance':prov,'backend':'numpy','duration_s':1.,'dt_ms':.1,'input_hz':150.,
           'input_protocol':'fixed_binomial_tape_v1','input_digest':'paired',
           'outputs':{name:transfer.digest(directory/name) for name in transfer.OUTPUTS}}
        transfer.write(directory/'manifest.json',m)
    followup.collect(tmp_path)
    result=transfer.read(tmp_path/'results.json')['rows'][0]
    assert result['A']==1 and result['F']==pytest.approx(1/3) and result['total_absolute_sum_hz']==3
    assert result['n_pairs']==10 and result['mn9_delta_hz']==-1
    (tmp_path/'results.json').unlink()
    (tmp_path/'trials'/jobs[-1]['trial_id']/'rates.parquet').write_bytes(b'corrupt')
    with pytest.raises(ValueError,match='Corrupt'): followup.collect(tmp_path)
    assert not (tmp_path/'results.json').exists()
