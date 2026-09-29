"""Validate reconstructed synaptic increments against saved state recordings."""
from pathlib import Path
import sys
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from eigencircuits.common import atomic_json,sha256,now,CON
from eigencircuits.graph import load_signed_matrix
from scripts.pcdr_ccr_transfer import read


def eligibility(spike_ticks, total_ticks, refractory_ticks):
    if refractory_ticks < 1: raise ValueError('Positive refractory duration required')
    spikes=np.asarray(spike_ticks,dtype=np.int64)
    if np.any(spikes<0) or np.any(spikes>=total_ticks): raise ValueError('Invalid spike tick')
    changes=np.zeros(total_ticks+1,dtype=np.int64)
    np.add.at(changes,spikes,1)
    np.add.at(changes,np.minimum(spikes+refractory_ticks,total_ticks),-1)
    return np.cumsum(changes[:-1])==0


def delayed_input(weights, raster, delay_ticks):
    if delay_ticks < 0: raise ValueError('Negative delay')
    incoming=(weights@raster).toarray()
    delayed=np.zeros_like(incoming)
    if delay_ticks==0:return incoming
    if delay_ticks<incoming.shape[1]:delayed[:,delay_ticks:]=incoming[:,:-delay_ticks]
    return delayed


def main():
    run=ROOT/'results/pcdr/observed_replay_20260928'
    out=ROOT/'docs/pcdr/evidence/2026-09-29/input_reconstruction'
    out.mkdir(parents=True,exist_ok=False)
    plan=read(run/'plan.json')
    certificate=read(ROOT/'docs/pcdr/evidence/2026-09-28/observed_replay_check.json')
    atomic_json(out/'protocol.json',{'recorded_utc':now(),'script_sha256':sha256(Path(__file__)),
        'connectivity_sha256':sha256(CON),'absolute_tolerance_mV':1e-9,
        'method':'Read all four verified spike files. Multiply selected postsynaptic rows of signed connectivity by sparse presynaptic spike counts, apply 0.275 mV, weight scale 1.2 and inhibitory scale 0.8, remove outgoing lesion columns, and delay 1.8 ms. Reconstruct non-input after-threshold eligibility from spike ticks and the 2.2 ms refractory interval, including the spike tick and excluding the recovery tick. Compare eligibility exactly and predicted masked increments against after_synapses g minus before_thresholds g at every tick. Ungated errors are a diagnostic, not the specified accepted model.',
        'limit':'Validates event increments for ten non-input cells in four cases, not voltages, causal pathways or convergence. No new simulation.'})
    w,ids=load_signed_matrix();ids=pd.Index(ids)
    selected=ids.get_indexer(plan['record_ids'])
    if np.any(selected<0):raise ValueError('Unknown recording cell')
    base=w[selected].astype(float).tocsc()
    base.data*=.275
    base.data[base.data<0]*=.8
    base.data*=1.2
    checked={r['trial']:r for r in certificate['rows']}
    rows=[]
    for j in plan['jobs']:
        directory=run/j['id'];m=read(directory/'manifest.json')
        if sha256(directory/'manifest.json')!=checked[j['id']]['manifest_sha256']:raise ValueError('Changed manifest')
        for name in ['spikes.parquet','states.npz']:
            if sha256(directory/name)!=m['outputs'][name]:raise ValueError('Changed reference')
        spikes=pd.read_parquet(directory/'spikes.parquet')
        n=round(1000/j['dt_ms']);tick=np.rint(spikes.t.to_numpy()*1000/j['dt_ms']).astype(np.int64)
        pre=ids.get_indexer(spikes.flywire_id)
        if np.any(pre<0) or np.any(tick<0) or np.any(tick>=n):raise ValueError('Invalid spike')
        if not np.allclose(spikes.t,tick*j['dt_ms']/1000,atol=1e-10,rtol=0):raise ValueError('Off-grid spike')
        raster=csr_matrix((np.ones(len(tick)),(pre,tick)),shape=(len(ids),n))
        if np.any(raster.data!=1):raise ValueError('Duplicate spike')
        weights=base.copy()
        for col in ids.get_indexer(j['lesion_ids']):
            if col<0:raise ValueError('Unknown lesion cell')
            weights.data[weights.indptr[col]:weights.indptr[col+1]]=0
        weights.eliminate_zeros()
        predicted=delayed_input(weights.tocsr(),raster,round(1.8/j['dt_ms']))
        with np.load(directory/'states.npz',allow_pickle=False) as state:
            actual=state['after_synapses_g_mV']-state['before_thresholds_g_mV']
            mask=np.array([eligibility(tick[pre==cell],n,round(2.2/j['dt_ms'])) for cell in selected])
            mask_errors=int(np.count_nonzero(mask!=state['after_synapses_not_refractory']))
            error=np.abs(predicted*mask-actual)
            rows.append({'trial':j['id'],'samples':int(error.size),'eligibility_mismatches':mask_errors,
                'max_absolute_error_mV':float(error.max()),'samples_exceeding_tolerance':int((error>1e-9).sum()),
                'ungated_max_absolute_error_mV':float(np.abs(predicted-actual).max())})
    passed=all(r['eligibility_mismatches']==0 and r['samples_exceeding_tolerance']==0 for r in rows)
    atomic_json(out/'results.json',{'status':'passed' if passed else 'failed','rows':rows,'completed_utc':now()})
    print(read(out/'results.json'))
    if not passed:raise ValueError('Reconstruction did not match; preserve diagnostics')


if __name__=='__main__':main()
