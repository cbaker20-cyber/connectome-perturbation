"""Reconstruct signed incoming increments for the fixed early recruitment group."""
from pathlib import Path
import sys
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from eigencircuits.common import atomic_json,sha256,now,CON,sugar_ids
from eigencircuits.graph import load_signed_matrix
from scripts.pcdr_ccr_transfer import read
from scripts.pcdr_input_reconstruction import delayed_input,eligibility


def signed_inputs(weights,raster,delay):
    positive=weights.copy();negative=weights.copy()
    positive.data[positive.data<0]=0;positive.eliminate_zeros()
    negative.data[negative.data>0]=0;negative.eliminate_zeros()
    return delayed_input(positive,raster,delay),delayed_input(negative,raster,delay)


def main():
    run=ROOT/'results/pcdr/observed_replay_20260928'
    cohort=ROOT/'docs/pcdr/evidence/2026-09-28/recruitment_timing/early_large_only.csv'
    out=ROOT/'docs/pcdr/evidence/2026-09-29/early_drive'
    out.mkdir(exist_ok=False)
    validation=ROOT/'docs/pcdr/evidence/2026-09-29/input_reconstruction/results.json'
    if read(validation)['status']!='passed':raise ValueError('Unvalidated reconstruction')
    cells=pd.read_csv(cohort,dtype={'root_id':str})
    if len(cells)!=577 or cells.root_id.duplicated().any() or set(cells.root_id)&set(sugar_ids()):
        raise ValueError('Changed early non-input group')
    atomic_json(out/'protocol.json',{'recorded_utc':now(),'script_sha256':sha256(Path(__file__)),
        'cohort_sha256':sha256(cohort),'validation_sha256':sha256(validation),'connectivity_sha256':sha256(CON),
        'method':'All 577 fixed early large-only cells, all four runs, batches of eight. Separate positive and negative signed weights before accumulation, preserving inhibitory scale, delay, outgoing lesion and reconstructed refractory masking. Report raw arrivals and accepted arrivals. Windows: 0–180 ms, 180–1000 ms and the same physical 20 ms interval immediately preceding each cell first spike in the coarse lesion, exclusive of that spike. This anchor uses known outcomes and is not independent selection. No p-values, rankings or intervention selection.',
        'limits':'Reconstructed increments, not measured voltage or current. Raw arrivals are computed from actual saved presynaptic spikes, not a simulation without refractory gating. Signed components are model-defined, not measured transmitter release. Masked comparisons after firing are influenced by postsynaptic refractory state.'})
    w,ids=load_signed_matrix();ids=pd.Index(ids);selected=ids.get_indexer(cells.root_id)
    if np.any(selected<0):raise ValueError('Unknown group ID')
    base=w[selected].astype(float).tocsc();base.data*=.275;base.data[base.data<0]*=.8;base.data*=1.2
    plan=read(run/'plan.json');certificate=read(ROOT/'docs/pcdr/evidence/2026-09-28/observed_replay_check.json')
    verified={r['trial']:r for r in certificate['rows']};rows=[]
    for j in plan['jobs']:
        directory=run/j['id'];m=read(directory/'manifest.json')
        if sha256(directory/'manifest.json')!=verified[j['id']]['manifest_sha256']:raise ValueError('Changed trial')
        if sha256(directory/'spikes.parquet')!=m['outputs']['spikes.parquet']:raise ValueError('Changed spikes')
        spikes=pd.read_parquet(directory/'spikes.parquet');n=round(1000/j['dt_ms'])
        tick=np.rint(spikes.t.to_numpy()*1000/j['dt_ms']).astype(np.int64);pre=ids.get_indexer(spikes.flywire_id)
        if np.any(pre<0) or np.any(tick<0) or np.any(tick>=n):raise ValueError('Invalid spike')
        raster=csr_matrix((np.ones(len(tick)),(pre,tick)),shape=(len(ids),n))
        if np.any(raster.data!=1):raise ValueError('Duplicate spike')
        weights=base.copy()
        for col in ids.get_indexer(j['lesion_ids']):
            if col<0:raise ValueError('Unknown lesion')
            weights.data[weights.indptr[col]:weights.indptr[col+1]]=0
        weights.eliminate_zeros();weights=weights.tocsr()
        for start in range(0,len(cells),8):
            pos,neg=signed_inputs(weights[start:start+8],raster,round(1.8/j['dt_ms']))
            for local,i in enumerate(range(start,min(start+8,len(cells)))):
                mask=eligibility(tick[pre==selected[i]],n,round(2.2/j['dt_ms']))
                end=float(cells.iloc[i].lesion_coarse_first_ms)
                for label,a,b in [('early',0.,180.),('later',180.,1000.),('pre_first_20ms',max(0.,end-20),end)]:
                    lo,hi=round(a/j['dt_ms']),round(b/j['dt_ms'])
                    gate=mask[lo:hi];p=pos[local,lo:hi];q=neg[local,lo:hi]
                    rows.append({'condition':j['condition'],'dt_ms':j['dt_ms'],'root_id':cells.iloc[i].root_id,
                        'window':label,'start_ms':a,'end_ms':b,'positive_raw_mV':float(p.sum()),
                        'negative_raw_mV':float(q.sum()),'positive_accepted_mV':float(p[gate].sum()),
                        'negative_accepted_mV':float(q[gate].sum()),'refractory_fraction':float((~gate).mean())})
        print('Completed '+j['id'],flush=True)
    frame=pd.DataFrame(rows);frame.to_csv(out/'cell_inputs.csv',index=False)
    sums=frame.groupby(['condition','dt_ms','window'])[['positive_raw_mV','negative_raw_mV','positive_accepted_mV','negative_accepted_mV']].sum()
    sums.to_csv(out/'group_sums.csv')
    atomic_json(out/'record.json',{'status':'complete','completed_utc':now(),'cells':len(cells),'rows':len(frame),
        'outputs':{p.name:sha256(p) for p in out.iterdir() if p.is_file()}})


if __name__=='__main__':main()
