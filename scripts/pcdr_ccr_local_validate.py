"""Extract the actual transfer archive and exercise its command-line workflow locally."""
from pathlib import Path
import json
import shutil
import sys
import tarfile
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.pcdr_ccr_transfer import digest, read, write, utc
from scripts.pcdr_bounded_process import run_bounded


def main():
    package=ROOT/'exports/ccr_notebook_20260922_final'
    output=ROOT/'results/pcdr/ccr_notebook_validation_20260922_final'
    output.mkdir(parents=True,exist_ok=False)
    archive=package/'Connectome_CCR_Notebook.zip'
    record=read(package/'archive.json')
    if digest(archive)!=record['sha256']: raise ValueError('Archive checksum mismatch')
    write(output/'protocol.json',{'created_utc':utc(),'archive':record,
        'controller_sha256':digest(Path(__file__)),
        'procedure':'Extract archive, verify, initialize technical Git snapshot, prepare fresh smoke plan. Reject missing jobs. Run 0-2, reject missing job 3, resume job 0 and verify unchanged outputs, reject lock collision, run job 3 and collect. Corrupt a disposable copy and require collection rejection; original remains unchanged.',
        'limits':'Each command has a 180-second external deadline. Four whole-brain trials, seed 631301; no inference or Slurm claim. Existing local environment, not a fresh Linux installation.'})
    extracted=output/'extracted'; extracted.mkdir()
    with zipfile.ZipFile(archive) as stream:
        for name in stream.namelist():
            if not (extracted/name).resolve().is_relative_to(extracted.resolve()):
                raise ValueError('Archive path escapes extraction directory')
        stream.extractall(extracted)
    snapshot=extracted/'connectome'; script=snapshot/'scripts/pcdr_ccr_transfer.py'
    study=snapshot/'results/smoke'
    executions={}
    def command(label,*args,success=True):
        result=run_bounded([sys.executable,str(script),*args],output/'logs'/label,180,cwd=snapshot)
        executions[label]=result
        write(output/'executions.json',executions)
        if result['timed_out'] or (result['returncode']==0)!=success:
            raise RuntimeError(f'Unexpected result for {label}; inspect logs')
    command('verify','verify')
    command('initialize','initialize')
    command('prepare','prepare','--study',str(study))
    command('missing_all','collect','--study',str(study),success=False)
    if (study/'smoke_certificate.json').exists(): raise AssertionError('Partial certificate')
    for index in range(3): command(f'worker_{index}','worker','--study',str(study),'--index',str(index))
    command('missing_last','collect','--study',str(study),success=False)
    if (study/'smoke_certificate.json').exists(): raise AssertionError('Partial certificate')
    files=list((study/'trials/baseline').iterdir())
    before={p.name:(digest(p),p.stat().st_mtime_ns) for p in files}
    command('resume','worker','--study',str(study),'--index','0')
    after={p.name:(digest(p),p.stat().st_mtime_ns) for p in files}
    if before!=after: raise AssertionError('Resume rewrote completed evidence')
    lock=study/'baseline.lock'; lock.write_text('deliberate local collision fixture',encoding='utf-8')
    command('locked','worker','--study',str(study),'--index','0',success=False)
    if not lock.exists(): raise AssertionError('Foreign lock removed')
    lock.unlink()
    command('worker_3','worker','--study',str(study),'--index','3')
    command('collect','collect','--study',str(study))
    corrupt=snapshot/'results/corrupt_copy'
    shutil.copytree(study,corrupt)
    (corrupt/'smoke_certificate.json').unlink()
    (corrupt/'trials/baseline/rates.parquet').write_bytes(b'deliberate corruption fixture')
    command('corrupt','collect','--study',str(corrupt),success=False)
    if (corrupt/'smoke_certificate.json').exists(): raise AssertionError('Corrupt certificate')
    shutil.copyfile(study/'smoke_certificate.json',output/'smoke_certificate.json')
    write(output/'validation.json',{'finished_utc':utc(),'passed':True,'archive':record,
        'source_manifest_sha256':digest(snapshot/'transfer_manifest.json'),
        'smoke_certificate_sha256':digest(output/'smoke_certificate.json'),
        'checks':['exact archive extraction','missing all rejected','missing last rejected',
                  'complete resume leaves hashes and mtimes unchanged','foreign lock rejected and retained',
                  'four real simulations verified','corrupted copied output rejected'],
        'not_tested':['CCR access','Linux package installation','Slurm submission/cancellation/requeue','scientific confirmation']})
    print(json.dumps(read(output/'validation.json')))


if __name__=='__main__': main()
