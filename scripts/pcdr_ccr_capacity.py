"""Measure throughput on planned trials before choosing within-allocation concurrency."""
import os
from pathlib import Path
import sys
import time
import concurrent.futures
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.pcdr_ccr_transfer import read,write,digest,utc,load_plan
from scripts.pcdr_bounded_process import run_bounded


def ceiling(cpus,memory_mb,peak_bytes):
    if min(cpus,memory_mb,peak_bytes)<=0:raise ValueError('Invalid allocation or memory measurement')
    # Keep two CPUs and 12 GB for Jupyter/analysis; 50% headroom per worker.
    count=min(24,cpus-2,int((memory_mb*1_000_000-12_000_000_000)/(peak_bytes*1.5)))
    if count<1:raise ValueError('Allocation too small for this expanded workflow')
    return count


def allocation():
    if not os.environ.get('SLURM_JOB_ID'):raise ValueError('Calibration must run inside the CCR allocation')
    cpus=int(os.environ['SLURM_CPUS_ON_NODE'])
    if hasattr(os,'sched_getaffinity'):cpus=min(cpus,len(os.sched_getaffinity(0)))
    if os.environ.get('SLURM_MEM_PER_NODE'):
        memory=int(os.environ['SLURM_MEM_PER_NODE'])
    elif os.environ.get('SLURM_MEM_PER_CPU'):
        memory=int(os.environ['SLURM_MEM_PER_CPU'])*cpus
    else:raise ValueError('Slurm memory allocation unavailable; inspect job environment')
    return cpus,memory


def check_certificate(study,workers):
    study=Path(study);c=read(study/'capacity.json')
    cpus,memory=allocation()
    if c['jobs_sha256']!=digest(study/'jobs.json') or c['slurm_job_id']!=os.environ['SLURM_JOB_ID']:
        raise ValueError('Recalibrate after changing the study or allocation')
    if workers>c['selected_workers'] or workers>ceiling(cpus,memory,c['peak_rss_bytes']):
        raise ValueError('Concurrency exceeds measured allocation capacity')


def calibrate(study,smoke):
    from scripts.pcdr_ccr_sensitivity import validated
    study=Path(study).resolve();plan=load_plan(study)
    cpus,memory=allocation()
    smoke_plan=load_plan(smoke)
    from scripts.pcdr_ccr_transfer import checked_trial
    peak=max(checked_trial(Path(smoke)/'trials'/j['trial_id'],j,smoke_plan)['peak_rss_bytes'] for j in smoke_plan['jobs'])
    cap=ceiling(cpus,memory,peak)
    lock=study/'controller.lock'
    with lock.open('x') as stream:stream.write(str(os.getpid()))
    waves=[];cursor=0
    try:
        # Use real pending jobs, spread over the grid; retain all completed outputs.
        pending=[]
        for job in plan['jobs']:
            directory=study/'trials'/job['trial_id']
            if (directory/'manifest.json').exists():
                try: validated(directory,job,plan);continue
                except (ValueError,FileNotFoundError):pass
            pending.append(job)
        import random
        random.Random(631550).shuffle(pending)
        candidates=sorted(set([1]+[n for n in [4,8,16,24] if n<=cap]+[cap]))
        for n in candidates:
            if (study/'STOP').exists():raise RuntimeError('Calibration stopped')
            if n>ceiling(cpus,memory,peak):break
            jobs=pending[cursor:cursor+n];cursor+=n
            if len(jobs)<n:break
            start=time.monotonic()
            def execute(job):
                result=run_bounded([sys.executable,str(ROOT/'scripts/pcdr_ccr_sensitivity.py'),'worker',
                    '--study',str(study),'--index',str(job['index'])],study/'calibration_logs'/job['trial_id'],600,cwd=ROOT)
                if result['returncode']!=0:raise RuntimeError('Calibration worker failed; inspect logs')
                m=validated(study/'trials'/job['trial_id'],job,plan)
                return m['peak_rss_bytes']
            with concurrent.futures.ThreadPoolExecutor(max_workers=n) as pool:
                rss=list(pool.map(execute,jobs))
            seconds=time.monotonic()-start;peak=max(peak,*rss)
            waves.append({'workers':n,'wall_seconds':seconds,'trials_per_second':n/seconds,
                          'peak_worker_rss_bytes':max(rss),'indices':[j['index'] for j in jobs]})
            write(study/'capacity_progress.json',{'waves':waves,'updated_utc':utc()})
            print(f'Calibration: {n} workers, {n/seconds:.3f} trials/s',flush=True)
        safe=[w for w in waves if w['workers']<=ceiling(cpus,memory,peak)]
        if pending:
            if not safe:raise ValueError('No successful safe calibration wave')
            best=max(w['trials_per_second'] for w in safe)
            chosen=min(w['workers'] for w in safe if w['trials_per_second']>=.9*best)
        else:
            chosen=1  # No trials remain; permit verification/collection without benchmarking again.
        write(study/'capacity.json',{'created_utc':utc(),'jobs_sha256':digest(study/'jobs.json'),
            'slurm_job_id':os.environ['SLURM_JOB_ID'],'cpus':cpus,'memory_mb':memory,
            'peak_rss_bytes':peak,'waves':waves,'selected_workers':chosen,
            'selection':'Smallest tested concurrency within 90% of the best observed throughput. Hardware-only choice; no outcome-based scientific selection.',
            'limits':'Short mixed-condition waves, not a precise scaling law or guarantee against all later memory peaks.'})
    finally:lock.unlink()


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--study',required=True);p.add_argument('--smoke',required=True)
    a=p.parse_args();calibrate(a.study,a.smoke)
