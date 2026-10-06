"""Decompose a selected cell's first crossing using its recorded initial state and arrivals."""
import io
import json
from pathlib import Path
import sys
import zipfile
import argparse
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.pcdr_ccr_transfer import digest,write


def kernel(lag):
    lag=np.asarray(lag,dtype=float)
    if np.any(lag<0) or not np.isfinite(lag).all():
        raise ValueError('Nonnegative finite lag required')
    return (-1/3)*(np.exp(-lag/5)-np.exp(-lag/20))


def run(archive,events_dir,out,root='720575940628455942'):
    validation=json.loads((ROOT/'docs/pcdr/evidence/2026-10-05/diagnostic_return/validation.json').read_text())
    if digest(archive)!=validation['archive_sha256']:raise ValueError('Changed archive')
    if root not in ['720575940628455942','720575940639283278']:
        raise ValueError('Choose a recorded first-spike target covered by selected_events.csv')
    dt=.0004
    events_path=events_dir/'selected_events.csv'
    events=pd.read_csv(events_path,dtype={'source_id':str,'target_id':str})
    with zipfile.ZipFile(archive) as z:
        plan=json.loads(z.read('diagnostic_plan.json'));i=plan['record_ids'].index(root)
        spikes=pd.read_parquet(io.BytesIO(z.read(f'{dt}/spikes.parquet')))
        times=spikes.loc[spikes.flywire_id.eq(root),'t'].to_numpy()*1000
        if not len(times) or not 600<times[0]<650:
            raise ValueError('First spike must fall inside the saved event interval, 600–650 ms')
        tick=round(times[0]/dt); t=tick*dt
        start=(tick//round(10/dt))*round(10/dt)
        with np.load(io.BytesIO(z.read(f'{dt}/state/{round(600/dt):010d}_before_thresholds.npz')),allow_pickle=False) as a:
            v,g=float(a['v_mV'][i,0]),float(a['g_mV'][i,0])
        with np.load(io.BytesIO(z.read(f'{dt}/state/{start:010d}_before_thresholds.npz')),allow_pickle=False) as a:
            observed=float(a['v_mV'][i,tick-start])
    selected=events[(events.dt_ms==dt)&events.target_id.eq(root)&(events.arrival_tick<tick)].copy()
    if selected.empty or not selected.accepted.all() or (selected.arrival_ms<600).any():
        raise ValueError('Expected accepted events after the initial observation')
    selected['voltage_contribution_mV']=selected.weight_mV*kernel((tick-selected.arrival_tick.to_numpy())*dt)
    base=-52+(v+52)*np.exp(-(t-600)/20)+g*kernel(t-600)
    predicted=float(base+selected.voltage_contribution_mV.sum())
    if abs(predicted-observed)>1e-8:raise ValueError('Decomposition differs from recorded voltage')
    out.mkdir(parents=True,exist_ok=False)
    selected.sort_values('voltage_contribution_mV',ascending=False).to_csv(out/'contributions.csv',index=False)
    write(out/'summary.json',dict(root_id=root,dt_ms=dt,first_spike_ms=t,recorded_voltage_mV=observed,
        initial_state_only_voltage_mV=float(base),reconstructed_voltage_mV=predicted,
        absolute_error_mV=abs(predicted-observed),script_sha256=digest(Path(__file__)),
        events_sha256=digest(events_path),archive_sha256=validation['archive_sha256'],
        interpretation='Linear decomposition before the first spike, conditional on observed arrivals. No network intervention or claim of first divergence.'))
    print((out/'summary.json').read_text())


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('archive',type=Path);p.add_argument('events_dir',type=Path);p.add_argument('out',type=Path)
    p.add_argument('--root',default='720575940628455942')
    a=p.parse_args();run(a.archive,a.events_dir,a.out,a.root)
