"""Describe actual CB4058 arrivals relative to the selected targets' resets."""
import argparse
from pathlib import Path
import sys
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.pcdr_ccr_transfer import read,write,digest,utc
from scripts.pcdr_first_spike import kernel

SOURCE='720575940643867296'


def run(out):
    crossing=ROOT/'results/pcdr/count_crossings_20261010'
    sources=ROOT/'results/pcdr/crossing_sources_fixed_20261010'
    gating=ROOT/'results/pcdr/baseline_gating_20261010'
    for folder in (crossing,sources,gating):
        v=read(folder/'verification.json')
        if v['status']!='verified':raise ValueError('Unverified input')
        for name,h in v['outputs'].items():
            if digest(folder/name)!=h:raise ValueError('Changed input evidence')
    out.mkdir(parents=True,exist_ok=False)
    write(out/'protocol.json',dict(recorded_utc=utc(),inputs={str(p):digest(p) for p in [Path(__file__),ROOT/'scripts/pcdr_first_spike.py',crossing/'results.json',sources/'results.json',gating/'verification.json']},
        source_id=SOURCE,selection='Source selected after it led inhibitory contribution in16 of26 other-run states. Keep all26 prior selected targets and four absent cases. Inspect actual arrivals before each previously fixed comparison tick, not new event or seed maxima.',
        design='For each native history, count this source arrivals before state time, classify latest as cleared by target reset, blocked during refractory, or retained; sum accepted post-reset contributions and compare prior independent source decomposition. Latest arrivals across runs are descriptions of cutoffs, not asserted matches of physical spikes.',
        limitations='Post-result source selection; target reset history is a confounder. A cleared contribution may follow earlier target spiking rather than cause it. Do not construct deletion counterfactuals or infer mechanism frequency across all neurons.'))
    previous=pd.read_csv(sources/'source_contributions.csv',dtype={'source_id':str})
    rows=[]
    for r in read(crossing/'results.json')['records']:
        if not r['selected']:
            rows.append(dict(seed=r['seed'],selected=False));continue
        f=pd.read_parquet(gating/f"{r['seed']}_events.parquet")
        for label,s in r['states'].items():
            last=-1 if s['last_reset_tick'] is None else s['last_reset_tick']
            events=f[(f.source_id==SOURCE)&(f.tick<s['tick'])&f['weight_mv_'+label].notna()].sort_values('tick')
            since=events[events.tick>last]
            retained=since[since['accept_'+label].eq(True)]
            value=float((retained['weight_mv_'+label]*kernel((s['tick']-retained.tick.to_numpy())*.0001)).sum())
            old=previous[(previous.seed==r['seed'])&(previous.run==label)&(previous.source_id==SOURCE)].contribution_mv
            if len(old)>1 or abs(value-(float(old.iloc[0]) if len(old) else 0))>1e-10:raise ValueError('Source contribution mismatch')
            status='no_arrival'
            if len(events):
                e=events.iloc[-1]
                status='cleared_by_reset' if e.tick<=last else ('retained_since_reset' if e['accept_'+label] else 'blocked_refractory')
            rows.append(dict(seed=r['seed'],selected=True,target_id=r['target_id'],role='leading' if label==r['gap']['leader'] else 'other',run=label,
                state_tick=s['tick'],last_reset_tick=last,source_arrivals_before_state=len(events),
                source_arrivals_since_reset=len(since),accepted_since_reset=len(retained),blocked_since_reset=len(since)-len(retained),
                source_voltage_contribution_mv=value,latest_arrival_tick=None if events.empty else int(events.tick.iloc[-1]),latest_arrival_status=status))
    pd.DataFrame(rows).to_csv(out/'histories.csv',index=False)
    write(out/'complete.json',dict(status='complete',completed_utc=utc(),outputs={p.name:digest(p) for p in out.iterdir() if p.is_file()}))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
    run(p.parse_args().out)
