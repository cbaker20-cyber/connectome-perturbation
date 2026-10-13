"""Prospective two-worker recovery on the existing long allocation; frozen science."""
import os
import sys
from pathlib import Path
import time
import signal
import subprocess
import shutil
import zipfile

ROOT = Path(os.environ.get('PCDR_PACKAGE', '/user/cbaker4/connectome_four_trial'))
sys.path.insert(0, str(ROOT))
from scripts.pcdr_four_trial import batch
from scripts.pcdr_smaller_pilot import package_plan, interrupted
from eigencircuits.common import atomic_json, read_json, environment, now


def fits(measures, remaining):
    import math
    if len(measures) != 2:
        raise ValueError('Require both concurrent probes')
    for m in measures:
        if m['status'] != 'complete' or m['duration_s'] != .01 or m['dt_ms'] != .00005:
            raise ValueError('Wrong or incomplete capacity probe')
        if not math.isfinite(m['seconds']) or m['seconds'] <= 0 or not 0 < m['peak_rss_bytes'] <= 16e9:
            raise ValueError('Invalid measured resources')
    estimate = 200*max(m['seconds'] for m in measures)
    return {'allowed': remaining >= estimate, 'per_trial_screen_seconds': estimate,
            'remaining_seconds': remaining, 'workers': 2, 'margin_factor': 2,
            'scope': 'Complete baseline/mode pair at0.00005ms; no promise of both final halvings.'}


def main():
    from scripts.pcdr_ccr_capacity import allocation
    from scripts.pcdr_resolution import seconds_left
    from scripts.pcdr_fine_ccr import checked, collect
    plan = package_plan()
    if os.environ.get('SLURM_JOB_ID') != '26427314' or not os.uname().nodename.startswith('cpn-c04-18'):
        raise ValueError('Wrong allocation/node')
    cpus, memory = allocation()
    if cpus < 4 or memory < 64000:
        raise ValueError('Require4available CPUs and64GB for two workers')
    if sys.version_info[:3] != (3, 11, 5) or environment()['packages'] != plan['packages']:
        raise ValueError('Environment does not match frozen study')
    out = ROOT/'recovery_pair_20261013'
    out.mkdir(exist_ok=False)
    import fcntl
    lock = (ROOT/'.recovery_pair.lock').open('w')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    slurm = subprocess.check_output(['squeue', '-h', '-j', '26427314', '-o', '%L'], text=True, timeout=20)
    deadline = time.monotonic()+min(54*3600, seconds_left(slurm)-1200)
    status = dict(status='running', phase='reference', started_utc=now(), job_id='26427314',
                  host=os.uname().nodename, cpus=cpus, memory_mb=memory, scientific_completed=0,
                  scope='seed631401 baseline/mode at0.00005ms,1second', original_criteria_unchanged=True)
    def update(records):
        status.update(processes=records, updated_utc=now())
        atomic_json(out/'progress.json', status)
    def commands(kind, dt, names):
        return [(name, [sys.executable, str(ROOT/'scripts/pcdr_four_trial.py'), 'child',
                       str(ROOT/'scripts/pcdr_smaller_pilot.py'), 'prefix', '--out', str(out/name),
                       '--kind', k, '--dt', str(dt)]) for name, k in zip(names, kind)]
    previous = signal.signal(signal.SIGTERM, interrupted)
    selected = [(i, j) for i,j in enumerate(plan['jobs']) if j['seed']==631401 and j['dt_ms']==.00005]
    if len(selected)!=2 or {j['condition'] for _,j in selected}!={'baseline','mode'}:
        raise ValueError('Pair identity mismatch')
    try:
        (out/'allocation.txt').write_text(subprocess.check_output(['scontrol','show','job','26427314'],text=True,timeout=20))
        shutil.copyfile(Path(__file__), out/'recovery_source.py')
        atomic_json(out/'execution_amendment.json', dict(status, reason='Four-worker gate blocked all work; prioritize complete pair with measured two-worker performance',
            deadline_reserve_seconds=1200, max_hours=54, memory_limit_per_worker=20_000_000_000,
            frozen_plan_sha256=__import__('hashlib').sha256((ROOT/'smaller_plan.json').read_bytes()).hexdigest()))
        refs = ['reference_baseline','reference_mode']
        records = batch(commands(refs,.0001,refs),out/'logs/references',min(deadline,time.monotonic()+3600),update)
        if any(r['returncode'] for r in records):raise RuntimeError('Reference worker failed')
        for name in refs:
            m=read_json(out/name/'measurement.json')
            if m['status']!='complete' or not m['exact_reference']:raise ValueError('Reference not verified')
        status['phase']='capacity'
        names=['probe_a','probe_b']
        records=batch(commands(['probe','probe'],.00005,names),out/'logs/capacity',min(deadline,time.monotonic()+7200),update)
        if any(r['returncode'] for r in records):raise RuntimeError('Capacity worker failed')
        decision=fits([read_json(out/n/'measurement.json') for n in names],deadline-time.monotonic())
        atomic_json(out/'capacity_gate.json',decision)
        if not decision['allowed']:
            status.update(status='budget_insufficient',phase='stopped')
            return
        status['phase']='scientific'
        work=[(j['id'],[sys.executable,str(ROOT/'scripts/pcdr_four_trial.py'),'child',str(ROOT/'scripts/pcdr_smaller_pilot.py'),
                      'worker','--out',str(out),'--index',str(i)]) for i,j in selected]
        records=batch(work,out/'logs/scientific',deadline,update)
        if any(r['returncode'] for r in records):raise RuntimeError('Scientific worker failed')
        for _,j in selected:checked(out/'trials'/j['id'],j)
        anchors=[j for j in plan['anchors'] if j['seed']==631401]
        for j in anchors:shutil.copytree(ROOT/'anchors'/j['id'],out/'trials'/j['id'])
        collect(out,dict(plan,jobs=anchors+[j for _,j in selected],steps_ms=[.0001,.00005]))
        a=read_json(out/'step_agreement.json')
        a.pop('final_two_halvings_meet_declared_criteria',None)
        for g in a['groups']:g['single_pair_meets_thresholds']=g.pop('meets_declared_criteria')
        a.update(original_30_seed_requirement_established=False,interpretation='One seed and one halving only; full convergence not evaluated.')
        atomic_json(out/'step_agreement.json',a)
        status.update(status='pair_complete',phase='finished')
    except BaseException as error:
        status.update(status='failed_or_interrupted',error=repr(error))
        raise
    finally:
        completed=[]
        for _,j in selected:
            p=out/'trials'/j['id']/'manifest.json'
            if p.exists() and read_json(p).get('status')=='complete':
                try:checked(p.parent,j);completed.append(j['id'])
                except (OSError,ValueError,KeyError) as error:status.setdefault('verification_errors',[]).append(str(error))
        status.update(scientific_completed=len(completed),completed_ids=completed,finished_utc=now())
        atomic_json(out/'progress.json',status)
        with zipfile.ZipFile(ROOT/'CCR_recovery_pair_20261013.zip','x',zipfile.ZIP_DEFLATED) as z:
            for p in out.rglob('*'):
                if p.is_file():z.write(p,'results/'+p.relative_to(out).as_posix())
            for n in ('package_manifest.json','smaller_plan.json','execution_plan.json'):z.write(ROOT/n,'package/'+n)
        signal.signal(signal.SIGTERM,previous)
        lock.close()


if __name__=='__main__':main()
