"""Measure short full-network fine-step runs before sizing a CCR study."""
import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:
    os.environ[key]='1'
from pathlib import Path
import sys,time,argparse,json
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import numpy as np
import pandas as pd
from eigencircuits.common import atomic_json,sha256,now,neuron_ids,environment
from eigencircuits.memory import peak_rss
from scripts.pcdr_bounded_process import run_bounded
from scripts.pcdr_fine_sim import input_tape,simulate


def main():
    p=argparse.ArgumentParser();p.add_argument('--dt',type=float,choices=[.0008,.0004,.0002,.0001]);a=p.parse_args()
    out=ROOT/'results/pcdr/fine_ramp_20260929'
    source=ROOT/'results/pcdr/results_ccr_20260927/raw_download/expanded_sensitivity/trials/default_baseline_631401'
    if a.dt is None:
        out.mkdir(exist_ok=False)
        atomic_json(out/'protocol.json',{'created_utc':now(),'duration_s':.01,'chunk_ms':1.,'steps_ms':[.0008,.0004,.0002,.0001],
            'selection':'First saved default baseline seed 631401; no lesion. Timing and memory study only, not a full-duration scientific comparison.',
            'source_manifest_sha256':sha256(source/'manifest.json'),
            'sources':{name:sha256(ROOT/name) for name in ['scripts/pcdr_fine_ramp.py','scripts/pcdr_fine_sim.py','model.py']}})
        for dt in [.0008,.0004,.0002,.0001]:
            label=str(dt).replace('.','p')
            result=run_bounded([sys.executable,str(Path(__file__)),'--dt',str(dt)],out/(label+'_logs'),240,cwd=ROOT)
            atomic_json(out/(label+'_process.json'),result)
            if result['returncode']!=0 or result['timed_out']:raise RuntimeError('Failed ramp case '+label)
            print(dt,result['elapsed_seconds'],flush=True)
        return
    directory=out/str(a.dt).replace('.','p');directory.mkdir(exist_ok=False)
    saved=json.loads((source/'manifest.json').read_text())
    if sha256(source/'input_events.parquet')!=saved['outputs']['input_events.parquet']:raise ValueError('Changed source input')
    ids=neuron_ids();lookup={rid:i for i,rid in enumerate(ids)};inputs=saved['input_ids']
    events=pd.read_parquet(source/'input_events.parquet');events=events[events.tick<100].copy()
    tape=input_tape(events,inputs,a.dt,.01)
    atomic_json(directory/'started.json',{'created_utc':now(),'environment':environment()})
    started=time.monotonic()
    frames=simulate(631401,[lookup[rid] for rid in inputs],[],tape=tape,duration_s=.01,dt_ms=a.dt,chunk_ms=1.,return_delivered=True)
    elapsed=time.monotonic()-started
    for name,frame in zip(['spikes','external','delivered'],frames):frame.to_parquet(directory/(name+'.parquet'),index=False)
    expected=events.copy();expected['neuron_index']=expected.flywire_id.map(lookup)
    expected['tick']=expected.tick*round(.1/a.dt)
    expected=expected[['neuron_index','tick']].sort_values(['tick','neuron_index']).reset_index(drop=True).astype('int64')
    pd.testing.assert_frame_equal(frames[1],expected)
    times=frames[0].t.to_numpy()
    if not np.allclose(times,np.rint(times*1000/a.dt)*a.dt/1000,atol=1e-12,rtol=0):raise ValueError('Off-grid spike')
    atomic_json(directory/'complete.json',{'completed_utc':now(),'dt_ms':a.dt,'duration_s':.01,'chunk_ms':1.,
        'elapsed_seconds':elapsed,'peak_rss_bytes':peak_rss(),'spikes':len(frames[0]),'external_events':len(frames[1]),
        'delivered_events':len(frames[2]),'outputs':{f.name:sha256(f) for f in directory.glob('*.parquet')},
        'limits':'Ten milliseconds of baseline only; includes initialization; not a full-run runtime prediction or convergence result.'})


if __name__=='__main__':main()
