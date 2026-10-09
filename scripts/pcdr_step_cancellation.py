"""Decompose fixed-seed cross-step response disagreement into paired components."""
from pathlib import Path
import argparse
import json
import sys
import zipfile
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.pcdr_ccr_transfer import read,write,digest,utc


def decompose(baseline,lesion):
    a,b=np.asarray(baseline,float),np.asarray(lesion,float)
    if a.ndim!=1 or a.shape!=b.shape or not len(a) or not np.isfinite([a,b]).all():
        raise ValueError('Finite matching nonempty vectors required')
    response=b-a
    budget=np.abs(a)+np.abs(b)
    same=a*b>0
    cancellation=2*np.minimum(np.abs(a),np.abs(b))*same
    if not np.allclose(np.abs(response),budget-cancellation,rtol=0,atol=1e-10):
        raise ValueError('Decomposition identity failed')
    total=float(budget.sum())
    return dict(baseline_L1=float(np.abs(a).sum()),lesion_L1=float(np.abs(b).sum()),
        response_L1=float(np.abs(response).sum()),component_L1_sum=total,
        cancelled_L1=float(cancellation.sum()),cancelled_fraction=None if total==0 else float(cancellation.sum()/total),
        baseline_only_neurons=int(((a!=0)&(b==0)).sum()),lesion_only_neurons=int(((a==0)&(b!=0)).sum()),
        same_direction_neurons=int(same.sum()),opposite_direction_neurons=int((a*b<0).sum()),
        exact_cancellation_neurons=int(((a==b)&(a!=0)).sum()))


def run(out):
    source=ROOT/'results/pcdr/fine_download_20261005';verified=ROOT/'results/pcdr/fine_verified_20261005'
    check=read(verified/'full_check.json');archive=ROOT/'CCR_fine_results.zip'
    if check['status']!='complete' or digest(archive)!=check['archive_sha256'] or digest(source/'plan.json')!=check['plan_sha256']:
        raise ValueError('Unverified source')
    plan=read(source/'plan.json');conditions=['baseline','mode','motor_003','motor_004','motor_005'];steps=[.0008,.0004,.0002,.0001]
    jobs=[j for j in plan['jobs'] if j['stage']=='fine' and j['variant']=='default']
    keys={(j['seed'],j['dt_ms'],j['condition']):j for j in jobs};seeds=sorted({j['seed'] for j in jobs})
    expected={(s,d,c) for s in seeds for d in steps for c in conditions}
    if len(seeds)!=30 or len(keys)!=len(jobs) or set(keys)!=expected:raise ValueError('Unexpected trial coverage')
    out.mkdir(parents=True,exist_ok=False)
    write(out/'protocol.json',dict(recorded_utc=utc(),inputs={str(p):digest(p) for p in [Path(__file__),source/'plan.json',verified/'full_check.json',archive]},
        design='All 30 default seeds, four lesion conditions and three adjacent halvings. Read hash-verified full-neuron rates; define baseline and lesion cross-step differences coarse minus fine. Their difference equals paired-response disagreement. Decompose L1 into component budget minus same-sign cancellation. No new threshold, exclusions, inference or simulations.',
        limitations='Algebraic attribution, not causal separation. Four comparisons reuse each seed baseline. Stable aggregate response may hide individual variation. Original agreement decisions unchanged.'))
    rows=[];hashes={}
    with zipfile.ZipFile(archive) as z:
        if (source/'neurons.csv').read_bytes()!=z.read('neurons.csv'):raise ValueError('Changed neuron table')
        ids=pd.Index(pd.read_csv(source/'neurons.csv',dtype=str).root_id)
        if not ids.is_unique:raise ValueError('Duplicate neurons')
        for seed in seeds:
            rates={}
            for dt in steps:
                for condition in conditions:
                    j=keys[seed,dt,condition];m=json.loads(z.read('trials/'+j['id']+'/manifest.json'))
                    path=source/'trials'/j['id']/'rates.parquet'
                    if m['status']!='complete' or m['spec']!=j or digest(path)!=m['outputs']['rates.parquet']:raise ValueError('Changed rate evidence')
                    hashes[str(path)]=m['outputs']['rates.parquet']
                    f=pd.read_parquet(path)
                    if f.root_id.duplicated().any() or not f.root_id.map(lambda x:type(x) is str).all() or not set(f.root_id)<=set(ids):raise ValueError('Invalid IDs')
                    values=f.set_index('root_id').rate_hz.reindex(ids,fill_value=0).to_numpy(float)
                    if not np.isfinite(values).all() or (values<0).any():raise ValueError('Invalid rates')
                    rates[dt,condition]=values
            for coarse,fine in zip(steps[:-1],steps[1:]):
                a=rates[coarse,'baseline']-rates[fine,'baseline']
                for condition in conditions[1:]:
                    b=rates[coarse,condition]-rates[fine,condition]
                    row=decompose(a,b)
                    direct=(rates[coarse,condition]-rates[coarse,'baseline'])-(rates[fine,condition]-rates[fine,'baseline'])
                    if not np.array_equal(direct,b-a):raise ValueError('Paired algebra mismatch')
                    row.update(seed=seed,coarse_ms=coarse,fine_ms=fine,condition=condition)
                    rows.append(row)
    frame=pd.DataFrame(rows);frame.to_csv(out/'pairs.csv',index=False)
    summaries=[]
    for key,g in frame.groupby(['coarse_ms','fine_ms','condition']):
        summaries.append(dict(zip(['coarse_ms','fine_ms','condition'],key))|dict(n=len(g),
            medians={c:float(g[c].median()) for c in ['baseline_L1','lesion_L1','response_L1','cancelled_fraction']},
            pooled_cancelled_fraction=float(g.cancelled_L1.sum()/g.component_L1_sum.sum()),
            lesion_L1_exceeds_baseline=int((g.lesion_L1>g.baseline_L1).sum())))
    write(out/'summary.json',dict(groups=summaries,rate_hashes=hashes,completed_utc=utc()))
    print(pd.DataFrame(summaries).to_string(index=False))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();run(a.out)
