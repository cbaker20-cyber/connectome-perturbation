"""Free-running single-cell replay driven by archived presynaptic events."""
from pathlib import Path
import argparse
import io
import json
import sys
import zipfile
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.pcdr_ccr_transfer import read,write,digest,utc


def replay(arrivals,weights,stop,dt):
    arrivals=np.asarray(arrivals);weights=np.asarray(weights,float)
    if arrivals.ndim!=1 or arrivals.shape!=weights.shape or not np.issubdtype(arrivals.dtype,np.integer):
        raise ValueError('Invalid arrival arrays')
    if np.any(arrivals<0) or not np.isfinite(weights).all() or not np.isfinite(dt) or dt<=0 or type(stop) is not int or stop<1:
        raise ValueError('Invalid replay parameters')
    refractory=round(2.2/dt)
    if refractory<1 or abs(refractory*dt-2.2)>1e-10:raise ValueError('Off-grid refractory duration')
    mask=arrivals<stop;arrivals=arrivals[mask];weights=weights[mask]
    ticks,inv=np.unique(arrivals,return_inverse=True)
    jumps=np.bincount(inv,weights=weights,minlength=len(ticks))
    t=-1;u=0.;g=0.;last=-refractory-1;spikes=[]
    for end,jump in zip(np.r_[ticks,stop-1],np.r_[jumps,0.]):
        end=int(end)
        while t<end:
            if t<last+refractory-1:
                t=min(end,last+refractory-1)
                if t==end:break
            # Evaluate all intervening threshold ticks from the same exact state.
            lag=np.arange(1,end-t+1,dtype=float)*dt
            e20=np.exp(-lag/20);e5=np.exp(-lag/5)
            v=u*e20+g*(e20-e5)/3
            crossings=np.flatnonzero(v>7.)
            if len(crossings):
                t+=int(crossings[0])+1;spikes.append(t);last=t;u=g=0.
            else:
                u=float(v[-1]);g*=float(e5[-1]);t=end
        if end-last>=refractory:g+=float(jump)
    return np.asarray(spikes,dtype=np.int64)


def worker(out):
    import pandas as pd
    p=read(out/'protocol.json')
    for path,h in p['inputs'].items():
        if digest(path)!=h:raise ValueError('Changed input: '+path)
    archive=ROOT/'CCR_separate_pathway_results.zip';records=[]
    with zipfile.ZipFile(archive) as z:
        plan=json.loads(z.read('diagnostic_plan.json'))
        for name,h in plan['model_files'].items():
            if digest(ROOT/name)!=h:raise ValueError('Changed model/data')
        con=pd.read_parquet(ROOT/'2023_03_23_connectivity_630_final.parquet')
        con.Presynaptic_ID=con.Presynaptic_ID.astype(str);con.Postsynaptic_ID=con.Postsynaptic_ID.astype(str)
        for trial,targets in p['comparisons'].items():
            dt=float(trial.rsplit('_',1)[1])
            for item in targets:
                target=item['target'];neuron=target['id'];stop=int(target['tick'])+1
                if neuron in plan['input_ids']:raise ValueError('Directly driven target unsupported')
                edges=con.loc[con.Postsynaptic_ID.eq(neuron)&~con.Presynaptic_ID.isin(plan['lesion_ids'])]
                if edges.Presynaptic_ID.duplicated().any():raise ValueError('Duplicate edges')
                weights=edges['Excitatory x Connectivity'].to_numpy(float)*.275*1.2;weights[weights<0]*=.8
                mapping=dict(zip(edges.Presynaptic_ID,weights))
                for label,name in [('reference','late_reference_'+str(dt)),('intervention',trial)]:
                    f=pd.read_parquet(io.BytesIO(z.read(name+'/spikes.parquet')))
                    ticks=f.t.to_numpy()*1000/dt
                    if np.max(np.abs(ticks-np.rint(ticks)),initial=0)>1e-6:raise ValueError('Off-grid spikes')
                    ticks=np.rint(ticks).astype(np.int64);selected=f.flywire_id.isin(mapping).to_numpy()
                    arrivals=ticks[selected]+round(1.8/dt);w=f.loc[selected,'flywire_id'].map(mapping).to_numpy(float)
                    actual=ticks[f.flywire_id.eq(neuron)&(ticks<stop)]
                    predicted=replay(arrivals,w,stop,dt)
                    name_out=trial+'_'+label+'.npz';np.savez(out/name_out,actual=actual,predicted=predicted)
                    records.append(dict(trial=trial,label=label,target_id=neuron,stop_ms=(stop-1)*dt,
                        exact_ticks=bool(np.array_equal(actual,predicted)),saved_spikes=len(actual),replayed_spikes=len(predicted),
                        symmetric_difference_ticks=sorted(set(actual.tolist())^set(predicted.tolist())),output=name_out,sha256=digest(out/name_out)))
    write(out/'results.json',dict(status='passed' if all(r['exact_ticks'] for r in records) else 'failed',records=records,completed_utc=utc()))
    print([(r['trial'],r['label'],r['exact_ticks']) for r in records])


def run(out):
    from scripts.pcdr_bounded_process import run_bounded
    prior=ROOT/'results/pcdr/pathway_routes_20261008/results.json'
    archive=ROOT/'CCR_separate_pathway_results.zip'
    if digest(archive)!=read(ROOT/'docs/pcdr/evidence/2026-10-08/separate_review.json')['archive_sha256']:raise ValueError('Changed archive')
    out.mkdir(parents=True,exist_ok=False)
    write(out/'protocol.json',dict(recorded_utc=utc(),inputs={str(p):digest(p) for p in [Path(__file__),prior,archive]},comparisons=read(prior)['comparisons'],
        method='Twelve local prefixes, four distinct targets at designated steps: generate thresholds and resets from initial rest using all archived presynaptic arrivals. Evaluate exact linear dynamics between event ticks; apply threshold before synapses, reset and reject refractory arrivals. Stop at first outside difference inclusive. No supplied postsynaptic reset times.',
        budget='One local worker, 120-second external deadline; no retry or full-network simulation.',
        limitation='Presynaptic inputs are observed network trajectories. Exact tick agreement is a replay implementation check, not convergence or a network counterfactual. Preserve mismatch outputs.'))
    process=run_bounded([sys.executable,str(Path(__file__).resolve()),'--out',str(out),'--worker'],out/'logs',120,cwd=ROOT)
    write(out/'process.json',process);print(process)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,required=True);parser.add_argument('--worker',action='store_true')
    args=parser.parse_args()
    if args.worker:worker(args.out)
    else:run(args.out)
