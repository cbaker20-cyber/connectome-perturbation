"""Partition pre-first-spike arrivals using fixed saved recruitment groups."""
from pathlib import Path
import sys
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from eigencircuits.common import atomic_json,sha256,now,CON,sugar_ids
from eigencircuits.graph import load_signed_matrix
from scripts.pcdr_ccr_transfer import read

GROUPS=['input','early_large_only','later_large_only','other_active','silent_all']


def arrivals(ticks,start,end,delay):
    """Count arrivals in a half-open interval without expanding synaptic events."""
    return int(np.searchsorted(ticks,end-delay,side='left')-np.searchsorted(ticks,start-delay,side='left'))


def main():
    run=ROOT/'results/pcdr/observed_replay_20260928'
    evidence=ROOT/'docs/pcdr/evidence'
    recruitment=evidence/'2026-09-28/recruitment_timing'
    out=evidence/'2026-09-29/source_inputs';out.mkdir(exist_ok=False)
    cells=pd.read_csv(recruitment/'early_large_only.csv',dtype={'root_id':str})
    active=pd.read_csv(recruitment/'active_cells.csv',dtype={'root_id':str}).set_index('root_id')
    previous_path=evidence/'2026-09-29/early_drive/cell_inputs.csv'
    previous=pd.read_csv(previous_path,dtype={'root_id':str})
    atomic_json(out/'protocol.json',{'recorded_utc':now(),'script_sha256':sha256(Path(__file__)),
        'cohort_sha256':sha256(recruitment/'early_large_only.csv'),'groups_sha256':sha256(recruitment/'active_cells.csv'),
        'previous_sha256':sha256(previous_path),'connectivity_sha256':sha256(CON),
        'method':'Same 577 targets and same physical 20 ms pre-first-spike windows in all four runs. Fixed mutually exclusive source groups: stimulated inputs; large-only recruited before 180 ms; large-only recruited at/after 180 ms; other cells active in any saved run; cells silent in all runs. Groups are outcome-defined. Count delayed spikes per incoming edge using sorted tick lookup, independently of the prior sparse-matrix calculation. Preserve sign, weight scaling and outgoing lesions. Require all per-target signed sums to reproduce the previous raw and accepted values within 1e-9 mV. All targets are nonrefractory before first spike in coarse lesion and silent in the other runs.',
        'limits':'An arrival from an earlier recruited cell demonstrates temporal connectivity, not that it caused target recruitment. Source groups condition on all four outcomes; no independent enrichment or causal test.'})
    w,ids=load_signed_matrix();ids=pd.Index(ids)
    labels=np.full(len(ids),'silent_all',dtype=object)
    for rid,row in active.iterrows():
        i=ids.get_loc(rid)
        labels[i]=('early_large_only' if row.early_large_only else 'later_large_only') if row.group=='large_only' else 'other_active'
    labels[ids.isin(sugar_ids())]='input'
    plan=read(run/'plan.json')
    cert=read(evidence/'2026-09-28/observed_replay_check.json');verified={r['trial']:r for r in cert['rows']}
    rows=[];max_error=0.
    for j in plan['jobs']:
        directory=run/j['id'];m=read(directory/'manifest.json')
        if sha256(directory/'manifest.json')!=verified[j['id']]['manifest_sha256'] or sha256(directory/'spikes.parquet')!=m['outputs']['spikes.parquet']:
            raise ValueError('Changed reference')
        spikes=pd.read_parquet(directory/'spikes.parquet')
        ticks={rid:np.sort(np.rint(f.t.to_numpy()*1000/j['dt_ms']).astype(np.int64)) for rid,f in spikes.groupby('flywire_id')}
        lesion=set(j['lesion_ids']);delay=round(1.8/j['dt_ms'])
        for cell in cells.itertuples():
            end=round(cell.lesion_coarse_first_ms/j['dt_ms']);start=end-round(20/j['dt_ms'])
            target=ids.get_loc(cell.root_id);edge=w.getrow(target)
            sums={g:[0.,0.,0] for g in GROUPS}
            for pre,value in zip(edge.indices,edge.data):
                rid=ids[pre]
                if rid in lesion or rid not in ticks:continue
                count=arrivals(ticks[rid],start,end,delay)
                weight=float(value)*.275
                if weight<0:weight*=.8
                weight*=1.2
                group=labels[pre];sums[group][0 if weight>0 else 1]+=count*weight
                sums[group][2]+=count
            saved=previous[(previous.condition==j['condition'])&(previous.dt_ms==j['dt_ms'])&(previous.root_id==cell.root_id)&(previous.window=='pre_first_20ms')]
            if len(saved)!=1:raise ValueError('Missing or duplicate previous result')
            for sign,k in [('positive',0),('negative',1)]:
                value=sum(v[k] for v in sums.values())
                for kind in ['raw','accepted']:
                    error=abs(value-float(saved.iloc[0][sign+'_'+kind+'_mV']));max_error=max(max_error,error)
                    if error>1e-9:raise ValueError('Independent arrival sums disagree')
            rows.extend({'condition':j['condition'],'dt_ms':j['dt_ms'],'root_id':cell.root_id,
                'source_group':g,'positive_mV':v[0],'negative_mV':v[1],'edge_event_count':v[2]} for g,v in sums.items())
        print('Checked '+j['id'],flush=True)
    frame=pd.DataFrame(rows);frame.to_csv(out/'cell_sources.csv',index=False)
    frame.groupby(['condition','dt_ms','source_group'])[['positive_mV','negative_mV','edge_event_count']].sum().to_csv(out/'group_sums.csv')
    atomic_json(out/'record.json',{'status':'complete','completed_utc':now(),'target_run_pairs':len(cells)*len(plan['jobs']),
        'max_independent_sum_error_mV':max_error,'outputs':{p.name:sha256(p) for p in out.iterdir() if p.is_file()}})


if __name__=='__main__':main()
