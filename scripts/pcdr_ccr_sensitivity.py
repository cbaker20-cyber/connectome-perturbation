"""Descriptive weight and MN9-dependence follow-up; no random-reference p-values."""
import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:
    os.environ[key]='1'
from pathlib import Path
import argparse
import concurrent.futures
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.pcdr_ccr_transfer import read,write,digest,utc,verify,load_plan,OUTPUTS
from scripts.pcdr_bounded_process import run_bounded

VARIANTS=[{'name':name,'weight_scale':w,'inhibitory_scale':i,'strong_fraction':None}
          for name,w,i in [('default',1.,1.),('weight_080',.8,1.),('weight_120',1.2,1.),
                           ('inhibition_080',1.,.8),('inhibition_120',1.,1.2)]]


def planned_jobs(conditions,variants=None,seeds=None):
    jobs=[]
    for variant in (VARIANTS if variants is None else variants):
        for seed in (range(631401,631411) if seeds is None else seeds):
            for condition in conditions:
                if condition.get('default_only') and variant['name']!='default':continue
                jobs.append({'index':len(jobs),'condition':condition['name'],'seed':seed,
                             'lesion_ids':sorted(condition['ids']),'context':'sugar','variant':variant,
                             'trial_id':f"{variant['name']}_{condition['name']}_{seed}"})
    return jobs


def prepare(study,smoke):
    from scripts.pcdr_ccr_transfer import collect
    from eigencircuits.common import provenance,neuron_ids,sugar_ids,MN9
    verify(); collect(smoke)
    design=read(ROOT/'sensitivity_design.json')
    names=[c['name'] for c in design['conditions']]
    if names[:7]!=['baseline','mode','mode_without_mn9','mn9_only','motor_003','motor_004','motor_005'] or len(set(names))!=len(names):
        raise ValueError('Unexpected conditions')
    ids=set(neuron_ids()); sensory=set(sugar_ids())
    conditions=design['conditions']; byname={c['name']:set(c['ids']) for c in conditions}
    if len(byname['mode'])!=51 or byname['mode_without_mn9']!=byname['mode']-{MN9} or byname['mn9_only']!={MN9}:
        raise ValueError('Invalid MN9 decomposition')
    for c in conditions:
        if len(c['ids'])!=len(set(c['ids'])) or not set(c['ids'])<=ids or set(c['ids'])&sensory:
            raise ValueError('Invalid membership')
    variants=design.get('network_variants',VARIANTS)
    seeds=design['seeds']
    jobs=planned_jobs(conditions,variants,seeds)
    if len(jobs)!=design['trials']:raise ValueError('Design job count mismatch')
    study=Path(study); study.mkdir(parents=True,exist_ok=False)
    write(study/'jobs.json',{'created_utc':utc(),'claim_status':'post_pilot_descriptive_sensitivity',
        'transfer_sha256':digest(ROOT/'transfer_manifest.json'),'provenance':provenance(),
        'smoke_certificate_sha256':digest(Path(smoke)/'smoke_certificate.json'),
        'design':design,'variants':variants,'conditions':conditions,'jobs':jobs})


def validated(directory,job,plan):
    m=read(directory/'manifest.json')
    if m.get('status')!='complete': raise ValueError('Incomplete trial')
    for key in ['trial_id','seed','context','lesion_ids']:
        if m[key]!=job[key]: raise ValueError(f'Wrong {key}')
    for key in ['weight_scale','inhibitory_scale','strong_fraction']:
        if m[key]!=job['variant'][key]: raise ValueError('Wrong network variant')
    for key,value in {'backend':'numpy','duration_s':1.,'dt_ms':.1,'input_hz':150.,
                      'input_protocol':'fixed_binomial_tape_v1'}.items():
        if m[key]!=value: raise ValueError('Wrong simulation settings')
    for key in ['inputs','sources','environment']:
        if m['provenance'][key]!=plan['provenance'][key]: raise ValueError('Wrong provenance')
    if set(m['outputs'])!=OUTPUTS: raise ValueError('Missing output entries')
    for name,expected in m['outputs'].items():
        if digest(directory/name)!=expected: raise ValueError(f'Corrupt output: {name}')
    return m


def worker(study,index):
    from eigencircuits.trials import trial
    study=Path(study); plan=load_plan(study)
    if not 0<=index<len(plan['jobs']): raise ValueError('Invalid index')
    job=plan['jobs'][index]; lock=study/(job['trial_id']+'.lock')
    with lock.open('x') as stream: stream.write(f'{os.getpid()} {utc()}\n')
    try:
        trial(study/'trials'/job['trial_id'],job['trial_id'],job['seed'],
              context=job['context'],lesion_ids=job['lesion_ids'],backend='numpy',
              **{k:v for k,v in job['variant'].items() if k!='name'})
    finally: lock.unlink()


def run(study,workers=2,hours=3):
    if not 1<=workers<=24 or not 0<hours<=7: raise ValueError('Use 1-24 workers and at most 7 hours')
    study=Path(study).resolve(); plan=load_plan(study)
    if workers>2:
        from scripts.pcdr_ccr_capacity import check_certificate
        check_certificate(study,workers)
    lock=study/'controller.lock'
    with lock.open('x') as stream: stream.write(str(os.getpid()))
    end=time.monotonic()+hours*3600
    results=[]
    def execute(job):
        remaining=end-time.monotonic()
        if (study/'STOP').exists() or remaining<30: return {'index':job['index'],'status':'not_started'}
        result=run_bounded([sys.executable,str(Path(__file__)), 'worker','--study',str(study),
                            '--index',str(job['index'])],study/'logs'/job['trial_id'],min(600,remaining),cwd=ROOT)
        return {'index':job['index'],'status':'complete' if result['returncode']==0 else 'failed','execution':result}
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
            futures=[pool.submit(execute,job) for job in plan['jobs']]
            try:
                for future in concurrent.futures.as_completed(futures):
                    results.append(future.result())
                    write(study/'progress.json',{'updated_utc':utc(),'finished':len(results),'total':len(plan['jobs']),
                                                'results':sorted(results,key=lambda r:r['index'])})
                    print(f"Finished {len(results)}/{len(plan['jobs'])}",flush=True)
            except BaseException:
                (study/'STOP').touch()
                raise
    finally: lock.unlink()


def collect(study):
    import numpy as np
    import pandas as pd
    from eigencircuits.common import neuron_ids,MN9
    from eigencircuits.readouts import paired_deltas,footprint,bootstrap_footprint
    study=Path(study); plan=load_plan(study); ids=neuron_ids(); lookup={rid:i for i,rid in enumerate(ids)}
    if (study/'controller.lock').exists(): raise ValueError('Controller still active')
    manifests={}
    for job in plan['jobs']:
        if (study/(job['trial_id']+'.lock')).exists(): raise ValueError('Worker still active')
        directory=study/'trials'/job['trial_id']
        manifests[job['trial_id']]=validated(directory,job,plan)
        rates=pd.read_parquet(directory/'rates.parquet'); spikes=pd.read_parquet(directory/'spikes.parquet')
        if rates.root_id.astype(str).tolist()!=ids: raise ValueError('Neuron universe mismatch')
        actual=spikes.groupby('flywire_id').size().reindex(ids,fill_value=0).to_numpy()
        if not np.array_equal(actual,rates.spike_count) or not np.array_equal(actual,rates.rate_hz):
            raise ValueError('Rates inconsistent with spikes')
    rows=[]; per_seed=[]
    for variant in plan['variants']:
        def paths(name):
            return [study/'trials'/j['trial_id'] for j in plan['jobs']
                    if j['condition']==name and j['variant']==variant]
        for condition in plan['conditions'][1:]:
            if condition.get('default_only') and variant['name']!='default':continue
            delta,seeds=paired_deltas(paths('baseline'),paths(condition['name']),ids)
            support=[lookup[rid] for rid in condition['ids']]
            row={'variant':variant['name'],'condition':condition['name'],'n_pairs':len(seeds),
                 **footprint(delta.mean(0),support),**bootstrap_footprint(delta,support),
                 'mn9_delta_hz':float(delta[:,lookup[MN9]].mean())}
            rows.append(row)
            for values,seed in zip(delta,seeds):
                per_seed.append({'variant':variant['name'],'condition':condition['name'],'seed':seed,
                                 **footprint(values,support),'mn9_delta_hz':float(values[lookup[MN9]])})
    write(study/'results.json',{'finished_utc':utc(),'claim_status':'descriptive; no p-values; no biological replication',
                              'jobs_sha256':digest(study/'jobs.json'),'rows':rows})
    pd.DataFrame(per_seed).to_csv(study/'per_seed.csv',index=False)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['prepare','worker','run','collect'])
    p.add_argument('--study',required=True);p.add_argument('--smoke');p.add_argument('--index',type=int)
    p.add_argument('--workers',type=int,default=2);p.add_argument('--hours',type=float,default=3)
    a=p.parse_args()
    if a.action=='prepare':
        if not a.smoke:p.error('--smoke required')
        prepare(a.study,a.smoke)
    elif a.action=='worker':
        if a.index is None:p.error('--index required')
        worker(a.study,a.index)
    elif a.action=='run':run(a.study,a.workers,a.hours)
    else:collect(a.study)


if __name__=='__main__':main()
