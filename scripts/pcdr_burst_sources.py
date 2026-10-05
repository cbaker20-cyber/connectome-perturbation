"""Attribute reconstructed pre-burst arrivals to their recorded source cells."""
from pathlib import Path
import argparse
import sys
import zipfile
import json
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from eigencircuits.common import neuron_ids
from scripts.pcdr_ccr_transfer import read,write,digest
from scripts.pcdr_recurrent_delivery import accepted


def run(out):
    out=Path(out)
    if out.exists():raise FileExistsError(out)
    plan=read(ROOT/'docs/pcdr/evidence/2026-10-05/mechanism/diagnostic_plan.json')
    archive=ROOT/'CCR_fine_results.zip'
    if digest(archive)!=plan['archive_sha256']:raise ValueError('Changed archive')
    ids=neuron_ids();lookup={v:i for i,v in enumerate(ids)}
    targets=set(plan['record_ids'])-set(plan['input_ids'])-set(plan['lesion_ids'])
    path=ROOT/'2023_03_23_connectivity_630_final.parquet'
    if digest(path)!=plan['model_files'][path.name]:raise ValueError('Changed connectivity')
    con=pd.read_parquet(path)
    con=con[con.Postsynaptic_Index.isin([lookup[v] for v in targets]) & ~con.Presynaptic_Index.isin([lookup[v] for v in plan['lesion_ids']])].copy()
    con['weight']=con['Excitatory x Connectivity']*.275*1.2
    con.loc[con.weight<0,'weight']*=.8
    out.mkdir(parents=True)
    write(out/'protocol.json',{'status':'post-result descriptive attribution','windows_ms':[[600,650],[650,700]],
        'target_ids':sorted(targets),'steps_ms':[.0008,.0004,.0002,.0001],
        'restriction':'Conditional on observed spikes; source ranking does not identify a causal initiating cell.',
        'archive_sha256':digest(archive),'script_sha256':digest(Path(__file__)),
        'gating_source_sha256':digest(ROOT/'scripts/pcdr_recurrent_delivery.py')})
    rows=[]
    with zipfile.ZipFile(archive) as z:
        for dt in [.0008,.0004,.0002,.0001]:
            name=f"fine_{str(dt).replace('.','p')}_w120_i080_mn9_only_631430"
            path=ROOT/'results/pcdr/fine_download_20261005/trials'/name/'spikes.parquet'
            m=json.loads(z.read('trials/'+name+'/manifest.json'))
            if digest(path)!=m['outputs']['spikes.parquet']:raise ValueError('Changed spikes')
            f=pd.read_parquet(path)
            spikes={lookup[v]:np.sort(np.rint(g.t.to_numpy()*1000/dt).astype(np.int64)) for v,g in f.groupby('flywire_id')}
            for edge in con.itertuples():
                pre=spikes.get(edge.Presynaptic_Index,np.array([],dtype=np.int64))
                post=spikes.get(edge.Postsynaptic_Index,np.array([],dtype=np.int64))
                arrival=pre+round(1.8/dt)
                for start in [600,650]:
                    selected=arrival[(arrival>=round(start/dt))&(arrival<round((start+50)/dt))]
                    if not len(selected):continue
                    gate=accepted(selected,post,round(2.2/dt))
                    rows.append(dict(dt_ms=dt,start_ms=start,source_id=ids[edge.Presynaptic_Index],
                        target_id=ids[edge.Postsynaptic_Index],sign='exc' if edge.weight>0 else 'inh',
                        arrivals=len(selected),accepted=int(gate.sum()),
                        attempted_mV=len(selected)*abs(edge.weight),accepted_mV=int(gate.sum())*abs(edge.weight)))
    f=pd.DataFrame(rows);f.to_csv(out/'edge_arrivals.csv',index=False)
    source=f.groupby(['dt_ms','start_ms','source_id','sign'],as_index=False)[['arrivals','accepted','attempted_mV','accepted_mV']].sum()
    ann=pd.read_csv(ROOT/'flywire_annotations.tsv',sep='\t',dtype=str,usecols=['root_id','cell_type','cell_class'])
    if ann.root_id.duplicated().any():raise ValueError('Duplicate annotation IDs')
    source=source.merge(ann.rename(columns={'root_id':'source_id'}),on='source_id',how='left',validate='many_to_one')
    source.sort_values(['dt_ms','start_ms','accepted_mV'],ascending=[True,True,False]).to_csv(out/'source_arrivals.csv',index=False)
    totals=source.groupby(['dt_ms','start_ms','sign'],as_index=False)[['attempted_mV','accepted_mV']].sum()
    old=pd.read_csv(ROOT/'results/pcdr/recurrent_delivery_20261005/recurrent_delivery.csv',dtype={'root_id':str})
    old=old[old.root_id.isin(targets)].groupby(['dt_ms','start_ms']).sum(numeric_only=True)
    for r in totals.itertuples():
        x=old.loc[r.dt_ms,r.start_ms]
        if not np.isclose(r.accepted_mV,x[f'accepted_{r.sign}_mV'],rtol=1e-12,atol=1e-8):raise ValueError('Accepted totals disagree')
        if not np.isclose(r.attempted_mV,x[f'accepted_{r.sign}_mV']+x[f'blocked_{r.sign}_mV'],rtol=1e-12,atol=1e-8):raise ValueError('Arrival totals disagree')
    totals['accepted_fraction']=totals.accepted_mV/totals.attempted_mV
    totals.to_csv(out/'totals.csv',index=False)
    selected=source[(source.dt_ms==.0004)&(source.start_ms==650)&(source.sign=='exc')].sort_values(
        ['accepted_mV','source_id'],ascending=[False,True]).head(2).source_id.tolist()
    histories=[]
    for dt in [.0008,.0004,.0002,.0001]:
        path=ROOT/'results/pcdr/fine_download_20261005/trials'/f"fine_{str(dt).replace('.','p')}_w120_i080_mn9_only_631430"/'spikes.parquet'
        f=pd.read_parquet(path)
        for v in selected:
            t=f.loc[f.flywire_id==v,'t'].to_numpy()
            histories.append(dict(dt_ms=dt,root_id=v,spikes=len(t),first_ms=float(t.min()*1000) if len(t) else None,
                spikes_600_650=int(np.count_nonzero((t>=.6)&(t<.65))),
                spikes_650_700=int(np.count_nonzero((t>=.65)&(t<.7))),
                times_590_700_ms=(t[(t>=.59)&(t<.7)]*1000).tolist()))
    write(out/'leading_source_spikes.json',histories)
    write(out/'complete.json',{'status':'complete','aggregate_checks':len(totals)*2,
        'annotation_sha256':digest(ROOT/'flywire_annotations.tsv'),
        'outputs':{p.name:digest(p) for p in out.iterdir()}})


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',required=True)
    run(p.parse_args().out)
