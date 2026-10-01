from pathlib import Path
import numpy as np
import pytest
from scripts.pcdr_fine_ccr import agreement, ceiling, checked
from scripts.pcdr_ccr_transfer import write, digest


def test_agreement_identical_and_redistributed():
    assert agreement(np.array([20.,0.]),np.array([20.,0.]),[0])['passes_response']
    assert not agreement(np.array([20.,10.]),np.array([20.,0.]),[0])['passes_response']


def test_undefined_fraction_does_not_pass():
    assert not agreement(np.zeros(2),np.zeros(2),[0])['passes_response']


def test_relative_difference_uses_finer_reference():
    result=agreement(np.array([19.,0.]),np.array([20.,0.]),[0])
    assert result['response_relative_L1']==pytest.approx(.05)
    assert result['passes_response']


def test_capacity_reserves_memory_and_cpus():
    assert ceiling(64,512000)==60
    assert ceiling(4,32000)==2
    assert ceiling(64,16000)==0
    assert ceiling(64,512000,20_000_000_000)==16


def test_completed_files_are_verified(tmp_path):
    spec={'id':'example'}
    outputs={}
    for name in ['spikes.parquet','rates.parquet','delivered_events.parquet','population.json']:
        (tmp_path/name).write_bytes(b'example')
        outputs[name]=digest(tmp_path/name)
    write(tmp_path/'manifest.json',{'status':'complete','spec':spec,'outputs':outputs})
    assert checked(tmp_path,spec)['status']=='complete'
    (tmp_path/'spikes.parquet').write_bytes(b'changed')
    with pytest.raises(ValueError,match='Changed trial output'):checked(tmp_path,spec)


def test_partial_trial_is_not_complete(tmp_path):
    write(tmp_path/'manifest.json',{'status':'running','spec':{'id':'a'},'outputs':{}})
    with pytest.raises(ValueError,match='Incomplete'):checked(tmp_path,{'id':'a'})


def test_collection_known_response(tmp_path,monkeypatch):
    import scripts.pcdr_fine_ccr as fine
    import scripts.pcdr_resolution as resolution
    import pandas as pd
    from eigencircuits.common import MN9
    ids=[MN9,'2','3']
    monkeypatch.setattr(fine,'neuron_ids',lambda:ids)
    monkeypatch.setattr(resolution,'neuron_ids',lambda:ids)
    jobs=[]
    for dt in [.0002,.0001]:
        for condition,values in [('baseline',[10,10,0]),('mode',[0,10,0])]:
            spec={'id':str(dt)+condition,'stage':'fine','dt_ms':dt,'variant':'default','condition':condition,'seed':1,
                  'lesion_ids':[] if condition=='baseline' else [MN9]}
            jobs.append(spec)
            directory=tmp_path/'trials'/spec['id'];directory.mkdir(parents=True)
            pd.DataFrame({'root_id':ids,'rate_hz':values}).to_parquet(directory/'rates.parquet',index=False)
            pd.DataFrame({'t':[],'flywire_id':[]}).to_parquet(directory/'spikes.parquet',index=False)
            pd.DataFrame({'tick':[],'flywire_id':[]}).to_parquet(directory/'delivered_events.parquet',index=False)
            write(directory/'population.json',[sum(values)]+[0]*99)
            outputs={p.name:digest(p) for p in directory.iterdir()}
            write(directory/'manifest.json',{'status':'complete','spec':spec,'outputs':outputs,'spike_count':sum(values),
                'mn9_hz':values[0],'recruited_noninput':2,'peak_rss_bytes':1234,'physical_input_digest':'same'})
    fine.collect(tmp_path,{'jobs':jobs,'steps_ms':[.0002,.0001],'mode_ids':[MN9],'criteria':{}})
    result=fine.read(tmp_path/'step_agreement.json')
    assert result['groups'][0]['meets_declared_criteria']
    assert result['groups'][0]['A_difference_hz']==0
    means=fine.read(tmp_path/'mean_results.json')['rows']
    assert all(m['A']==10 and m['F']==1 for m in means)


@pytest.mark.parametrize('fail',[False,True])
def test_controller_completion_failure_and_cleanup(tmp_path,monkeypatch,fail):
    import scripts.pcdr_fine_ccr as fine
    root=tmp_path/'package';root.mkdir()
    jobs=[{'id':'replay','stage':'replay','seed':631401,'dt_ms':.1},
          {'id':'fine','stage':'fine','seed':631401,'dt_ms':.0001}]
    write(root/'fine_plan.json',{'jobs':jobs})
    write(root/'original/jobs.json',{'provenance':{'environment':{'packages':fine.environment()['packages']}}})
    monkeypatch.setattr(fine,'ROOT',root)
    monkeypatch.setattr(fine,'verify_package',lambda:None)
    monkeypatch.setattr(fine,'allocation',lambda:(4,32000))
    monkeypatch.setattr(fine,'neuron_ids',lambda:['1'])
    monkeypatch.setenv('SLURM_JOB_ID','123')
    monkeypatch.setattr(fine.subprocess,'check_output',lambda *a,**k:'02:00:00')
    out=root/'fine_results'; collected=[];archives=[]
    monkeypatch.setattr(fine,'collect',lambda *a:collected.append(True))
    monkeypatch.setattr(fine,'archive',lambda *a:archives.append(True))
    def fake_process(command,logs,seconds,cwd):
        if fail:return {'returncode':1,'timed_out':False}
        target=Path(command[command.index('--out')+1])
        if command[2]=='probe':
            write(target/'measurement.json',{'peak_rss_bytes':1_000_000_000})
        else:
            spec=jobs[int(command[-1])];directory=target/'trials'/spec['id'];directory.mkdir(parents=True)
            outputs={}
            for name in ['spikes.parquet','rates.parquet','delivered_events.parquet','population.json']:
                (directory/name).write_bytes(b'test');outputs[name]=digest(directory/name)
            write(directory/'manifest.json',{'status':'complete','spec':spec,'outputs':outputs})
        return {'returncode':0,'timed_out':False}
    monkeypatch.setattr(fine,'run_bounded',fake_process)
    if fail:
        with pytest.raises(RuntimeError,match='Worker failed'):fine.run(out,1)
        assert not collected
        assert fine.read(out/'progress.json')['status']=='interrupted_or_failed'
    else:
        fine.run(out,1)
        assert fine.read(out/'progress.json')['completed']==2
        assert collected
        monkeypatch.setattr(fine,'run_bounded',lambda *a,**k:pytest.fail('Completed trials should be reused'))
        fine.run(out,1)
        assert len(collected)==2
    assert archives
    assert not (out/'controller.lock').exists()


def test_result_archive_retains_evidence_not_lock(tmp_path,monkeypatch):
    import scripts.pcdr_fine_ccr as fine
    import zipfile
    monkeypatch.setattr(fine,'ROOT',tmp_path)
    for name in ['fine_plan.json','package_manifest.json','requirements-ccr.txt','notebook_content.json','run_all.sh','CCR_Fine_Steps.ipynb','START_HERE.md','model.py']:
        (tmp_path/name).write_text('test')
    out=tmp_path/'fine_results';out.mkdir()
    (out/'controller.lock').write_text('owned lock')
    (out/'progress.json').write_text('{"status":"interrupted"}')
    fine.archive(out)
    with zipfile.ZipFile(tmp_path/'CCR_fine_results.zip') as z:
        assert z.testzip() is None
        assert 'controller.lock' not in z.namelist()
        assert 'progress.json' in z.namelist()
        assert 'package/run_all.sh' in z.namelist()


def test_notebook_saves_allowed_but_source_changes_rejected(tmp_path,monkeypatch):
    import scripts.pcdr_fine_ccr as fine
    monkeypatch.setattr(fine,'ROOT',tmp_path)
    notebook={'cells':[{'cell_type':'code','source':['x=1\n'],'outputs':[],'execution_count':None,'metadata':{}}]}
    write(tmp_path/'CCR_Fine_Steps.ipynb',notebook)
    write(tmp_path/'notebook_content.json',fine.notebook_content(notebook))
    write(tmp_path/'package_manifest.json',{name:digest(tmp_path/name) for name in ['CCR_Fine_Steps.ipynb','notebook_content.json']})
    fine.verify_package()
    notebook['cells'][0].update(outputs=[{'output_type':'stream','text':'saved output'}],execution_count=1,metadata={'trusted':True})
    write(tmp_path/'CCR_Fine_Steps.ipynb',notebook)
    fine.verify_package()
    notebook['cells'][0]['source']='x=2\n'
    write(tmp_path/'CCR_Fine_Steps.ipynb',notebook)
    with pytest.raises(ValueError,match='cell source changed'):fine.verify_package()
    write(tmp_path/'notebook_content.json',fine.notebook_content(notebook))
    with pytest.raises(ValueError,match='Changed package file'):fine.verify_package()


def test_repair_released_zip_with_saved_notebook(tmp_path,monkeypatch):
    import json,sys,types,zipfile
    from scripts import pcdr_repair_notebook as repair
    monkeypatch.setitem(sys.modules,'fcntl',types.SimpleNamespace(LOCK_EX=1,LOCK_NB=2,flock=lambda *a:None))
    root=tmp_path/'package';root.mkdir()
    (root/'scripts').mkdir()
    old='def verify_package():\n    pass\n\n\ndef checked():\n    pass\n'
    (root/'scripts/pcdr_fine_ccr.py').write_text(old)
    document={'cells':[{'cell_type':'code','source':['x=1\n'],'outputs':[]}]}
    write(root/'CCR_Fine_Steps.ipynb',document)
    write(root/'package_manifest.json',{name:digest(root/name) for name in ['scripts/pcdr_fine_ccr.py','CCR_Fine_Steps.ipynb']})
    upload=tmp_path/'upload.zip'
    with zipfile.ZipFile(upload,'w') as z:
        for name in ['scripts/pcdr_fine_ccr.py','CCR_Fine_Steps.ipynb','package_manifest.json']:z.write(root/name,'connectome_fine/'+name)
    monkeypatch.setattr(repair,'EXPECTED_ZIP',digest(upload))
    document['cells'][0]['outputs']=[{'text':'finished'}]
    write(root/'CCR_Fine_Steps.ipynb',document)
    repair.repair(root,upload)
    assert (root/'fine_results/repair_20261001/package_manifest.json').is_file()
    assert 'def notebook_content' in (root/'scripts/pcdr_fine_ccr.py').read_text()
    import scripts.pcdr_fine_ccr as fine
    monkeypatch.setattr(fine,'ROOT',root)
    fine.verify_package()
    with pytest.raises(ValueError,match='already changed'):repair.repair(root,upload)
