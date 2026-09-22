"""After singles, attempt one resource-bounded mode pilot; never claim confirmation."""
import argparse
import ctypes
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from eigencircuits.common import atomic_json, now, provenance, read_json, sha256


def create_pilot(pilot, modes, controls, out):
    import pandas as pd
    selected = read_json(modes/'selection.json')
    matches = read_json(controls/'manifest.json')
    features = pilot/'analysis/features.parquet'
    if selected['status'] != 'selected' or matches['status'] != 'ready' or not matches['full_matching'] or matches['accepted'] != 5:
        raise ValueError('Need a valid mode and five strict fully matched sets')
    if matches['target_ids'] != selected['root_ids'] or matches['features_sha256'] != sha256(features):
        raise ValueError('Mode/control features disagree')
    if matches['controls_sha256'] != sha256(controls/'controls.parquet'):
        raise ValueError('Control checksum mismatch')
    conditions = [{'name':'baseline','ids':[],'role':'baseline'},
                  {'name':'mode','ids':selected['root_ids'],'role':'mode'}]
    for index, group in pd.read_parquet(controls/'controls.parquet').groupby('control'):
        conditions.append({'name':f'control_{index:03}', 'ids':group.root_id.tolist(), 'role':'control'})
    seeds = list(range(630901,630906))
    variant = {'name':'default','weight_scale':1.,'inhibitory_scale':1.,'strong_fraction':None}
    jobs = []
    for seed in seeds:
        for condition in conditions:
            jobs.append({'index':len(jobs),'condition':condition['name'],'role':condition['role'],
                         'lesion_ids':condition['ids'],'seed':seed,'variant':variant,
                         'trial_id':f"default_{condition['name']}_{seed}"})
    atomic_json(out/'jobs.json', {'phase':'local_mode_pilot','claim_status':'exploratory_not_confirmation',
        'status':'prepared_not_submitted','created_utc':now(),'backend':'numpy','n_jobs':len(jobs),
        'conditions':conditions,'variants':[variant],'seeds':seeds,'jobs':jobs,'provenance':provenance(),
        'selection_sha256':sha256(pilot/'analysis/selection.json'),'features_sha256':sha256(features),
        'mode_sha256':sha256(modes/'selection.json'),'controls_sha256':sha256(controls/'controls.parquet'),
        'reason':'Five strict controls and five fresh seeds are a local pilot. The 199-control, 30-seed confirmation remains separate.'})


def summarize_mode(study):
    from eigencircuits.readouts import reference_test
    rows = read_json(study/'analysis/results.json')
    result = reference_test(next(r for r in rows if r['role']=='mode'), [r for r in rows if r['role']=='control'])
    result.update(claim_status='exploratory_not_confirmation', n_seeds=5,
                  results_sha256=sha256(study/'analysis/results.json'))
    atomic_json(study/'pilot_comparison.json', result)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--action', choices=['watch','prepare','summarize'], default='watch')
    args = p.parse_args()
    singles = ROOT/'results/pcdr/ccr_singles_20260919'
    pilot = ROOT/'results/pcdr/corrected_20260919'
    base = ROOT/'results/pcdr/local_followthrough_20260920'
    modes, controls, study = base/'modes', base/'full_controls_5', base/'mode_pilot'
    if args.action == 'prepare':
        create_pilot(pilot,modes,controls,study); return
    if args.action == 'summarize':
        summarize_mode(study); return
    base.mkdir(parents=True, exist_ok=True)
    deadline = read_json(singles/'local_status.json')['deadline_epoch']
    status = {'started_utc':now(),'deadline_epoch':deadline,'status':'waiting_for_singles', 'pid':os.getpid()}
    lock = base/'controller.lock'
    with lock.open('x') as f: f.write(str(os.getpid()))
    statefile = base/'status.json'
    env = dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1', NUMEXPR_NUM_THREADS='1')
    def phase(name, command, limit):
        from pcdr_local_queue import available_memory
        while time.time()<deadline:
            free=available_memory()
            if free is None or free>=4*1024**3: break
            status.update(status='waiting_for_memory',phase=name,updated_utc=now());atomic_json(statefile,status)
            time.sleep(30)
        remaining = deadline-time.time()
        if remaining < 60 or (base/'STOP').exists():
            raise TimeoutError('Deadline reached or STOP requested')
        status.update(status='running',phase=name,command=command,updated_utc=now()); atomic_json(statefile,status)
        with (base/(name+'.log')).open('a',encoding='utf-8') as f:
            f.write(now()+' '+json.dumps(command)+'\n');f.flush()
            proc = subprocess.Popen(command,cwd=ROOT,env=env,stdout=f,stderr=subprocess.STDOUT)
            try:
                code = proc.wait(timeout=min(limit,remaining))
            except subprocess.TimeoutExpired:
                if os.name == 'nt':
                    subprocess.run(['taskkill','/PID',str(proc.pid),'/T','/F'],stdout=f,stderr=f)
                else: proc.kill()
                proc.wait(); raise
            if code: raise RuntimeError(f'{name} failed with exit code {code}; see log')
    try:
        atomic_json(statefile,status)
        while time.time()<deadline:
            state = read_json(singles/'local_status.json')
            if state['status']=='complete': break
            if state['status'] in ['failed','stopped_at_limit']:
                raise RuntimeError('Single-cell stage stopped; do not bypass its gate')
            if (base/'STOP').exists(): raise RuntimeError('STOP requested')
            time.sleep(30)
        else: raise TimeoutError('Deadline before singles completion')
        if os.name == 'nt': ctypes.windll.kernel32.SetThreadExecutionState(0x80000001)
        phase('single_cell_findings',[sys.executable,str(ROOT/'scripts/pcdr_local_findings.py'),'--study',str(singles)],120)
        features = str(pilot/'analysis/features.parquet')
        phase('modes',[sys.executable,'-m','eigencircuits.build_modes','--features',features,'--out',str(modes)],7200)
        if read_json(modes/'selection.json')['status'] != 'selected':
            status.update(status='complete_no_eligible_mode',finding='Prespecified sugar-context mode selection failed',updated_utc=now())
            atomic_json(statefile,status); return
        # Full matching is required even for this reduced pilot. No relaxed fallback.
        expression = 'from eigencircuits.controls import generate; generate('+repr(features)+','+repr(str(modes))+','+repr(str(controls))+',full=True,n_sets=5)'
        phase('matching',[sys.executable,'-c',expression],3600)
        phase('prepare',[sys.executable,str(Path(__file__).resolve()),'--action','prepare'],60)
        remaining_hours = max(.01,(deadline-time.time())/3600)
        phase('pilot',[sys.executable,str(ROOT/'scripts/pcdr_local_queue.py'),'--study',str(study),
                       '--features',features,'--hours',str(remaining_hours)],max(1,deadline-time.time()))
        phase('summarize',[sys.executable,str(Path(__file__).resolve()),'--action','summarize'],60)
        phase('mode_findings',[sys.executable,str(ROOT/'scripts/pcdr_local_findings.py'),'--study',str(study)],120)
        status.update(status='complete_local_mode_pilot',updated_utc=now(),claim_status='exploratory_not_confirmation')
        atomic_json(statefile,status)
    except BaseException as error:
        status.update(status='stopped',error=repr(error),updated_utc=now());atomic_json(statefile,status)
        raise
    finally:
        if os.name=='nt': ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)
        lock.unlink(missing_ok=True)


if __name__=='__main__': main()
