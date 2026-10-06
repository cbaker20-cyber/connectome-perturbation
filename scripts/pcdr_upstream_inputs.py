"""Reconstruct voltage before first firing from the known initial state and all saved arrivals."""
import argparse
import io
import json
from pathlib import Path
import sys
import zipfile

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from eigencircuits.common import neuron_ids
from scripts.pcdr_ccr_transfer import digest,write
from scripts.pcdr_first_spike import kernel

TARGETS=['720575940638633806','720575940629910636','720575940611439473']
CHECKS=['720575940628455942','720575940639283278']


def contribution(arrivals, weight, tick, dt):
    arrivals=np.asarray(arrivals,dtype=np.int64)
    if np.any(arrivals<0) or tick<0 or not np.isfinite(weight) or not np.isfinite(dt) or dt<=0:
        raise ValueError('Invalid event reconstruction inputs')
    earlier=arrivals[arrivals<tick]
    return float(weight*kernel((tick-earlier)*dt).sum())


def run(archive,out):
    validation=json.loads((ROOT/'docs/pcdr/evidence/2026-10-05/diagnostic_return/validation.json').read_text())
    if digest(archive)!=validation['archive_sha256']:raise ValueError('Changed archive')
    ids=neuron_ids();lookup={v:i for i,v in enumerate(ids)}
    rows,summaries,histories=[],[],[]
    with zipfile.ZipFile(archive) as z:
        plan=json.loads(z.read('diagnostic_plan.json'))
        path=ROOT/'2023_03_23_connectivity_630_final.parquet'
        if digest(path)!=plan['model_files'][path.name]:raise ValueError('Changed connectivity')
        con=pd.read_parquet(path)
        selected=TARGETS+CHECKS
        con=con[con.Postsynaptic_Index.isin([lookup[v] for v in selected]) &
                ~con.Presynaptic_Index.isin([lookup[v] for v in plan['lesion_ids']])].copy()
        con['weight']=con['Excitatory x Connectivity']*.275*1.2
        con.loc[con.weight<0,'weight']*=.8
        first_times={}
        for dt in [.0004,.0002]:
            frame=pd.read_parquet(io.BytesIO(z.read(f'{dt}/spikes.parquet')))
            trains={lookup[v]:np.sort(np.rint(g.t.to_numpy()*1000/dt).astype(np.int64)) for v,g in frame.groupby('flywire_id')}
            for root in ['720575940629667639','720575940623862015']:
                train=trains.get(lookup[root],np.array([],dtype=np.int64))
                histories.append(dict(dt_ms=dt,root_id=root,first_spike_ms=float(train[0]*dt) if len(train) else None,
                    spikes_590_645_ms=(train[(train>=round(590/dt))&(train<round(645/dt))]*dt).tolist()))
            for target in selected:
                if target in plan['input_ids']:raise ValueError('Externally driven target unsupported')
                post=trains.get(lookup[target],np.array([],dtype=np.int64))
                if dt==.0004:
                    if not len(post):raise ValueError('Expected first spike')
                    first_times[target]=float(post[0]*dt)
                time=first_times[target];tick=round(time/dt)
                if np.any(post<tick):raise ValueError('Prior reset invalidates initial-state reconstruction')
                v=-52.;previous=-52.
                for edge in con[con.Postsynaptic_Index==lookup[target]].itertuples():
                    arrival=trains.get(edge.Presynaptic_Index,np.array([],dtype=np.int64))+round(1.8/dt)
                    value=contribution(arrival,edge.weight,tick,dt)
                    previous+=contribution(arrival,edge.weight,tick-1,dt)
                    v+=value
                    if np.any(arrival<tick):
                        earlier=arrival[arrival<tick]
                        rows.append(dict(dt_ms=dt,target_id=target,source_id=ids[edge.Presynaptic_Index],
                            evaluation_ms=time,weight_mV=edge.weight,arrival_count=len(earlier),
                            last_arrival_ms=float(earlier[-1]*dt),voltage_contribution_mV=value))
                if dt==.0004 and not (previous<=-45<v):
                    raise ValueError(f'First crossing not reproduced: {target}, {previous}, {v}')
                if dt==.0002 and v>-45:raise ValueError('Silent finer cell reconstructed above threshold')
                record=dict(dt_ms=dt,target_id=target,evaluation_ms=time,voltage_mV=v,
                    previous_tick_voltage_mV=previous,spikes_before_evaluation=int((post<tick).sum()),
                    total_spikes_through_750_ms=len(post),distance_below_threshold_mV=-45-v)
                if target in CHECKS:
                    i=plan['record_ids'].index(target);start=(tick//round(10/dt))*round(10/dt)
                    with np.load(io.BytesIO(z.read(f'{dt}/state/{start:010d}_before_thresholds.npz')),allow_pickle=False) as a:
                        measured=float(a['v_mV'][i,tick-start])
                    record.update(recorded_voltage_mV=measured,absolute_error_mV=abs(v-measured))
                    if abs(v-measured)>1e-8:raise ValueError('Recorded check cell mismatch')
                summaries.append(record)
    out.mkdir(parents=True,exist_ok=False)
    pd.DataFrame(rows).to_csv(out/'source_contributions.csv',index=False)
    write(out/'leading_source_times.json',histories)
    write(out/'summary.json',dict(archive_sha256=validation['archive_sha256'],script_sha256=digest(Path(__file__)),
        kernel_sha256=digest(ROOT/'scripts/pcdr_first_spike.py'),targets=TARGETS,recorded_checks=CHECKS,results=summaries,
        interpretation='Conditional voltage reconstruction from the model initial state, before any postsynaptic reset. Not an independent network simulation or causal intervention.'))
    print(json.dumps(summaries,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('archive',type=Path);p.add_argument('out',type=Path)
    a=p.parse_args();run(a.archive,a.out)
