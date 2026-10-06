"""Compare reconstructed arrivals, state updates and resets with the returned recordings."""
import argparse
import io
from pathlib import Path
import sys
import zipfile
import json

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from eigencircuits.common import neuron_ids
from scripts.pcdr_ccr_transfer import digest, write
from scripts.pcdr_recurrent_delivery import accepted


def advance(v, g, ready, dt):
    em, es = np.exp(-dt/20), np.exp(-dt/5)
    return (np.where(ready,-52+(v+52)*em+g*(5/(5-20))*(es-em),v),
            np.where(ready,g*es,g))


def compare(actual, expected, label):
    error = float(np.max(np.abs(actual-expected)))
    if not np.allclose(actual,expected,atol=1e-8,rtol=1e-10):
        raise ValueError(f'{label}: maximum difference {error}')
    return error


def run(archive, out):
    validation = json.loads((ROOT/'docs/pcdr/evidence/2026-10-05/diagnostic_return/validation.json').read_text())
    if digest(archive) != validation['archive_sha256']:
        raise ValueError('Archive differs from independently checked return')
    out.mkdir(parents=True,exist_ok=False)
    ids=neuron_ids(); lookup={v:i for i,v in enumerate(ids)}
    rows, checks, event_rows, histories = [], [], [], []
    with zipfile.ZipFile(archive) as z:
        plan=json.loads(z.read('diagnostic_plan.json'))
        conpath=ROOT/'2023_03_23_connectivity_630_final.parquet'
        if digest(conpath)!=plan['model_files'][conpath.name]:
            raise ValueError('Connectivity changed')
        targets=[v for v in plan['record_ids'] if v not in plan['input_ids']]
        record_rows=[plan['record_ids'].index(v) for v in targets]
        con=pd.read_parquet(conpath)
        con=con[con.Postsynaptic_Index.isin([lookup[v] for v in targets]) &
                ~con.Presynaptic_Index.isin([lookup[v] for v in plan['lesion_ids']])].copy()
        con['weight']=con['Excitatory x Connectivity']*.275*1.2
        con.loc[con.weight<0,'weight']*=.8
        for dt in plan['dt_ms']:
            f=pd.read_parquet(io.BytesIO(z.read(f'{dt}/spikes.parquet')))
            spikes={lookup[v]:np.rint(g.t.to_numpy()*1000/dt).astype(np.int64) for v,g in f.groupby('flywire_id')}
            for root in ['720575940628455942','720575940628695043','720575940639283278',
                         '720575940623387786','720575940637902938']:
                train=spikes.get(lookup[root],np.array([],dtype=np.int64))
                histories.append(dict(dt_ms=dt,root_id=root,first_ms=float(train[0]*dt) if len(train) else None,
                    spikes_590_655_ms=(train[(train>=round(590/dt))&(train<round(655/dt))]*dt).tolist()))
            arrivals={v:[] for v in targets}
            for edge in con.itertuples():
                if edge.weight==0:continue
                target=ids[edge.Postsynaptic_Index]
                times=spikes.get(edge.Presynaptic_Index,np.array([],dtype=np.int64))+round(1.8/dt)
                times=times[(times>=round(600/dt)) & (times<round(750/dt))]
                if not len(times):continue
                gate=accepted(times,spikes.get(edge.Postsynaptic_Index,[]),round(2.2/dt))
                arrivals[target].append((times,gate,edge.weight))
                if target in ['720575940628455942','720575940628695043','720575940639283278']:
                    for tick,allow in zip(times,gate):
                        if tick<round(650/dt):
                            event_rows.append(dict(dt_ms=dt,target_id=target,source_id=ids[edge.Presynaptic_Index],
                                arrival_tick=int(tick),arrival_ms=float(tick*dt),weight_mV=edge.weight,accepted=bool(allow)))
                for lo,hi in [(600,650),(640,650),(650,700),(700,750)]:
                    pick=(times>=round(lo/dt)) & (times<round(hi/dt))
                    if not pick.any():continue
                    rows.append(dict(dt_ms=dt,target_id=target,source_id=ids[edge.Presynaptic_Index],
                        start_ms=lo,end_ms=hi,weight_mV=edge.weight,arrivals=int(pick.sum()),
                        accepted=int((pick&gate).sum()),attempted_magnitude_mV=float(pick.sum()*abs(edge.weight)),
                        accepted_magnitude_mV=float((pick&gate).sum()*abs(edge.weight))))
            errors={k:0. for k in ['arrivals','voltage_update','drive_update','reset_v','reset_g']}
            previous=None
            for start_ms in range(600,750,10):
                start=round(start_ms/dt); n=round(10/dt)
                states={}
                for phase in ['before_thresholds','after_synapses','end']:
                    with np.load(io.BytesIO(z.read(f'{dt}/state/{start:010d}_{phase}.npz')),allow_pickle=False) as a:
                        states[phase]={k:a[k][record_rows] for k in ['v_mV','g_mV','not_refractory']}
                before,after,end=(states[k] for k in ['before_thresholds','after_synapses','end'])
                predicted=np.zeros((len(targets),n))
                for i,target in enumerate(targets):
                    for times,gate,weight in arrivals[target]:
                        selected=times[gate & (times>=start) & (times<start+n)]-start
                        np.add.at(predicted[i],selected,weight)
                errors['arrivals']=max(errors['arrivals'],compare(after['g_mV']-before['g_mV'],predicted,'arrivals'))
                if previous is None:
                    prev_v,prev_g=end['v_mV'][:,:-1],end['g_mV'][:,:-1]
                    offset=1
                else:
                    prev_v=np.column_stack([previous[0],end['v_mV'][:,:-1]])
                    prev_g=np.column_stack([previous[1],end['g_mV'][:,:-1]])
                    offset=0
                v,g=advance(prev_v,prev_g,before['not_refractory'][:,offset:],dt)
                errors['voltage_update']=max(errors['voltage_update'],compare(before['v_mV'][:,offset:],v,'voltage update'))
                errors['drive_update']=max(errors['drive_update'],compare(before['g_mV'][:,offset:],g,'drive update'))
                firing=(before['v_mV']>-45)&before['not_refractory']
                errors['reset_v']=max(errors['reset_v'],compare(end['v_mV'],np.where(firing,-52,after['v_mV']),'voltage reset'))
                errors['reset_g']=max(errors['reset_g'],compare(end['g_mV'],np.where(firing,0,after['g_mV']),'drive reset'))
                previous=(end['v_mV'][:,-1],end['g_mV'][:,-1])
            checks.append(dict(dt_ms=dt,neurons=len(targets),recorded_ticks=round(150/dt),maximum_errors_mV=errors))
    pd.DataFrame(rows).to_csv(out/'incoming_sources.csv',index=False)
    pd.DataFrame(event_rows).sort_values(['dt_ms','arrival_tick','target_id','source_id']).to_csv(out/'selected_events.csv',index=False)
    write(out/'source_spike_times.json',histories)
    write(out/'checks.json',dict(status='complete',archive_sha256=validation['archive_sha256'],checks=checks,
        script_sha256=digest(Path(__file__)),gating_script_sha256=digest(ROOT/'scripts/pcdr_recurrent_delivery.py'),
        selection='All 13 recorded non-input cells. Overlapping descriptive windows; do not sum across windows.',
        limitation='Conditional reconstruction using observed spikes. Does not establish the first divergence or causal necessity.'))
    print(json.dumps(checks,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('archive',type=Path);p.add_argument('out',type=Path)
    args=p.parse_args();run(args.archive,args.out)
