"""Conditional voltage reconstruction at the six first outside differences."""
from pathlib import Path
import argparse
import io
import json
import sys
import zipfile
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.pcdr_ccr_transfer import read,write,digest,utc
from scripts.pcdr_recurrent_delivery import accepted
from scripts.pcdr_first_spike import kernel


def voltage(arrivals,weights,post,tick,dt):
    arrivals=np.asarray(arrivals);weights=np.asarray(weights,float);post=np.asarray(post)
    if arrivals.shape!=weights.shape or not np.isfinite(weights).all() or dt<=0:
        raise ValueError('Invalid arrivals or weights')
    if np.any(np.diff(post)<0) or np.any(arrivals<0):raise ValueError('Invalid spike history')
    previous=post[post<tick];last=int(previous[-1]) if len(previous) else -1
    keep=(arrivals>last)&(arrivals<tick)&accepted(arrivals,post,round(2.2/dt))
    return -52.+float(np.sum(weights[keep]*kernel((tick-arrivals[keep])*dt)))


def run(out):
    prior=ROOT/'results/pcdr/pathway_routes_20261008'
    for name,h in read(prior/'complete.json')['outputs'].items():
        if digest(prior/name)!=h:raise ValueError('Changed route evidence')
    archive=ROOT/'CCR_separate_pathway_results.zip'
    review=read(ROOT/'docs/pcdr/evidence/2026-10-08/separate_review.json')
    if digest(archive)!=review['archive_sha256']:raise ValueError('Changed archive')
    out.mkdir(parents=True,exist_ok=False)
    deps=[Path(__file__),ROOT/'scripts/pcdr_recurrent_delivery.py',ROOT/'scripts/pcdr_first_spike.py',prior/'results.json',archive]
    write(out/'protocol.json',dict(recorded_utc=utc(),inputs={str(p):digest(p) for p in deps},
        design='Six first outside events; evaluate reference and intervention voltage at previous and crossing ticks using archived incoming spikes, observed resets, 1.8 ms delay, refractory gating and exact linear impulse kernel. Require reference prior tick <= -45 and crossing > -45; intervention crossing <= -45. Preserve failures. No free-running replay or fitted parameters.',
        limitation='Conditional on observed spike/reset histories. Matching these crossings is not full-trajectory reproduction or convergence. No counterfactual network simulation.'))
    records=[]
    with zipfile.ZipFile(archive) as z:
        plan=json.loads(z.read('diagnostic_plan.json'))
        for name,h in plan['model_files'].items():
            if digest(ROOT/name)!=h:raise ValueError('Changed model/data')
        con=pd.read_parquet(ROOT/'2023_03_23_connectivity_630_final.parquet')
        con.Presynaptic_ID=con.Presynaptic_ID.astype(str);con.Postsynaptic_ID=con.Postsynaptic_ID.astype(str)
        for trial,targets in read(prior/'results.json')['comparisons'].items():
            dt=float(trial.rsplit('_',1)[1])
            for target in targets:
                neuron=target['target']['id'];tick=target['target']['tick']
                if neuron in plan['input_ids']:raise ValueError('External input unsupported')
                edges=con.loc[con.Postsynaptic_ID.eq(neuron)&~con.Presynaptic_ID.isin(plan['lesion_ids'])]
                if edges.Presynaptic_ID.duplicated().any():raise ValueError('Duplicate incoming pair')
                weights=edges['Excitatory x Connectivity'].to_numpy(float)*.275*1.2
                weights[weights<0]*=.8
                mapping=dict(zip(edges.Presynaptic_ID,weights))
                row=dict(trial=trial,target_id=neuron,time_ms=tick*dt)
                for label,name in [('reference','late_reference_'+str(dt)),('intervention',trial)]:
                    f=pd.read_parquet(io.BytesIO(z.read(name+'/spikes.parquet')))
                    ticks=np.rint(f.t.to_numpy()*1000/dt).astype(np.int64)
                    post=ticks[f.flywire_id.eq(neuron)]
                    selected=f.flywire_id.isin(mapping).to_numpy()
                    arrivals=ticks[selected]+round(1.8/dt)
                    w=f.loc[selected,'flywire_id'].map(mapping).to_numpy(float)
                    v=[voltage(arrivals,w,post,t,dt) for t in [tick-1,tick]]
                    previous=post[post<tick]
                    ready=not len(previous) or tick-previous[-1]>=round(2.2/dt)
                    row[label]=dict(previous_voltage_mv=v[0],crossing_voltage_mv=v[1],ready=bool(ready),
                        saved_spike_at_tick=bool(np.any(post==tick)),last_reset_ms=None if not len(previous) else float(previous[-1]*dt))
                a,b=row['reference'],row['intervention']
                row['crossing_check_passed']=bool(a['ready'] and b['ready'] and a['previous_voltage_mv']<=-45<a['crossing_voltage_mv'] and b['crossing_voltage_mv']<=-45 and a['saved_spike_at_tick'] and not b['saved_spike_at_tick'])
                records.append(row)
    write(out/'results.json',dict(status='passed' if all(r['crossing_check_passed'] for r in records) else 'failed',records=records,completed_utc=utc()))
    print(json.dumps(records,indent=2))
    if not all(r['crossing_check_passed'] for r in records):raise ValueError('Crossing mismatch; preserve result')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    run(parser.parse_args().out)
