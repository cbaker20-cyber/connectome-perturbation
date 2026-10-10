"""Attribute reconstructed crossing-state voltage to actual presynaptic sources."""
import argparse
from pathlib import Path
import sys
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.pcdr_ccr_transfer import read,write,digest,utc
from scripts.pcdr_first_spike import kernel


def run(out):
    crossing=ROOT/'results/pcdr/count_crossings_20261010'
    gating=ROOT/'results/pcdr/baseline_gating_20261010'
    for folder in [crossing,gating]:
        verification=read(folder/'verification.json')
        if verification['status']!='verified':raise ValueError('Unverified input')
        for name,h in verification['outputs'].items():
            if digest(folder/name)!=h:raise ValueError('Changed verified output')
    out.mkdir(parents=True,exist_ok=False)
    write(out/'protocol.json',dict(recorded_utc=utc(),inputs={str(p):digest(p) for p in [Path(__file__),ROOT/'scripts/pcdr_first_spike.py',crossing/'results.json',crossing/'verification.json',gating/'verification.json']},
        design='All 52 states at the previously selected first cumulative two-spike gaps. Group accepted since-reset voltage contributions by exact presynaptic ID. Preserve signed contributions, every source, no new event selection. Rank largest inhibitory contributor per state only for descriptive summaries.',
        limitations='Conditional algebraic attribution after observed resets, not causal deletion effects. Histories may have unequal integration durations. Repeated targets/sources do not constitute independent evidence. Ranking is descriptive and no new intervention is authorized.'))
    rows=[];summary=[]
    for r in read(crossing/'results.json')['records']:
        if not r['selected']:continue
        events=pd.read_parquet(gating/f"{r['seed']}_events.parquet")
        for label,s in r['states'].items():
            last=-1 if s['last_reset_tick'] is None else s['last_reset_tick']
            selected=events[(events.tick>last)&(events.tick<s['tick'])&events['accept_'+label].eq(True)].copy()
            selected['contribution_mv']=selected['weight_mv_'+label]*kernel((s['tick']-selected.tick.to_numpy())*.0001)
            contributions=selected.groupby('source_id').contribution_mv.sum()
            if abs(float(contributions.sum())+52-s['voltage_mv'])>1e-10:raise ValueError('Source sum mismatch')
            for neuron,value in contributions.items():
                rows.append(dict(seed=r['seed'],target_id=r['target_id'],role='leading' if label==r['gap']['leader'] else 'other',run=label,
                    source_id=neuron,contribution_mv=float(value)))
            negative=contributions[contributions<0].sort_values()
            inhibition=float(-negative.sum())
            summary.append(dict(seed=r['seed'],target_id=r['target_id'],role='leading' if label==r['gap']['leader'] else 'other',run=label,
                tick=s['tick'],voltage_mv=s['voltage_mv'],last_reset_tick=last,
                total_inhibitory_contribution_magnitude_mv=inhibition,
                largest_inhibitory_source=None if negative.empty else str(negative.index[0]),
                largest_inhibitory_contribution_magnitude_mv=0 if negative.empty else float(-negative.iloc[0]),
                largest_inhibitory_fraction=None if not inhibition else float(-negative.iloc[0]/inhibition)))
    pd.DataFrame(rows).to_csv(out/'source_contributions.csv',index=False)
    write(out/'results.json',dict(completed_utc=utc(),records=summary))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
    run(p.parse_args().out)
