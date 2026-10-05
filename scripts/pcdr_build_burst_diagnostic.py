"""Build one self-contained two-replay diagnostic upload."""
import hashlib
import json
from pathlib import Path
import sys
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.pcdr_ccr_transfer import read, digest


def build():
    inputs=ROOT/'results/pcdr/diagnostic_inputs_20261005'
    plan=read(inputs/'diagnostic_plan.json')
    files={}
    names=['model.py','scripts/pcdr_fine_sim.py','scripts/pcdr_followup_sim.py','scripts/pcdr_state_recorder.py',
        'scripts/pcdr_burst_diagnostic.py','scripts/pcdr_bounded_process.py','scripts/pcdr_ccr_transfer.py',
        'eigencircuits/__init__.py','eigencircuits/common.py','eigencircuits/memory.py',
        'tests/test_pcdr_state_recorder.py','tests/test_pcdr_fine_sim.py','tests/test_pcdr_burst_diagnostic.py',
        '2023_03_23_completeness_630_final.csv','2023_03_23_connectivity_630_final.parquet','LICENSE']
    for name in names:files[name]=(ROOT/name).read_bytes()
    for name,h in plan['model_files'].items():
        if digest(ROOT/name)!=h:raise ValueError('Changed model/data')
    for name,h in plan['reference_files'].items():
        if digest(inputs/name)!=h:raise ValueError('Changed replay reference')
        files[name]=(inputs/name).read_bytes()
    files['diagnostic_plan.json']=(inputs/'diagnostic_plan.json').read_bytes()
    files['requirements-ccr.txt']=(ROOT/'docs/pcdr/requirements-ccr.txt').read_bytes()
    files['START_HERE.md']=(ROOT/'docs/pcdr/CCR_BURST_DIAGNOSTIC.md').read_bytes()
    files['run_all.sh']=b'''#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
exec 9>.run_all.lock
flock -n 9 || { echo "Another Run All is active in this folder."; exit 1; }
module load ccrsoft/2024.04
module load gcccore/13.2.0 python/3.11.5
unset PYTHONPATH PIP_TARGET PIP_PREFIX PIP_USER
export PYTHONNOUSERSITE=1 PIP_CONFIG_FILE=/dev/null
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 MPLBACKEND=Agg
if [ ! -x .diagnostic-venv/bin/python ]; then python -m venv .diagnostic-venv; fi
PYTHON="$PWD/.diagnostic-venv/bin/python"
"$PYTHON" -m pip install -r requirements-ccr.txt
"$PYTHON" -m pip check
"$PYTHON" -c 'import hashlib,json,pathlib; m=json.load(open("package_manifest.json")); assert all(hashlib.sha256(pathlib.Path(k).read_bytes()).hexdigest()==v for k,v in m.items()), "Package file changed"'
"$PYTHON" -m pytest -q tests
mkdir -p diagnostic_results
"$PYTHON" -m pip freeze > diagnostic_results/installed-libraries.txt
"$PYTHON" -u scripts/pcdr_burst_diagnostic.py run --plan diagnostic_plan.json --out diagnostic_results --hours 11
'''
    cells=[]
    def add(kind,s):
        c={'cell_type':kind,'metadata':{},'source':s.splitlines(True),'id':f'cell-{len(cells)}'}
        if kind=='code':c.update(outputs=[],execution_count=None)
        cells.append(c)
    add('markdown','# Burst diagnostic at CCR\nRequest 4 CPU cores, 32000 MB RAM, 12 hours, no GPU. Account smuldoon, general-compute, permitted QoS. Open here and Run All. Two workers replay 750 ms each; recording begins at 600 ms. Exact saved spike/input prefixes must match before success.\n')
    add('code','''from pathlib import Path
import os,subprocess,time,json
ROOT=Path.cwd().resolve()
assert (ROOT/'diagnostic_plan.json').is_file(), 'Open from the extracted connectome_diagnostic folder.'
assert os.environ.get('SLURM_JOB_ID'), 'Use the CCR compute allocation.'
with (ROOT/'run_all.log').open('a') as f:
    process=subprocess.Popen(['bash','-lc','bash run_all.sh'],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
last=None
while process.poll() is None:
    states={}
    for step in ['0.0004','0.0002']:
        p=ROOT/'diagnostic_results'/step/'state/progress.json'
        if p.exists():states[step]=json.loads(p.read_text())['simulated_ms']
    if states!=last:print('Simulated ms of 750:',states,flush=True);last=states
    time.sleep(30)
if process.returncode:
    print((ROOT/'run_all.log').read_text()[-10000:])
    raise RuntimeError('Stopped. Preserve outputs and inspect the log.')
state=json.loads((ROOT/'diagnostic_results/progress.json').read_text())
assert state['status']=='complete',state
from IPython.display import FileLink,display
display(FileLink('CCR_diagnostic_results.zip'))
''')
    # Notebook execution counts and outputs change on save; only immutable run files are hashed.
    manifest={name:hashlib.sha256(data).hexdigest() for name,data in files.items()}
    files['package_manifest.json']=(json.dumps(manifest,indent=2)+'\n').encode()
    files['CCR_Burst_Diagnostic.ipynb']=(json.dumps({'cells':cells,'metadata':{'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'}},'nbformat':4,'nbformat_minor':5},indent=1)+'\n').encode()
    target=ROOT/'exports/CCR_Diagnostic.zip';target.parent.mkdir(exist_ok=True)
    tmp=target.with_suffix('.zip.tmp')
    with zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED) as z:
        for name,data in sorted(files.items()):z.writestr('connectome_diagnostic/'+name,data)
    with zipfile.ZipFile(tmp) as z:
        if z.testzip() is not None:raise ValueError('Upload CRC failure')
        for name,h in manifest.items():
            if hashlib.sha256(z.read('connectome_diagnostic/'+name)).hexdigest()!=h:raise ValueError('Upload hash failure')
    tmp.replace(target)
    print(target, target.stat().st_size, digest(target))


if __name__=='__main__':build()
