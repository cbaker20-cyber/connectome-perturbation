"""Write the upload notebook and freeze the descriptive follow-up memberships."""
from pathlib import Path
import json
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.pcdr_ccr_transfer import read,write,digest,utc


def main():
    source=ROOT/'results/pcdr/motor_composition_pilot_20260922/jobs.json'
    previous=read(source)
    byname={c['name']:c for c in previous['conditions']}
    mode=byname['mode']['ids']; mn9='720575940660219265'
    conditions=[{'name':'baseline','ids':[]},{'name':'mode','ids':mode},
                {'name':'mode_without_mn9','ids':[rid for rid in mode if rid!=mn9]},
                {'name':'mn9_only','ids':[mn9]}]
    conditions += [{'name':name,'ids':byname[name]['ids']} for name in ['motor_003','motor_004','motor_005']]
    design={'recorded_utc':utc(),'source_jobs_sha256':digest(source),'conditions':conditions,
        'question':'Does the selected structural support retain its descriptive response footprint under modest model-weight changes, and how much of the response depends on MN9 being in the support?',
        'timing':'Specified after the prior motor-composition pilot and distribution-matching failure; exploratory follow-up, not original confirmation.',
        'comparators':'Three lexicographically first representatives of the three previously observed response groups. Optimized, overlapping and distribution-imbalanced. Not random draws; no reference p-values.',
        'variants':'Default; all weights multiplied by 0.8 or 1.2; inhibitory weights alone multiplied by 0.8 or 1.2. One factor changes at a time. Factors are investigator-chosen sensitivity settings, not estimated biological uncertainty.',
        'seeds':list(range(631401,631411)),'trials':350,
        'analysis':'Each lesion gets its own variant baseline with identical scheduled input and seed. Average signed rate changes over seeds before absolute values. Report A, F, absolute whole-brain response and MN9 change, with 2000 whole-seed bootstrap intervals. No p-values, no support reselection, no claims of biological replication.',
        'cautions':'A uses different denominators for 51-cell, 50-cell and one-cell supports; compare whole-brain response as well. MN9 outgoing-only silencing does not clamp its own firing. Mode-minus-MN9 versus mode is not an additive causal decomposition in a recurrent nonlinear model. Pairwise set response equality may change under altered weights. Ten seeds give descriptive, conditional intervals only.',
        'next_decision':'Report all variants and conditions. If effects change substantially with weights or MN9 exclusion, narrow the interpretation. Regardless of direction, do not promote this to an eigencircuit confirmation while matching and model-to-biology validity remain unresolved.'}
    design_path=ROOT/'docs/pcdr/CCR_SENSITIVITY_DESIGN.json'
    if design_path.exists():
        old=read(design_path)
        if {k:v for k,v in old.items() if k!='recorded_utc'}!={k:v for k,v in design.items() if k!='recorded_utc'}:
            raise ValueError('Existing scientific design differs; create an explicit amendment')
    else: write(design_path,design)
    cells=[]
    def md(text):cells.append({'cell_type':'markdown','metadata':{},'source':text.splitlines(True)})
    def code(text):cells.append({'cell_type':'code','metadata':{},'execution_count':None,'outputs':[],'source':text.splitlines(True)})
    md('''# Connectome preliminary follow-up at CCR

Open this notebook after extracting the ZIP. Run the cells from the top.

**OnDemand settings:** UB-HPC · account `smuldoon` · `general-compute` · **4 cores, 16000 MB RAM, 4 hours, no GPU**. Use the actual valid QoS in your form (the pasted form says its displayed `normal` value should be ignored). Keep the Jupyter application's supported architecture; do not request an incompatible AVX2 node. Leave extra modules blank unless needed to make Python 3.11 available.

The default 2.8 GB allocation is too small: one local simulation peaked at about 2.84 GB before notebook overhead. This workflow uses at most two simulation processes. Cluster timings and memory still need checking.

First: verify the files and run four technical checks. Then: 350 descriptive trials covering five weight settings and seven conditions, using ten shared seeds. The controls are imperfect; this is not a confirmatory test. See `START_HERE.md` and `sensitivity_design.json`. Code and notebook were prepared with Codex assistance.
''')
    code('''from pathlib import Path
import os, sys, json, shutil, subprocess, time
ROOT = Path.cwd().resolve()
if not (ROOT / "transfer_manifest.json").exists():
    raise RuntimeError("Open this notebook from the extracted connectome directory.")
os.environ.update(OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
print("Folder:", ROOT)
print("Notebook Python:", sys.version)
print("Slurm job:", os.environ.get("SLURM_JOB_ID", "not detected; local session"))
''')
    md('''## Libraries and a separate simulation environment

The notebook itself uses Python's standard library and IPython. Simulation uses NumPy, SciPy, pandas, PyArrow, Brian2, Cython, matplotlib and joblib; pytest and statsmodels are retained for the recorded environment. Exact versions, including dependencies, are in `requirements-ccr.txt`; the complete installed list is saved below. The local run had no psutil, which is not required for this workflow.

Use **Python 3.11** for the simulation environment. The notebook kernel can use another version. If no Python 3.11 executable is found, load an appropriate CCR module or set `BASE_PYTHON` to its absolute path. This checks availability instead of guessing a module name. A failed installation should be recorded and reviewed, not fixed by silently changing versions.
''')
    code('''BASE_PYTHON = sys.executable if sys.version_info[:2] == (3, 11) else shutil.which("python3.11")
if not BASE_PYTHON:
    raise RuntimeError("Python 3.11 is not available. Set BASE_PYTHON to an available Python 3.11 path.")
subprocess.run([BASE_PYTHON, "-c", "import sys; assert sys.version_info[:2] == (3,11)"], check=True)
ENV = ROOT / ".ccr-venv"
PYTHON = ENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
if not PYTHON.exists():
    subprocess.run([BASE_PYTHON, "-m", "venv", str(ENV)], check=True)
subprocess.run([str(PYTHON), "-m", "pip", "install", "-r", str(ROOT / "requirements-ccr.txt")], check=True)
subprocess.run([str(PYTHON), "-m", "pip", "check"], check=True)
(ROOT / "results").mkdir(exist_ok=True)
with (ROOT / "results/installed-libraries.txt").open("w") as f:
    subprocess.run([str(PYTHON), "-m", "pip", "freeze"], stdout=f, check=True)
print((ROOT / "requirements-ccr.txt").read_text())
''')
    md('''## Verify and run the four technical checks

These checks use a fresh seed: baseline, exact replay, no input, and an outgoing-only MN9 lesion. All 127,400 neurons must appear in the rate tables. A resumed completed trial must pass its output checksums. The small local Git snapshot records transfer provenance; it is separate from the GitHub repository's history.
''')
    code('''def command(script, *args):
    subprocess.run([str(PYTHON), str(ROOT / "scripts" / script), *map(str, args)], cwd=ROOT, check=True)
command("pcdr_ccr_transfer.py", "verify")
if not (ROOT / ".git").exists():
    command("pcdr_ccr_transfer.py", "initialize")
SMOKE = ROOT / "results/smoke"
if not (SMOKE / "jobs.json").exists():
    command("pcdr_ccr_transfer.py", "prepare", "--study", SMOKE)
for index in range(4):
    command("pcdr_ccr_transfer.py", "worker", "--study", SMOKE, "--index", index)
command("pcdr_ccr_transfer.py", "collect", "--study", SMOKE)
certificate = json.loads((SMOKE / "smoke_certificate.json").read_text())
print(json.dumps(certificate, indent=2))
''')
    md('''## Prepare and start the descriptive follow-up

The conditions are baseline, the 51-cell mode, mode without MN9, MN9 alone, and three existing comparator sets. Weight settings are default, all weights ×0.8/×1.2, and inhibitory weights ×0.8/×1.2. Each comparison uses its own network baseline and the same input schedule. No mode or comparison set is selected using these new outcomes.

The controller runs inside this OnDemand allocation, at most two trials at once, for at most three hours. It does not submit additional Slurm jobs. Keep the OnDemand session alive. If a run stops, completed trials are checked and reused on restart. The next cell starts the run; set `START_FOLLOWUP = False` if you only want the smoke checks today.
''')
    code('''START_FOLLOWUP = True
STUDY = ROOT / "results/sensitivity"
if START_FOLLOWUP:
    if not (STUDY / "jobs.json").exists():
        command("pcdr_ccr_sensitivity.py", "prepare", "--study", STUDY, "--smoke", SMOKE)
    if (STUDY / "controller.lock").exists():
        raise RuntimeError("A controller lock exists. Check whether it is still running before restarting.")
    if (STUDY / "STOP").exists():
        raise RuntimeError("A STOP file exists. Remove it only when you intend to resume.")
    log = (STUDY / "controller.log").open("a")
    process = subprocess.Popen([str(PYTHON), str(ROOT / "scripts/pcdr_ccr_sensitivity.py"),
        "run", "--study", str(STUDY), "--workers", "2", "--hours", "3"],
        cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, start_new_session=(os.name != "nt"))
    log.close()
    print("Started controller PID", process.pid, "inside this allocation.")
''')
    md('''## Progress and results

Rerun this cell to check progress. Once all 350 jobs are complete it verifies the output files and creates the results. A stopped or failed run never produces a partial final analysis. Times, failures and logs stay in `results/sensitivity`.
''')
    code('''progress_path = STUDY / "progress.json"
if progress_path.exists():
    progress = json.loads(progress_path.read_text())
    counts = {}
    for item in progress["results"]:
        counts[item["status"]] = counts.get(item["status"], 0) + 1
    print(counts, "of", progress["total"], "jobs")
    if counts.get("complete", 0) == 350 and not (STUDY / "controller.lock").exists():
        command("pcdr_ccr_sensitivity.py", "collect", "--study", STUDY)
        rows = json.loads((STUDY / "results.json").read_text())["rows"]
        for row in rows:
            print(row["variant"], row["condition"], "A:", round(row["A"], 3), "F:", row["F"])
    else:
        print("Still running or incomplete. Check controller.log and individual job logs if failures appear.")
else:
    print("No progress file yet.")
''')
    md('''## Stop or download

To stop after the current trials, set `STOP_AFTER_CURRENT = True` and run the next cell. Do not remove a lock while a process is active. Before a restart following forced session termination, confirm the old Slurm allocation and its processes have ended; retain the logs and failed manifests.

When finished, download `results.json`, `per_seed.csv`, `jobs.json`, the smoke certificate, installed library list, and logs. Keep the full trial directories on CCR for reproducibility. The final optional archive contains the small summaries, not all spike tables. Conditional seed intervals measure simulation variability, not biological uncertainty.
''')
    code('''STOP_AFTER_CURRENT = False
if STOP_AFTER_CURRENT:
    (STUDY / "STOP").touch()
    print("Stop requested; currently running trials can finish.")
if (STUDY / "results.json").exists():
    import zipfile
    files = [STUDY / name for name in ["results.json", "per_seed.csv", "jobs.json", "progress.json", "controller.log"]]
    files += [SMOKE / "smoke_certificate.json", ROOT / "results/installed-libraries.txt"]
    with zipfile.ZipFile(ROOT / "CCR_results_summary.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for path in files:
            if path.exists(): z.write(path, path.relative_to(ROOT))
    print("Download CCR_results_summary.zip; retain full results on CCR.")
''')
    for cell in cells:
        if cell['cell_type']=='code': compile(''.join(cell['source']),'<notebook>','exec')
    write(ROOT/'notebooks/CCR_Preliminary_Followup.ipynb',{'cells':cells,'metadata':{
        'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},
        'language_info':{'name':'python','version':'3.11'}},'nbformat':4,'nbformat_minor':4})


if __name__=='__main__':main()
