"""Verify the final ZIP and its execution-equivalent tested predecessor."""
from pathlib import Path
import sys
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.pcdr_ccr_transfer import read,write,digest,verify,utc


def main():
    prior=ROOT/'exports/ccr_notebook_20260922_final/connectome'
    release=ROOT/'exports/ccr_notebook_20260922_release'
    out=ROOT/'results/pcdr/ccr_release_verification_20260922';out.mkdir(exist_ok=False)
    record=read(release/'archive.json');archive=release/record['archive']
    if digest(archive)!=record['sha256']:raise ValueError('Archive mismatch')
    with zipfile.ZipFile(archive) as zipped:
        if zipped.testzip() is not None:raise ValueError('ZIP CRC error')
        for name in zipped.namelist():
            if not (out/name).resolve().is_relative_to(out.resolve()):raise ValueError('Unsafe ZIP path')
        zipped.extractall(out)
    current=out/'connectome'; a=verify(prior);b=verify(current)
    if set(a['files'])!=set(b['files']):raise ValueError('Different payload membership')
    changes=[name for name in a['files'] if a['files'][name]!=b['files'][name]]
    if changes!=['START_HERE.md']:raise ValueError(f'Unexpected immutable changes: {changes}')
    notebooks=[read(path/'CCR_Preliminary_Followup.ipynb') for path in [prior,current]]
    code=[[cell['source'] for cell in nb['cells'] if cell['cell_type']=='code'] for nb in notebooks]
    if code[0]!=code[1]:raise ValueError('Notebook code changed')
    for source in code[1]:compile(''.join(source),'<notebook>','exec')
    tested=read(ROOT/'results/pcdr/ccr_notebook_validation_20260922_final/validation.json')
    if not tested['passed'] or digest(prior/'transfer_manifest.json')!=tested['source_manifest_sha256']:
        raise ValueError('Previous execution evidence does not match')
    write(out/'verification.json',{'finished_utc':utc(),'passed':True,'archive':record,
        'payload_files':len(b['files']),'changed_payload_files':changes,
        'change':'Corrected library prose: statsmodels was installed; psutil was absent. Notebook markdown corrected likewise.',
        'identical':['all Python and shell scripts','three model datasets','sensitivity design','requirements','notebook code cells'],
        'execution_evidence_sha256':digest(ROOT/'results/pcdr/ccr_notebook_validation_20260922_final/validation.json'),
        'limits':'The predecessor ZIP underwent four real local trials and failure/resume checks. The final ZIP was extracted and hash/CRC checked; unchanged simulation code was not rerun solely for prose changes. Linux installation and CCR remain untested.'})
    print(read(out/'verification.json'))


if __name__=='__main__':main()
