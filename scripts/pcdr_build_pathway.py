"""Build and check the current pathway upload without submitting it."""
import hashlib
import json
from pathlib import Path
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.pcdr_ccr_transfer import read,digest


def build():
    inputs=ROOT/'results/pcdr/diagnostic_inputs_20261005'
    plan=read(inputs/'diagnostic_plan.json')
    names=['model.py','scripts/pcdr_fine_sim.py','scripts/pcdr_followup_sim.py',
        'scripts/pcdr_state_recorder.py','scripts/pcdr_burst_diagnostic.py',
        'scripts/pcdr_bounded_process.py','scripts/pcdr_ccr_transfer.py',
        'scripts/pcdr_edge_intervention.py','scripts/pcdr_late_switch.py','scripts/pcdr_pathway_trial.py','scripts/pcdr_pathway_run.py',
        'eigencircuits/__init__.py','eigencircuits/common.py','eigencircuits/memory.py',
        'tests/test_pcdr_late_switch.py','tests/test_pcdr_pathway_trial.py','tests/test_pcdr_pathway_run.py','tests/test_pcdr_edge_intervention.py',
        '2023_03_23_completeness_630_final.csv','2023_03_23_connectivity_630_final.parquet','LICENSE']
    files={name:(ROOT/name).read_bytes() for name in names}
    for name,h in plan['model_files'].items():
        if digest(ROOT/name)!=h:raise ValueError('Changed model/data')
    for name,h in plan['reference_files'].items():
        if digest(inputs/name)!=h:raise ValueError('Changed reference')
        files[name]=(inputs/name).read_bytes()
    files['diagnostic_plan.json']=(inputs/'diagnostic_plan.json').read_bytes()
    files['requirements-ccr.txt']=(ROOT/'docs/pcdr/requirements-ccr.txt').read_bytes()
    files['START_HERE.md']=(ROOT/'docs/pcdr/CCR_PATHWAY_RUN.md').read_bytes()
    files['run_all.sh']=(ROOT/'scripts/pcdr_pathway_run_all.sh').read_text(encoding='utf-8').replace('\r\n','\n').replace('pathway_results','late_pathway_results').replace('--workers 4','--workers 4 --late').encode()
    manifest={name:hashlib.sha256(data).hexdigest() for name,data in files.items()}
    files['package_manifest.json']=(json.dumps(manifest,indent=2)+'\n').encode()
    cells=[]
    def add(kind,text):
        cell=dict(cell_type=kind,metadata={},source=text.splitlines(True),id=f'cell-{len(cells)}')
        if kind=='code':cell.update(outputs=[],execution_count=None)
        cells.append(cell)
    add('markdown','# Two connections removed at 600 ms\nRequest 4 cores, 32000 MB RAM, 8 hours, no GPU. Open here and Run All once. Four trials run through 750 ms; two no-change references and two late removals. Read START_HERE.md for the comparison and restart limits. After reconnecting, use only the last status cell.\n')
    add('code','''from pathlib import Path
import os, subprocess
ROOT=Path.cwd().resolve()
assert (ROOT/'package_manifest.json').is_file(), 'Open in the extracted connectome_late_pathway folder.'
assert os.environ.get('SLURM_JOB_ID'), 'Launch a CCR compute session first.'
assert int(os.environ.get('SLURM_CPUS_PER_TASK', '4')) >= 4, 'Request four CPU cores.'
with (ROOT/'run_all.log').open('a') as log:
    process=subprocess.Popen(['bash','-lc','bash run_all.sh'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
print('Started process',process.pid,'. Setup and simulation logs: run_all.log',flush=True)
''')
    add('markdown','Run the following cell to check after reconnecting. It also waits for completion during Run All.\n')
    add('code','''from pathlib import Path
import json, time
from IPython.display import FileLink, display
ROOT=Path.cwd().resolve()
last=None
while True:
    status=ROOT/'late_pathway_results/progress.json'
    state=json.loads(status.read_text()) if status.exists() else {'status':'setting up'}
    clocks={p.parent.name:json.loads(p.read_text())['simulated_ms'] for p in (ROOT/'late_pathway_results').glob('*/simulation_progress.json')}
    current=(state,clocks)
    if current!=last:print(state, '\\nSimulated ms of 750:',clocks,flush=True);last=current
    if state['status']=='complete':
        display(FileLink('CCR_late_pathway_results.zip'));break
    if state['status']=='failed':raise RuntimeError(state)
    if 'process' in globals() and process.poll() is not None and process.returncode:
        print((ROOT/'run_all.log').read_text()[-6000:])
        raise RuntimeError('Launch stopped; inspect run_all.log. An existing run may still be active.')
    time.sleep(30)
''')
    files['CCR_Late_Pathway.ipynb']=(json.dumps(dict(cells=cells,metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'}},nbformat=4,nbformat_minor=5),indent=1)+'\n').encode()
    target=ROOT/'exports/CCR_Pathway.zip';temporary=target.with_suffix('.zip.tmp')
    with zipfile.ZipFile(temporary,'w',zipfile.ZIP_DEFLATED) as archive:
        for name,data in sorted(files.items()):archive.writestr('connectome_late_pathway/'+name,data)
    with zipfile.ZipFile(temporary) as archive:
        if archive.testzip() is not None:raise ValueError('Upload CRC failure')
        for name,h in manifest.items():
            if hashlib.sha256(archive.read('connectome_late_pathway/'+name)).hexdigest()!=h:raise ValueError('Upload hash failure')
        for cell in cells:
            if cell['cell_type']=='code':compile(''.join(cell['source']),'notebook','exec')
    temporary.replace(target)
    print(target,target.stat().st_size,digest(target))


if __name__=='__main__':build()
