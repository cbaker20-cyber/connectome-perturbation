"""Describe early spike-event divergence in the verified separate G/H case."""
from pathlib import Path
import argparse
import io
import sys
import zipfile
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.pcdr_ccr_transfer import read,write,digest,utc


def difference(reference, intervention):
    for frame in [reference,intervention]:
        if set(frame.columns)!={'id','tick'} or frame.duplicated().any():
            raise ValueError('Invalid event inventory')
        if not frame.id.map(lambda v:type(v) is str).all() or not pd.api.types.is_integer_dtype(frame.tick):
            raise ValueError('Invalid ID or tick types')
    result=reference.merge(intervention,on=['id','tick'],how='outer',indicator=True,validate='one_to_one')
    result=result.loc[result._merge.ne('both')].copy()
    result['direction']=result._merge.map({'left_only':'reference_only','right_only':'intervention_only'}).astype(str)
    return result[['id','tick','direction']].sort_values(['tick','id','direction']).reset_index(drop=True)


def run(out):
    archive=ROOT/'CCR_separate_pathway_results.zip'
    reviewed=ROOT/'docs/pcdr/evidence/2026-10-08/separate_review.json'
    review=read(reviewed)
    if not review['checks_passed'] or digest(archive)!=review['archive_sha256']:raise ValueError('Archive not verified')
    out.mkdir(parents=True,exist_ok=False)
    write(out/'protocol.json',dict(recorded_utc=utc(),inputs={str(p):digest(p) for p in [archive,reviewed,Path(__file__)]},
        question='When do each intervention and reference first differ outside the source and two targets, and which early changed neurons are shared?',
        design='All six reference-versus-intervention comparisons. Exact neuron/tick symmetric difference; retain every changed event and first change per neuron. Summaries use fixed [600,610), [610,620), [620,650), [650,730), [730,750) ms windows and common changed-neuron sets before 650 ms. Recheck all pre-switch prefixes. No causal path inference from event order.',
        status='Post-result descriptive analysis; original endpoints and convergence rules unchanged. No simulation.'))
    source='720575940628695043';g='720575940629667639';h='720575940623862015'
    excluded={source,g,h};summaries={};shared={}
    with zipfile.ZipFile(archive) as z:
        if len(z.namelist())!=len(set(z.namelist())) or z.testzip() is not None:raise ValueError('Archive integrity failure')
        def events(condition,dt):
            frame=pd.read_parquet(io.BytesIO(z.read(f'{condition}_{dt}/spikes.parquet')))
            ticks=frame.t.to_numpy()*1000/dt
            if not np.isfinite(ticks).all() or np.max(np.abs(ticks-np.rint(ticks)),initial=0)>1e-6:raise ValueError('Off-grid event')
            return pd.DataFrame({'id':frame.flywire_id,'tick':np.rint(ticks).astype(np.int64)})
        for dt in [.0004,.0002]:
            ref=events('late_reference',dt);changed={}
            for condition in ['late_g','late_h','late_edges']:
                trial=f'{condition}_{dt}';other=events(condition,dt)
                diff=difference(ref,other)
                if (diff.tick<round(600/dt)).any():raise ValueError('Changed pre-switch history')
                # Set algebra independently verifies the keyed merge event inventory.
                a=set(ref.itertuples(index=False,name=None));b=set(other.itertuples(index=False,name=None))
                actual=set(diff[['id','tick']].itertuples(index=False,name=None))
                if actual!=a^b:raise ValueError('Independent event difference mismatch')
                diff.to_parquet(out/(trial+'_events.parquet'),index=False)
                first=diff.drop_duplicates('id').copy();first['time_ms']=first.tick*dt
                first.to_parquet(out/(trial+'_first.parquet'),index=False)
                outside=first.loc[~first.id.isin(excluded)]
                changed[condition]=set(first.loc[first.tick<round(650/dt),'id'])-excluded
                def earliest(frame):
                    if frame.empty:return []
                    return frame.loc[frame.tick.eq(frame.tick.min())].assign(time_ms=lambda x:x.tick*dt).to_dict('records')
                windows=[]
                for lo,hi in [(600,610),(610,620),(620,650),(650,730),(730,750)]:
                    d=diff.loc[diff.tick.between(round(lo/dt),round(hi/dt)-1)]
                    windows.append(dict(start_ms=lo,end_ms=hi,unmatched_events=len(d),changed_neurons=d.id.nunique(),
                        reference_only=int(d.direction.eq('reference_only').sum()),intervention_only=int(d.direction.eq('intervention_only').sum())))
                summaries[trial]=dict(first_changed_events=earliest(diff),first_changed_events_outside_selected_three=earliest(outside),
                    windows=windows,total_changed_neurons=len(first),total_unmatched_events=len(diff))
            common=set.intersection(*changed.values())
            shared[str(dt)]=dict(before_ms=650,excluding_selected_three=True,counts={k:len(v) for k,v in changed.items()},
                all_three_common_ids=sorted(common),single_common_ids=sorted(changed['late_g']&changed['late_h']))
    write(out/'results.json',dict(comparisons=summaries,early_shared=shared,completed_utc=utc(),
        limitation='Unmatched events include shifted spikes as missing-plus-added events. Shared changed neurons and ordering do not identify synaptic transmission paths, membrane-state divergence or a common causal mediator.'))
    write(out/'complete.json',dict(status='complete',outputs={p.name:digest(p) for p in out.iterdir() if p.is_file()}))
    print({k:v['first_changed_events_outside_selected_three'] for k,v in summaries.items()})


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    run(parser.parse_args().out)
