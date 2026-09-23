"""Copy completed preliminary records into the repository without raw trial files."""
from pathlib import Path
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.pcdr_ccr_transfer import write,digest,utc


def main():
    out=ROOT/'docs/pcdr/evidence/2026-09-22-preliminary'
    out.mkdir(parents=True,exist_ok=False)
    items={}
    for group,names in {
        'distribution_feasibility_20260922':['protocol.json','result.json','execution.json'],
        'ccr_notebook_validation_20260922_final':['protocol.json','executions.json','smoke_certificate.json','validation.json'],
        'ccr_release_verification_20260922':['verification.json']}.items():
        for name in names: items[f'{group}/{name}']=ROOT/'results/pcdr'/group/name
    package=ROOT/'exports/ccr_notebook_20260922_release'
    items['release/archive.json']=package/'archive.json'
    items['release/transfer_manifest.json']=package/'connectome/transfer_manifest.json'
    items['release/requirements-ccr.txt']=package/'connectome/requirements-ccr.txt'
    rows=[]
    for name,source in items.items():
        target=out/name;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source,target)
        if digest(source)!=digest(target):raise ValueError('Copy changed')
        rows.append({'file':name,'source':source.relative_to(ROOT).as_posix(),'sha256':digest(target),'bytes':target.stat().st_size})
    write(out/'manifest.json',{'created_utc':utc(),'files':rows,
                             'scope':'Completed preliminary and local deployment checks. Raw data and trial outputs stay local. No CCR results.'})
    shutil.copyfile(package/'connectome/requirements-ccr.txt',ROOT/'docs/pcdr/requirements-ccr.txt')


if __name__=='__main__':main()
