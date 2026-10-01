"""Run the frozen fine-step study and retain complete or interrupted results."""
import os
for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[key] = '1'
os.environ['MPLBACKEND'] = 'Agg'
import argparse
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from pathlib import Path
import shutil
import subprocess
import sys
import time
import zipfile
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np
import pandas as pd
from eigencircuits.common import environment, neuron_ids
from scripts.pcdr_ccr_transfer import read, write, digest, utc
from scripts.pcdr_ccr_capacity import allocation
from scripts.pcdr_bounded_process import run_bounded
from scripts import pcdr_resolution as resolution
from scripts.pcdr_fine_sim import simulate, input_tape


def notebook_content(document):
    return [[cell['cell_type'], ''.join(cell['source'])] for cell in document['cells']]


def verify_package():
    manifest = read(ROOT / 'package_manifest.json')
    for name, expected in manifest.items():
        if name == 'CCR_Fine_Steps.ipynb':
            continue
        if digest(ROOT / name) != expected:
            raise ValueError('Changed package file: ' + name)
    if 'notebook_content.json' not in manifest:
        raise ValueError('Missing frozen notebook source record')
    if notebook_content(read(ROOT / 'CCR_Fine_Steps.ipynb')) != read(ROOT / 'notebook_content.json'):
        raise ValueError('Notebook cell source changed; saved outputs and metadata are allowed')


def checked(directory, spec):
    record = read(directory / 'manifest.json')
    if record['status'] != 'complete' or record['spec'] != spec:
        raise ValueError('Incomplete or different trial: ' + spec['id'])
    if set(record['outputs']) != {'spikes.parquet', 'rates.parquet', 'delivered_events.parquet', 'population.json'}:
        raise ValueError('Missing trial outputs')
    for name, expected in record['outputs'].items():
        if digest(directory / name) != expected:
            raise ValueError('Changed trial output: ' + str(directory / name))
    return record


def worker(out, index):
    plan = read(ROOT / 'fine_plan.json')
    spec = plan['jobs'][index]
    # Reuse the established output checks and readouts, changing only the replay recorder.
    resolution.simulate = simulate
    resolution.input_tape = input_tape
    resolution.worker(ROOT / 'original', out / 'trials' / spec['id'], spec)


def agreement(coarse, fine, support):
    from eigencircuits.readouts import footprint
    a, b = footprint(coarse, support), footprint(fine, support)
    relative = float(np.abs(coarse - fine).sum() / max(1., np.abs(fine).sum()))
    f_diff = None if a['F'] is None or b['F'] is None else abs(a['F'] - b['F'])
    passed = abs(a['A'] - b['A']) <= max(1., .05 * b['A']) and f_diff is not None and f_diff <= .01 and relative <= .05
    return {'A_difference_hz': abs(a['A'] - b['A']), 'F_difference': f_diff,
            'response_relative_L1': relative, 'passes_response': bool(passed)}


def collect(out, plan):
    resolution.collect(out, plan)
    ids = neuron_ids(); lookup = {v:i for i,v in enumerate(ids)}
    jobs = {(j['dt_ms'], j['variant'], j['condition'], j['seed']):j for j in plan['jobs'] if j['stage'] != 'replay'}
    rows = []
    means = {}
    for coarse, fine in zip(plan['steps_ms'][:-1], plan['steps_ms'][1:]):
        for key, job in jobs.items():
            dt, variant, condition, seed = key
            if dt != fine or condition == 'baseline':
                continue
            vectors, populations = [], []
            for step in [coarse, fine]:
                lesion = out/'trials'/jobs[step,variant,condition,seed]['id']
                base = out/'trials'/jobs[step,variant,'baseline',seed]['id']
                vectors.append(resolution.rates(lesion/'rates.parquet',ids)-resolution.rates(base/'rates.parquet',ids))
                populations.append([np.asarray(read(p/'population.json')) for p in [base,lesion]])
            support = [lookup[v] for v in job['lesion_ids']]
            result = agreement(*vectors, support)
            temporal = max(float(abs(a-b).sum()/max(1.,abs(b).sum())) for a,b in zip(*populations))
            result.update(coarse_ms=coarse, fine_ms=fine, variant=variant, condition=condition, seed=seed,
                          population_relative_L1=temporal, passes=bool(result['passes_response'] and temporal<=.05))
            rows.append(result)
            means.setdefault((coarse,fine,variant,condition),[]).append((vectors,support))
    pd.DataFrame(rows).to_csv(out/'step_agreement.csv',index=False)
    groups = []
    for key, values in means.items():
        vectors = np.mean([v[0] for v in values],axis=0)
        result = agreement(*vectors,values[0][1])
        group = [r for r in rows if (r['coarse_ms'],r['fine_ms'],r['variant'],r['condition'])==key]
        fraction = sum(r['passes'] for r in group)/len(group)
        result.update(coarse_ms=key[0],fine_ms=key[1],variant=key[2],condition=key[3],n=len(group),fraction_passing=fraction,
                      meets_declared_criteria=bool(result['passes_response'] and fraction>=.95))
        groups.append(result)
    final_steps=plan['steps_ms'][-2:]
    final_groups=[g for g in groups if g['fine_ms'] in final_steps]
    final_pass=(all(g['meets_declared_criteria'] for g in final_groups) if len(plan['steps_ms'])>=3 and final_groups else None)
    write(out/'step_agreement.json',{'groups':groups,'final_two_halvings_meet_declared_criteria':final_pass,'criteria':plan['criteria'],
        'interpretation':'Numerical agreement under declared tolerances only. Examine both final successive halvings; no proof of continuous-time convergence or biological validity.'})


def archive(out):
    destination = out.parent/'CCR_fine_results.zip'
    temporary = destination.with_suffix('.zip.tmp')
    with zipfile.ZipFile(temporary,'w',zipfile.ZIP_DEFLATED,compresslevel=1) as z:
        for path in sorted(out.rglob('*')):
            if path.is_file() and path.name != 'controller.lock':
                z.write(path,path.relative_to(out))
        for name in ['fine_plan.json','package_manifest.json','requirements-ccr.txt','notebook_content.json','run_all.sh','CCR_Fine_Steps.ipynb','START_HERE.md']:
            z.write(ROOT/name,'package/'+name)
        for folder in ['scripts','eigencircuits']:
            for path in sorted((ROOT/folder).glob('*.py')):
                z.write(path,'package/'+path.relative_to(ROOT).as_posix())
        z.write(ROOT/'model.py','package/model.py')
        if (ROOT/'run_all.log').exists():z.write(ROOT/'run_all.log','run_all.log')
    with zipfile.ZipFile(temporary) as z:
        bad = z.testzip()
        if bad: raise ValueError('Invalid result archive member: '+bad)
    os.replace(temporary,destination)
    print('Download '+str(destination),flush=True)


def ceiling(cpus, memory_mb, peak=4_000_000_000):
    return max(0,min(60,cpus-2,int((memory_mb*1_000_000-16_000_000_000)/max(8_000_000_000,1.5*peak))))


def run(out, hours):
    if not 0 < hours <= 72: raise ValueError('Hours must be in (0,72]')
    verify_package()
    cpus,memory = allocation()
    cap=ceiling(cpus,memory)
    if cap<1: raise ValueError('Insufficient allocated CPU or memory')
    remaining=resolution.seconds_left(subprocess.check_output(['squeue','-h','-j',os.environ['SLURM_JOB_ID'],'-o','%L'],text=True))
    budget=min(hours*3600,remaining-1800)
    if budget<3600: raise ValueError('Need more than 90 minutes remaining')
    deadline=time.monotonic()+budget
    plan=read(ROOT/'fine_plan.json')
    expected=read(ROOT/'original/jobs.json')['provenance']['environment']['packages']
    current=environment()
    if sys.version_info[:2]!=(3,11) or current['packages']!=expected:
        raise ValueError('Simulation environment differs; use the supplied dedicated Python 3.11 environment')
    out.mkdir(parents=True,exist_ok=True)
    lock=out/'controller.lock'
    with lock.open('x') as f: f.write(f'{os.getpid()} Slurm {os.environ["SLURM_JOB_ID"]}\n')
    status={'status':'running','started_utc':utc(),'completed':0,'total':len(plan['jobs']),
            'environment':current,'slurm_job_id':os.environ['SLURM_JOB_ID'],'workers':1}
    try:
        if (out/'plan.json').exists() and read(out/'plan.json')!=plan: raise ValueError('Different prior plan')
        history=out/'controller_history'/str(time.time_ns())
        for name in ['progress.json','capacity.json']:
            if (out/name).exists():
                history.mkdir(parents=True,exist_ok=True)
                shutil.copy2(out/name,history/name)
        write(out/'plan.json',plan)
        pd.DataFrame({'root_id':neuron_ids()}).to_csv(out/'neurons.csv',index=False)
        write(out/'progress.json',status)
        def execute(index):
            spec=plan['jobs'][index]; directory=out/'trials'/spec['id']
            if directory.exists():
                record=read(directory/'manifest.json') if (directory/'manifest.json').exists() else {}
                if record.get('status')=='complete':
                    checked(directory,spec)
                    return spec['id']
                # An interrupted attempt is evidence. Keep it before restarting this job.
                saved=out/'interrupted'/(spec['id']+'_'+str(time.time_ns()))
                saved.parent.mkdir(exist_ok=True)
                directory.rename(saved)
            seconds=deadline-time.monotonic()
            if seconds<=0: raise TimeoutError('Allocation budget reached')
            logs=out/'logs'/spec['id']/str(time.time_ns())
            result=run_bounded([sys.executable,str(Path(__file__)),'worker','--out',str(out),'--index',str(index)],logs,seconds,cwd=ROOT)
            write(logs/'process.json',result)
            if result['returncode'] or result['timed_out']: raise RuntimeError('Worker failed: '+spec['id'])
            checked(directory,spec)
            return spec['id']
        if all((out/'trials'/j['id']/'manifest.json').exists() and read(out/'trials'/j['id']/'manifest.json').get('status')=='complete' for j in plan['jobs']):
            for spec in plan['jobs']: checked(out/'trials'/spec['id'],spec)
            collect(out,plan)
            status.update(status='complete',completed=len(plan['jobs']),finished_utc=utc(),active=0)
            write(out/'progress.json',status)
            return
        # Exact replays must pass before any fine-step outcomes are generated.
        for i,j in enumerate(plan['jobs']):
            if j['stage']=='replay':
                execute(i); status['completed']+=1
        write(out/'progress.json',status)
        # Measure contention on fixed short prefixes; outcomes do not choose concurrency.
        waves=[]; peak=4_000_000_000
        for n in sorted(set([1]+[x for x in [8,32,60] if x<=cap]+[cap])):
            if n>ceiling(cpus,memory,peak): break
            start=time.perf_counter()
            def probe(k):
                target=out/'capacity'/str(time.time_ns())/str(k)
                target.mkdir(parents=True)
                result=run_bounded([sys.executable,str(Path(__file__)),'probe','--out',str(target)],target/'logs',min(3600,max(1,deadline-time.monotonic())),cwd=ROOT)
                write(target/'process.json',result)
                if result['returncode'] or result['timed_out']: raise RuntimeError('Capacity check failed')
                return read(target/'measurement.json')['peak_rss_bytes']
            with ThreadPoolExecutor(max_workers=n) as pool: measurements=list(pool.map(probe,range(n)))
            peak=max(peak,*measurements); elapsed=time.perf_counter()-start
            waves.append({'workers':n,'seconds':elapsed,'trials_per_second':n/elapsed,'peak_bytes':max(measurements)})
            write(out/'capacity.json',{'waves':waves})
            print('Capacity:',waves[-1],flush=True)
        safe=[w for w in waves if w['workers']<=ceiling(cpus,memory,peak)]
        if not safe: raise ValueError('No measured concurrency fits the allocation')
        best=max(w['trials_per_second'] for w in safe)
        workers=min(w['workers'] for w in safe if w['trials_per_second']>=.9*best)
        write(out/'capacity.json',{'waves':waves,'selected_workers':workers,'memory_mb':memory,'cpus':cpus,
            'limits':'Short prefix throughput; full-run memory uses at least 8 GB reserved per worker.'})
        status['workers']=workers
        pending=[i for i,j in enumerate(plan['jobs']) if j['stage']!='replay']
        # Fixed first seeds and difficult examples finish before the remaining seed panel.
        pending.sort(key=lambda i:(plan['jobs'][i]['seed'] not in [631401,631405,631430],-plan['jobs'][i]['dt_ms']))
        with ThreadPoolExecutor(max_workers=workers) as pool:
            running={}; cursor=0
            while cursor<len(pending) or running:
                while cursor<len(pending) and len(running)<workers:
                    if time.monotonic()>=deadline: raise TimeoutError('Allocation budget reached')
                    index=pending[cursor];cursor+=1
                    running[pool.submit(execute,index)]=index
                done,_=wait(running,timeout=30,return_when=FIRST_COMPLETED)
                for future in done:
                    name=future.result();del running[future];status['completed']+=1
                    print(f'{status["completed"]}/{status["total"]}: {name}',flush=True)
                status['updated_utc']=utc();status['active']=len(running)
                write(out/'progress.json',status)
        collect(out,plan)
        status.update(status='complete',finished_utc=utc(),active=0)
        write(out/'progress.json',status)
    except BaseException as error:
        status.update(status='interrupted_or_failed',error=repr(error),finished_utc=utc())
        write(out/'progress.json',status)
        raise
    finally:
        try: archive(out)
        finally: lock.unlink()


def probe(out):
    from eigencircuits.memory import peak_rss
    source=ROOT/'original/trials/default_baseline_631401'
    manifest=read(source/'manifest.json'); ids=neuron_ids();lookup={v:i for i,v in enumerate(ids)}
    events=pd.read_parquet(source/'input_events.parquet');events=events[events.tick<100]
    started=time.monotonic()
    frames=simulate(631401,[lookup[v] for v in manifest['input_ids']],[],
        tape=input_tape(events,manifest['input_ids'],.0001,.01),duration_s=.01,dt_ms=.0001,chunk_ms=1.,return_delivered=True)
    pd.testing.assert_frame_equal(frames[1],frames[2])
    write(out/'measurement.json',{'seconds':time.monotonic()-started,'peak_rss_bytes':peak_rss(),'spikes':len(frames[0])})


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['run','worker','probe','collect'])
    p.add_argument('--out',type=Path,default=ROOT/'fine_results');p.add_argument('--hours',type=float,default=70.)
    p.add_argument('--index',type=int)
    a=p.parse_args();a.out=a.out.resolve()
    if a.action=='run':run(a.out,a.hours)
    elif a.action=='worker':worker(a.out,a.index)
    elif a.action=='probe':probe(a.out)
    else:
        collect(a.out,read(ROOT/'fine_plan.json'));archive(a.out)
