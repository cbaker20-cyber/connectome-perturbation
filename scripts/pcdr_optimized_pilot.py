"""Frozen descriptive pilot of optimized comparison sets; no reference p-values."""
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from eigencircuits.common import atomic_json, now, read_json, sha256, provenance, sugar_ids
from scripts.pcdr_local_queue import write

STUDY=ROOT/'results/pcdr/optimized_pilot_20260921'
PILOT=ROOT/'results/pcdr/corrected_20260919'
AUDIT=ROOT/'results/pcdr/matching_audit_20260921'
MODE=ROOT/'results/pcdr/exploratory80_20260921/modes/selection.json'
FEATURES=PILOT/'analysis/features.parquet'


def prepare():
    import numpy as np
    import pandas as pd
    from eigencircuits.controls import FULL_FEATURES, standardized_difference
    STUDY.mkdir(exist_ok=False)
    ids=read_json(MODE)['root_ids'];members=pd.read_parquet(AUDIT/'witness/members.parquet')
    validation=read_json(AUDIT/'independent_validation.json')
    for relative,expected in validation['inputs'].items():
        assert sha256(ROOT/relative)==expected
    assert read_json(ROOT/'results/pcdr/ccr_singles_20260919/summary.json')['status']=='complete'
    f=pd.read_parquet(FEATURES).set_index('root_id');f.index=f.index.astype(str)
    target=f.loc[ids];seen=set();balances=[]
    conditions=[{'name':'baseline','ids':[],'role':'baseline'}, {'name':'mode','ids':ids,'role':'mode'}]
    for number,g in members.groupby('witness'):
        names=g.root_id.astype(str).tolist();key=tuple(sorted(names));sample=f.loc[names]
        assert len(names)==len(set(names))==len(ids) and key not in seen
        assert not set(names)&(set(ids)|set(sugar_ids()))
        assert Counter(zip(target.model_sign,target.recruited))==Counter(zip(sample.model_sign,sample.recruited))
        smd=standardized_difference(np.log1p(target[FULL_FEATURES].to_numpy(float)),np.log1p(sample[FULL_FEATURES].to_numpy(float)))
        assert np.isfinite(smd).all() and np.all(smd<=.1)
        balances.append(dict(zip(FULL_FEATURES,map(float,smd))));seen.add(key)
        conditions.append({'name':f'optimized_{number:03}','ids':names,'role':'optimized_comparison'})
    assert len(seen)==5
    seeds=list(range(630901,630906))
    # No earlier trial used these planned but previously unlaunched seeds.
    prior=[p for p in (ROOT/'results/pcdr').glob('*/trials/*/manifest.json')
           if read_json(p).get('seed') in seeds]
    assert not prior, 'Fresh-seed check failed'
    deadline=read_json(ROOT/'results/pcdr/exploratory80_20260921/amendment.json')['deadline_epoch']
    timings=[read_json(p)['wall_seconds'] for p in (ROOT/'results/pcdr/ccr_singles_20260919/trials').glob('*/manifest.json')]
    record={'recorded_utc':now(),'authorization':'User asked whether to start testing after approving the matching audit.',
        'question':'Descriptively compare the selected mode lesion with five optimized matched comparison lesions under sugar drive.',
        'claim_status':'descriptive_optimized_comparisons_not_confirmation',
        'primary_readouts':'A = mean absolute mean paired DeltaHz inside own support; F = own-support share of total absolute mean paired DeltaHz. Zero total response makes F undefined.',
        'secondary':'MN9, motor total and per-neuron DeltaHz, signed and off-support effects. Model readouts, not behavior.',
        'analysis':'Show all six lesion sets and all five paired seeds. Paired-seed bootstrap intervals describe seed variability. No Monte Carlo reference p-values, no significance claim, no stopping on effect direction.',
        'selection':'Frozen rank-33 exploratory support and five audit witness sets; seed 630610 optimization objectives. No substitution, rematching or extra eigenpairs.',
        'seeds':seeds,'trials':35,'deadline_epoch':deadline,
        'simulation':'Unchanged NumPy LIF, output-only lesions, 21 sugar inputs at 150 Hz, 1 second, dt 0.1 ms, paired fixed_binomial_tape_v1.',
        'resources':'One serial simulation process, BLAS threads 1, >=4 GiB free RAM, >=10 GiB free disk; original Monday deadline. Stop on failure, STOP or deadline; retain incomplete work without calling it complete.',
        'estimated_hours_median_prior':float(np.median(timings)*35/3600),
        'estimated_hours_p95_prior':float(np.quantile(timings,.95)*35/3600),
        'balances':balances,'limitations':'Optimized sets are not uniform random draws; overlap allowed and recorded. Five seeds and five comparators are exploratory. Confirmation sampling remains unresolved.',
        'inputs':{str(p.relative_to(ROOT)):sha256(p) for p in [FEATURES,MODE,AUDIT/'witness/members.parquet',AUDIT/'witness/protocol.json',Path(__file__)]}}
    atomic_json(STUDY/'amendment.json',record)
    variant={'name':'default','weight_scale':1.,'inhibitory_scale':1.,'strong_fraction':None}
    jobs=[]
    for seed in seeds:
        for c in conditions:
            jobs.append({'index':len(jobs),'condition':c['name'],'role':c['role'],'lesion_ids':c['ids'],
                         'seed':seed,'variant':variant,'trial_id':f"default_{c['name']}_{seed}"})
    atomic_json(STUDY/'jobs.json',{'phase':'optimized_matching_pilot','claim_status':record['claim_status'],
        'created_utc':now(),'backend':'numpy','n_jobs':len(jobs),'jobs':jobs,'conditions':conditions,
        'variants':[variant],'seeds':seeds,'provenance':provenance(),
        'selection_sha256':sha256(PILOT/'analysis/selection.json'),'features_sha256':sha256(FEATURES),
        'mode_sha256':sha256(MODE),'amendment_sha256':sha256(STUDY/'amendment.json'),'status':'prepared_not_submitted'})
    write(STUDY/'local_status.json',{'started_utc':now(),'deadline_epoch':deadline,'status':'starting','completed':0,'total':35})
    print(json.dumps({'prepared':35,'estimated_hours':record['estimated_hours_median_prior'],'p95_hours':record['estimated_hours_p95_prior']}))


def run():
    lock=STUDY/'supervisor.lock'
    with lock.open('x') as f:f.write(str(os.getpid()))
    state={'status':'running','pid':os.getpid(),'started_utc':now()}
    write(STUDY/'supervisor_status.json',state)
    try:
        command=[sys.executable,str(ROOT/'scripts/pcdr_local_queue.py'),'--study',str(STUDY),'--features',str(FEATURES)]
        with (STUDY/'queue.log').open('a',encoding='utf-8') as log:
            log.write(now()+' '+json.dumps(command)+'\n');log.flush()
            subprocess.run(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
        if read_json(STUDY/'local_status.json')['status']!='complete':
            state['status']='stopped_incomplete';return
        summary=read_json(STUDY/'summary.json');assert summary['primary']==[]
        from scripts.pcdr_local_findings import report
        report(STUDY)
        with (STUDY/'FINDINGS.md').open('a',encoding='utf-8') as f:
            f.write('\nOptimized comparison sets: descriptive pilot only. No calibrated random-reference p-values. See amendment.json for the frozen design and matching audit for set overlap.\n')
        manifest=read_json(STUDY/'findings_manifest.json')
        manifest.update(report_sha256=sha256(STUDY/'FINDINGS.md'),supervisor_sha256=sha256(__file__))
        atomic_json(STUDY/'findings_manifest.json',manifest)
        state['status']='complete_descriptive_pilot'
    except BaseException as error:
        state.update(status='failed',error=repr(error));raise
    finally:
        state['updated_utc']=now();write(STUDY/'supervisor_status.json',state);lock.unlink(missing_ok=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--prepare',action='store_true');args=p.parse_args()
    prepare() if args.prepare else run()
