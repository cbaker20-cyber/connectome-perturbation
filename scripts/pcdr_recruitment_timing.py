"""Map recruitment in four saved runs; do not select an intervention."""
import os
os.environ['MPLBACKEND'] = 'Agg'
from pathlib import Path
import sys
import numpy as np
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from eigencircuits.common import atomic_json, sha256, now, sugar_ids, CON
from eigencircuits.graph import load_signed_matrix
from scripts.pcdr_ccr_transfer import read


def activity(frame, ids):
    if not set(frame.flywire_id) <= set(ids): raise ValueError('Unknown neuron ID')
    if not np.isfinite(frame.t).all() or (frame.t < 0).any() or (frame.t >= 1).any():
        raise ValueError('Invalid spike time')
    grouped = frame.groupby('flywire_id').t
    return grouped.size().reindex(ids, fill_value=0), grouped.min().reindex(ids)


def main():
    run = ROOT / 'results/pcdr/observed_replay_20260928'
    out = ROOT / 'docs/pcdr/evidence/2026-09-28/recruitment_timing'
    out.mkdir(exist_ok=False)
    plan = read(run / 'plan.json')
    features_path = ROOT / 'results/pcdr/corrected_20260919/analysis/features.parquet'
    certificate_path = ROOT / 'docs/pcdr/evidence/2026-09-28/observed_replay_check.json'
    certificate = read(certificate_path)
    atomic_json(out / 'protocol.json', {'recorded_utc': now(), 'script_sha256': sha256(Path(__file__)),
        'features_sha256': sha256(features_path), 'connectivity_sha256': sha256(CON),
        'verification_sha256': sha256(certificate_path),
        'rules': 'Exclude the 21 stimulated inputs from recruitment summaries. Retain union of spiking cells. Define large-only cells as active in the 0.0125 ms lesion and silent throughout all other three one-second runs. This uses full outcomes and is descriptive, not a cell type. Record first spikes and full counts in every run. Use 10 ms first-recruitment bins. Split large-only cells by first spike before 180 ms versus at/after 180 ms; 180 ms is an outcome-informed description before the previously observed sharp rise, not an independently estimated transition. Report all early cells, annotation counts and static directed edge counts among early and later large-only cells after zeroing lesioned outgoing edges. No rankings for intervention, enrichment test or causal path claims.'})
    f = pd.read_parquet(features_path).set_index('root_id'); f.index = f.index.astype(str)
    if not f.index.is_unique: raise ValueError('Duplicate feature IDs')
    table = f[['super_class','cell_type','model_sign']].copy()
    table.index.name = 'root_id'
    bins, names = [], []
    verified = {r['trial']: r for r in certificate['rows']}
    for j in plan['jobs']:
        directory = run / j['id']
        if sha256(directory / 'manifest.json') != verified[j['id']]['manifest_sha256']: raise ValueError('Changed manifest')
        m = read(directory / 'manifest.json')
        if sha256(directory / 'spikes.parquet') != m['outputs']['spikes.parquet']: raise ValueError('Changed spikes')
        spikes = pd.read_parquet(directory / 'spikes.parquet')
        name = ('baseline' if j['condition']=='baseline' else 'lesion') + ('_coarse' if j['dt_ms']==.0125 else '_fine')
        names.append(name)
        count, first = activity(spikes, table.index)
        table[name+'_count'] = count
        table[name+'_first_ms'] = first * 1000
        recruited = first.loc[~first.index.isin(sugar_ids())].dropna().to_numpy()
        histogram = np.bincount(np.floor((recruited+1e-12)/.01).astype(int), minlength=100)
        bins.extend({'run':name, 'start_ms':i*10,'first_spiking_cells':int(n)} for i,n in enumerate(histogram))
    table = table.loc[~table.index.isin(sugar_ids())]
    union = table[[n+'_count' for n in names]].sum(axis=1)>0
    table = table.loc[union].copy()
    other = ['baseline_coarse','baseline_fine','lesion_fine']
    only = (table.lesion_coarse_count>0) & (table[[n+'_count' for n in other]].sum(axis=1)==0)
    table['group'] = np.where(only, 'large_only', 'other_active')
    table['early_large_only'] = only & (table.lesion_coarse_first_ms < 180)
    table['recorded_state'] = table.index.isin(plan['record_ids'])
    table.to_csv(out/'active_cells.csv')
    early = table.loc[table.early_large_only].sort_values(['lesion_coarse_first_ms'], kind='stable')
    early.to_csv(out/'early_large_only.csv')
    annotation_rows=[]
    for label, selected in [('large_only',table.loc[only]),('early_large_only',early),('other_active',table.loc[~only])]:
        for field in ['super_class','model_sign']:
            for value,count in selected[field].fillna('unavailable').value_counts().items():
                annotation_rows.append({'group':label,'field':field,'value':str(value),'cells':int(count)})
    pd.DataFrame(annotation_rows).to_csv(out/'annotations.csv',index=False)
    w, ids = load_signed_matrix()
    index = pd.Index(ids)
    lesion = next(j['lesion_ids'] for j in plan['jobs'] if j['condition']=='mode_without_mn9')
    w = w.tocsc()
    for col in index.get_indexer(lesion):
        if col < 0: raise ValueError('Unknown lesion ID')
        w.data[w.indptr[col]:w.indptr[col+1]] = 0
    w.eliminate_zeros(); w=w.tocsr()
    groups={'early':early.index,'later':table.index[only & ~table.early_large_only]}
    connections=[]
    for source,pre_ids in groups.items():
        for target,post_ids in groups.items():
            pre,post=index.get_indexer(pre_ids),index.get_indexer(post_ids)
            if np.any(pre<0) or np.any(post<0): raise ValueError('Unknown group ID')
            data=w[post][:,pre].data
            connections.append({'source':source,'target':target,'source_cells':len(pre),'target_cells':len(post),
                                'positive_edges':int((data>0).sum()),'negative_edges':int((data<0).sum())})
    pd.DataFrame(connections).to_csv(out/'connections.csv',index=False)
    pop = pd.DataFrame(bins);pop.to_csv(out/'recruitment_bins.csv',index=False)
    import matplotlib.pyplot as plt
    fig, ax=plt.subplots(figsize=(8,4.5))
    for name in names:
        data=pop[pop.run==name]
        ax.plot(data.start_ms+10,data.first_spiking_cells.cumsum(),label=name.replace('_',' '))
    ax.set(xlabel='Time (ms)',ylabel='Cumulative non-input cells with a spike')
    ax.legend();fig.tight_layout();fig.savefig(out/'recruitment.png',dpi=160);plt.close(fig)
    atomic_json(out/'summary.json', {'completed_utc':now(),'large_only_cells':int(only.sum()),
        'early_large_only_cells':len(early),'large_only_spikes':int(table.loc[only,'lesion_coarse_count'].sum()),
        'large_only_recorded_cells':int(table.loc[only,'recorded_state'].sum()),
        'recruited_by_run':{n:int((table[n+'_count']>0).sum()) for n in names},
        'first_large_only_ms':float(table.loc[only,'lesion_coarse_first_ms'].min()) if only.any() else None,
        'outputs':{p.name:sha256(p) for p in out.iterdir() if p.is_file()}})


if __name__=='__main__': main()
