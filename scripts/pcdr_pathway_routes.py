"""Check direct connectivity and delay compatibility of earliest outside changes."""
from pathlib import Path
import argparse
import json
import sys
import zipfile
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.pcdr_ccr_transfer import read,write,digest,utc


def arrivals(events, weight, delay_ticks, deadline):
    if delay_ticks<0 or type(delay_ticks) is not int:raise ValueError('Invalid delay')
    if events.duplicated(['id','tick']).any():raise ValueError('Duplicate events')
    rows=[]
    for event in events.itertuples(index=False):
        if event.direction not in ['reference_only','intervention_only']:raise ValueError('Unknown direction')
        arrival=int(event.tick)+delay_ticks
        if arrival<=deadline and weight!=0:
            rows.append(dict(source_id=event.id,emission_tick=int(event.tick),arrival_tick=arrival,
                intervention_minus_reference_increment_mv=weight*(1 if event.direction=='intervention_only' else -1),
                direction=event.direction))
    return rows


def run(out):
    previous=ROOT/'results/pcdr/pathway_divergence_20261008'
    archive=ROOT/'CCR_separate_pathway_results.zip'
    for path,h in read(previous/'protocol.json')['inputs'].items():
        if digest(path)!=h:raise ValueError('Changed prior input: '+path)
    for name,h in read(previous/'complete.json')['outputs'].items():
        if digest(previous/name)!=h:raise ValueError('Changed prior output: '+name)
    summary=read(previous/'results.json');out.mkdir(parents=True,exist_ok=False)
    write(out/'protocol.json',dict(recorded_utc=utc(),inputs={str(p):digest(p) for p in [archive,previous/'results.json',Path(__file__)]},
        question='Are direct G/H connections and delayed unmatched emissions compatible with each earliest outside spike difference?',
        design='All six saved earliest-outside targets; inspect both G and H edges, actual scaled signed weights and queued arrival ticks through the first changed event. Retain all unmatched upstream emissions before that deadline; no new intervention.',
        limitation='Predicted synaptic increments from saved spikes and connectivity are not measured conductance or voltage; receptor/refractory/reset state and other inputs can alter effects. Delay compatibility is not sufficiency.'))
    with zipfile.ZipFile(archive) as z:
        plan=json.loads(z.read('diagnostic_plan.json'))
        for name,h in plan['model_files'].items():
            if digest(ROOT/name)!=h:raise ValueError('Changed model/data: '+name)
        model=z.read('source/model.py').decode()
        if "'t_dly'     : 1.8*ms" not in model or "on_pre='g += w', delay=params['t_dly']" not in model:
            raise ValueError('Unreviewed delay or synaptic update')
        source_record=dict(model_source_sha256=__import__('hashlib').sha256(model.encode()).hexdigest(),delay_ms=1.8,
            archived_model_lines=[line for line in model.splitlines() if "'t_dly'" in line or "on_pre='g += w'" in line])
    ids=pd.read_csv(ROOT/'2023_03_23_completeness_630_final.csv',index_col=0).index.astype(str)
    if not ids.is_unique:raise ValueError('Duplicate neuron IDs')
    lookup={v:i for i,v in enumerate(ids)}
    con=pd.read_parquet(ROOT/'2023_03_23_connectivity_630_final.parquet')
    selected=['720575940629667639','720575940623862015'];records={}
    for trial,info in summary['comparisons'].items():
        dt=float(trial.rsplit('_',1)[1]);delay=round(1.8/dt)
        if abs(delay*dt-1.8)>1e-12:raise ValueError('Off-grid delay')
        diff=pd.read_parquet(previous/(trial+'_events.parquet'))
        records[trial]=[]
        for target in info['first_changed_events_outside_selected_three']:
            deadline=target['tick'];edges=[]
            for source in selected:
                rows=con.loc[con.Presynaptic_Index.eq(lookup[source])&con.Postsynaptic_Index.eq(lookup[target['id']])]
                if len(rows)>1:raise ValueError('Duplicate connection pair')
                weight=0. if rows.empty else float(rows['Excitatory x Connectivity'].iloc[0])*.275*1.2
                if weight<0:weight*=.8
                if source in plan['lesion_ids']:weight=0.
                upstream=diff.loc[diff.id.eq(source)]
                predicted=arrivals(upstream,weight,delay,deadline)
                edges.append(dict(source_id=source,connection_present=not rows.empty,scaled_weight_mv=weight,
                    arrivals_before_or_at_target_change=predicted,
                    earliest_arrival_to_change_ms=None if not predicted else (deadline-min(r['arrival_tick'] for r in predicted))*dt))
            records[trial].append(dict(target=target,edges=edges))
    write(out/'results.json',dict(comparisons=records,source=source_record,completed_utc=utc(),
        conclusion_scope='Direct-edge presence and timing compatibility only. Predicted increments are not observed state changes or causal mediation.'))
    write(out/'complete.json',dict(status='complete',outputs={p.name:digest(p) for p in out.iterdir() if p.is_file()}))
    print(json.dumps(records,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    run(parser.parse_args().out)
