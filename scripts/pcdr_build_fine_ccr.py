"""Build the single self-contained CCR fine-step upload."""
from pathlib import Path
import json
import sys
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.pcdr_ccr_transfer import read, digest, write
from scripts.pcdr_ccr_sensitivity import validated


def make_plan(old):
    steps=[.0008,.0004,.0002,.0001]
    conditions=['baseline','mode','motor_003','motor_004','motor_005']
    jobs=[dict(j) for j in old['jobs'] if j['stage']=='replay']
    templates=[j for j in old['jobs'] if j['dt_ms']==.05 and j['stage']=='default' and j['condition'] in conditions]
    for seed,condition in [(631405,'mode_without_mn9'),(631430,'mn9_only')]:
        for name in ['baseline',condition]:
            templates.append(next(j for j in old['jobs'] if j['stage']=='finer' and j['seed']==seed and j['condition']==name))
    for dt in steps:
        for template in templates:
            j=dict(template,dt_ms=dt,stage='fine')
            j['id']=f"fine_{str(dt).replace('.','p')}_{j['variant']}_{j['condition']}_{j['seed']}"
            jobs.append(j)
    assert len(jobs)==620 and len({j['id'] for j in jobs})==620
    return {'version':1,'created_date':'2026-09-30','steps_ms':steps,'duration_s':1.,'mode_ids':old['mode_ids'],
        'jobs':jobs,'criteria':{'A':'absolute difference <= max(1 Hz, 5% of finer A)',
        'F':'absolute difference <= 0.01; undefined fractions do not pass',
        'response':'sum absolute difference of paired response vectors / max(1 Hz, sum absolute finer response) <= 0.05',
        'population':'10 ms bin count relative L1 <= 0.05 for BOTH baseline and lesion',
        'group':'mean paired response criteria pass AND >=95% of individual pairs pass response and population criteria',
        'interpretation':'Require both final successive halvings to meet criteria. These are chosen numerical tolerances, not published biological standards. Report all failures and raw differences; no significance claim or candidate reselection.'}}


def notebook():
    cells=[]
    def add(kind,text):
        cell={'cell_type':kind,'id':f'cell-{len(cells)+1}','metadata':{},'source':text.splitlines(True)}
        if kind=='code':cell.update(execution_count=None,outputs=[])
        cells.append(cell)
    add('markdown','''# Fine-step comparison at CCR
Choose Cell → Run All (classic Notebook) or Run → Run All Cells (JupyterLab).
Request UB-HPC, smuldoon, general-compute, 64 cores, 512000 MB, 72 hours, no GPU. Use a permitted QoS from your form; leave extra Jupyter modules and node features blank.

This runs four exact replays followed by 616 one-second trials. It keeps the same 30 default seeds, selected group, three comparison sets, and two previously unstable altered-weight examples. Smaller steps do not by themselves prove convergence. The criteria were fixed in fine_plan.json before these new results.

Python 3.11.5 loads inside a separate shell; the notebook can keep its current kernel. No hand-entered Python path is needed. run_all.sh installs the pinned libraries in a dedicated environment, tests them, runs the study, checks results, and makes CCR_fine_results.zip. Closing your browser does not cancel the allocated job. The allocation expiring still stops it.
''')
    add('code','''from pathlib import Path
import os, subprocess, time, json
ROOT=Path.cwd().resolve()
assert (ROOT/'fine_plan.json').is_file(), 'Open this notebook from the extracted connectome_fine directory.'
assert os.environ.get('SLURM_JOB_ID'), 'Launch this notebook inside the CCR compute allocation.'
print('Folder:',ROOT, '\\nSlurm job:',os.environ['SLURM_JOB_ID'])
''')
    add('code','''# The shell loads simulation modules without changing the notebook kernel.
log=ROOT/'run_all.log'
with log.open('a') as stream:
    process=subprocess.Popen(['bash','-lc','bash run_all.sh'],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
print('Controller PID:',process.pid,'; log:',log)
last=None
while process.poll() is None:
    path=ROOT/'fine_results/progress.json'
    if path.exists():
        state=json.loads(path.read_text())
        message=(state.get('status'),state.get('completed'),state.get('total'),state.get('workers'))
        if message!=last:
            print(message,flush=True);last=message
    time.sleep(30)
if process.returncode:
    print(log.read_text()[-12000:])
    raise RuntimeError('Run stopped; inspect run_all.log and progress.json. Completed trials are retained.')
print('Run and collection finished.')
''')
    add('code','''from IPython.display import FileLink, display
state=json.loads((ROOT/'fine_results/progress.json').read_text())
assert state['status']=='complete' and state['completed']==state['total'], state
print(state['completed'],'verified trials; inspect step_agreement.json for numerical agreement.')
display(FileLink('CCR_fine_results.zip'))
''')
    return {'cells':cells,'metadata':{'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'}},'nbformat':4,'nbformat_minor':5}


def main():
    old=read(ROOT/'docs/pcdr/CCR_RESOLUTION_PLAN.json');plan=make_plan(old)
    study=ROOT/'results/pcdr/results_ccr_20260927/raw_download/expanded_sensitivity'
    original=read(study/'jobs.json')
    for name in ['2023_03_23_completeness_630_final.csv','2023_03_23_connectivity_630_final.parquet']:
        assert digest(ROOT/name)==original['provenance']['inputs'][name], 'Changed original data: '+name
    assert digest(ROOT/'model.py')==original['provenance']['sources']['model.py'], 'Changed original model'
    byid={j['trial_id']:j for j in original['jobs']}
    names=sorted({j['source_trial'] for j in plan['jobs']})
    files={}
    code=['scripts/pcdr_repair_notebook.py','model.py','scripts/pcdr_fine_ccr.py','scripts/pcdr_fine_sim.py','scripts/pcdr_resolution.py',
          'scripts/pcdr_followup_sim.py','scripts/pcdr_ccr_capacity.py','scripts/pcdr_ccr_transfer.py',
          'scripts/pcdr_ccr_sensitivity.py','scripts/pcdr_bounded_process.py',
          'eigencircuits/__init__.py','eigencircuits/common.py','eigencircuits/readouts.py','eigencircuits/memory.py',
          'tests/test_pcdr_fine_sim.py','tests/test_pcdr_fine_ccr.py']
    for name in code+['2023_03_23_completeness_630_final.csv','2023_03_23_connectivity_630_final.parquet','LICENSE']:
        files[name]=(ROOT/name).read_bytes()
    for name in names:
        validated(study/'trials'/name,byid[name],original)
        for path in (study/'trials'/name).iterdir():
            if path.is_file():files['original/trials/'+name+'/'+path.name]=path.read_bytes()
    files['original/jobs.json']=(study/'jobs.json').read_bytes()
    files['requirements-ccr.txt']=(ROOT/'docs/pcdr/requirements-ccr.txt').read_bytes()
    files['START_HERE.md']=(ROOT/'docs/pcdr/CCR_FINE_RUN.md').read_bytes()
    files['run_all.sh']=(ROOT/'scripts/pcdr_fine_run_all.sh').read_bytes().replace(b'\r\n',b'\n')
    document=notebook()
    files['CCR_Fine_Steps.ipynb']=(json.dumps(document,indent=1)+'\n').encode()
    files['notebook_content.json']=(json.dumps([[c['cell_type'], ''.join(c['source'])] for c in document['cells']],indent=2)+'\n').encode()
    files['fine_plan.json']=(json.dumps(plan,indent=2)+'\n').encode()
    import hashlib
    manifest={name:hashlib.sha256(data).hexdigest() for name,data in files.items()}
    files['package_manifest.json']=(json.dumps(manifest,indent=2)+'\n').encode()
    destination=ROOT/'exports/CCR_Fine_Steps.zip';destination.parent.mkdir(exist_ok=True)
    temporary=destination.with_suffix('.zip.tmp')
    with zipfile.ZipFile(temporary,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for name,data in sorted(files.items()):z.writestr('connectome_fine/'+name,data)
    with zipfile.ZipFile(temporary) as z:
        assert z.testzip() is None
        for name,expected in manifest.items():assert hashlib.sha256(z.read('connectome_fine/'+name)).hexdigest()==expected
    temporary.replace(destination)
    write(ROOT/'docs/pcdr/CCR_FINE_PLAN.json',plan)
    write(ROOT/'docs/pcdr/evidence/2026-10-01/fine_package.json',{
        'archive_sha256':digest(destination),'archive_bytes':destination.stat().st_size,
        'files':len(files),'original_trials':len(names),'planned_trials':len(plan['jobs']),
        'verification':'All ZIP member hashes and CRCs checked; all included original trials validated against saved manifests.',
        'limits':'CCR module setup and full-duration execution have not run here.'})
    print(destination, destination.stat().st_size,'bytes;',len(files),'files')


if __name__=='__main__':main()
