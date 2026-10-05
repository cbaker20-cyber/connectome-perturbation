"""Reconstruct recurrent arrival gating from saved spikes; check against recorded drive."""
from pathlib import Path
import sys
import argparse
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.pcdr_ccr_transfer import read,write,digest
from eigencircuits.common import neuron_ids


def accepted(arrivals, postsynaptic_spikes, refractory_ticks):
    arrivals=np.asarray(arrivals,dtype=np.int64)
    postsynaptic_spikes=np.asarray(postsynaptic_spikes,dtype=np.int64)
    if np.any(np.diff(postsynaptic_spikes)<0):raise ValueError('Postsynaptic spikes must be sorted')
    indices=np.searchsorted(postsynaptic_spikes,arrivals,side='right')-1
    result=np.ones(len(arrivals),dtype=bool)
    present=indices>=0
    # Even zero-refractory input cells are marked refractory in the tick of a spike.
    result[present]=arrivals[present]-postsynaptic_spikes[indices[present]]>=max(1,refractory_ticks)
    return result


def run(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    plan=read(ROOT/'results/pcdr/diagnostic_inputs_20261005/diagnostic_plan.json')
    ids=neuron_ids();lookup={v:i for i,v in enumerate(ids)}
    con_path=ROOT/'2023_03_23_connectivity_630_final.parquet'
    if digest(con_path)!=plan['model_files'][con_path.name]:raise ValueError('Connectivity changed')
    con=pd.read_parquet(con_path)
    targets=[lookup[v] for v in plan['record_ids']]
    con=con.loc[con.Postsynaptic_Index.isin(targets)&~con.Presynaptic_Index.isin([lookup[v] for v in plan['lesion_ids']])].copy()
    con['weight']=con['Excitatory x Connectivity']*.275*1.2
    con.loc[con.weight<0,'weight']*=.8
    rows,checks=[],[]
    edges=np.array([0,600,650,700,730,1000.])
    for dt in [.0008,.0004,.0002,.0001]:
        directory=ROOT/'results/pcdr/fine_download_20261005/trials'/f"fine_{str(dt).replace('.','p')}_w120_i080_mn9_only_631430"
        m=read(directory/'manifest.json')
        if digest(directory/'spikes.parquet')!=m['outputs']['spikes.parquet']:raise ValueError('Spikes changed')
        frame=pd.read_parquet(directory/'spikes.parquet')
        frame['tick']=np.rint(frame.t.to_numpy()*1000/dt).astype(np.int64)
        spikes={lookup[v]:np.sort(g.tick.to_numpy()) for v,g in frame.groupby('flywire_id')}
        prefix_ticks=round(20/dt)
        predicted=np.zeros((len(targets),prefix_ticks)) if dt in plan['dt_ms'] else None
        for ti,target in enumerate(targets):
            totals=np.zeros((5,4))
            post=spikes.get(target,np.array([],dtype=np.int64))
            refractory=0 if ids[target] in plan['input_ids'] else round(2.2/dt)
            for row in con.loc[con.Postsynaptic_Index==target].itertuples():
                arrival=spikes.get(row.Presynaptic_Index,np.array([],dtype=np.int64))+round(1.8/dt)
                arrival=arrival[arrival<round(1000/dt)]
                allow=accepted(arrival,post,refractory)
                phase=np.searchsorted(edges,np.round(arrival*dt,9),side='right')-1
                positive=row.weight>0
                # Separate magnitudes of accepted and blocked excitatory/inhibitory increments.
                column=np.where(allow,0 if positive else 1,2 if positive else 3)
                np.add.at(totals,(phase,column),abs(row.weight))
                if predicted is not None:
                    selected=arrival[allow&(arrival<prefix_ticks)]
                    np.add.at(predicted[ti],selected,row.weight)
            for k in range(5):
                rows.append(dict(dt_ms=dt,root_id=ids[target],start_ms=edges[k],end_ms=edges[k+1],
                    accepted_exc_mV=totals[k,0],accepted_inh_mV=totals[k,1],blocked_exc_mV=totals[k,2],blocked_inh_mV=totals[k,3]))
        if predicted is not None:
            recorded=np.zeros_like(predicted)
            d=ROOT/'results/pcdr/diagnostic_prefix_20261005'/str(dt)
            evidence=read(d/'manifest.json')
            for name,h in evidence['outputs'].items():
                if digest(d/name)!=h:raise ValueError('Prefix recording changed')
            for start in [0,round(10/dt)]:
                with np.load(d/'state'/f'{start:010d}_before_thresholds.npz') as before, np.load(d/'state'/f'{start:010d}_after_synapses.npz') as after:
                    if before['indices'].tolist()!=targets or after['indices'].tolist()!=targets:raise ValueError('Recording ID order changed')
                    recorded[:,before['tick']]=after['g_mV']-before['g_mV']
            error=float(np.max(np.abs(recorded-predicted)))
            if not np.allclose(recorded,predicted,atol=1e-8,rtol=1e-10):raise ValueError('Arrival gating disagrees with recorded drive')
            checks.append(dict(dt_ms=dt,max_absolute_drive_error_mV=error,neurons=len(targets),ticks=prefix_ticks))
    pd.DataFrame(rows).to_csv(out/'recurrent_delivery.csv',index=False)
    write(out/'checks.json',{'status':'complete','prefix_checks':checks,
        'script_sha256':digest(Path(__file__)),'plan_sha256':digest(ROOT/'results/pcdr/diagnostic_inputs_20261005/diagnostic_plan.json'),
        'interpretation':'Reconstructed weighted arrivals conditional on observed spikes, not a causal intervention or membrane-state measurement.',
        'output_sha256':digest(out/'recurrent_delivery.csv')})


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',required=True)
    run(p.parse_args().out)
