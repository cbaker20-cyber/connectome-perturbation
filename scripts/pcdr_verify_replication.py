"""Verify every completed optimized-pilot trial and recompute all readouts."""
from pathlib import Path
import sys,json
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from eigencircuits.common import now,sha256,atomic_json,MN9
S=ROOT/'results/pcdr/seed_replication_20260921'
plan=json.loads((S/'jobs.json').read_text());summary=json.loads((S/'summary.json').read_text())
assert len(plan['jobs'])==210 and summary['primary']==[] and summary['status']=='complete'
assert not (S/'pilot_comparison.json').exists()
assert not (S/'analysis/secondary_tests.parquet').exists()
features=pd.read_parquet(ROOT/'results/pcdr/corrected_20260919/analysis/features.parquet').set_index('root_id')
ids=features.index.tolist();motor=features.index[features.super_class=='motor'].tolist()
results=json.loads((S/'analysis/results.json').read_text());assert len(results)==6
rates={};manifests={};sources={}
for job in plan['jobs']:
    d=S/'trials'/job['trial_id'];m=json.loads((d/'manifest.json').read_text())
    assert m['status']=='complete' and m['seed']==job['seed'] and m['trial_id']==job['trial_id']
    assert sorted(m['lesion_ids'])==sorted(job['lesion_ids'])
    assert m['provenance']['inputs']==plan['provenance']['inputs'] and m['provenance']['sources']==plan['provenance']['sources']
    for name,digest in m['outputs'].items():assert sha256(d/name)==digest
    r=pd.read_parquet(d/'rates.parquet').set_index('root_id')
    assert r.index.is_unique and set(r.index)==set(ids)
    rates[(job['condition'],job['seed'])]=r.reindex(ids).rate_hz
    manifests[(job['condition'],job['seed'])]=m;sources[str(d/'manifest.json')]=sha256(d/'manifest.json')
rows=[];checks=[];delivered=0
for result in results:
    condition=result['condition'];support=result['support_ids'];ds=[]
    for seed in plan['seeds']:
        a=manifests[('baseline',seed)];b=manifests[(condition,seed)]
        for key in ['input_digest','input_protocol','duration_s','dt_ms','context','input_hz','weight_scale','inhibitory_scale','strong_fraction','backend']:
            assert a[key]==b[key]
        delivered+=int(a['delivered_input_digest']==b['delivered_input_digest'])
        delta=rates[(condition,seed)]-rates[('baseline',seed)];ds.append(delta.to_numpy())
        total=float(abs(delta).sum());inside=float(abs(delta.loc[support]).sum())
        rows.append({'condition':condition,'seed':seed,'A_single_seed':inside/len(support),'F_single_seed':inside/total if total else None,
            'MN9_delta_hz':float(delta.loc[MN9]),'motor_total_delta_hz':float(delta.loc[motor].sum()),
            'baseline_MN9_hz':float(rates[('baseline',seed)].loc[MN9]),'lesion_MN9_hz':float(rates[(condition,seed)].loc[MN9])})
    mean=pd.Series(np.mean(ds,axis=0),index=ids);total=float(abs(mean).sum());inside=float(abs(mean.loc[support]).sum())
    for key,value in {'A':inside/len(support),'F':inside/total,'mn9_delta_hz':mean.loc[MN9],
                      'motor_total_delta_hz':mean.loc[motor].sum(),'motor_mean_delta_hz':mean.loc[motor].mean(),
                      'off_absolute_sum_hz':total-inside}.items():np.testing.assert_allclose(result[key],value,rtol=1e-12,atol=1e-10)
    footprint=S/'analysis/default'/condition/'footprint.parquet';fp=pd.read_parquet(footprint).set_index('root_id')
    assert fp.index.is_unique and len(fp)==127400
    np.testing.assert_allclose(fp.reindex(ids).delta_hz,mean,rtol=1e-12,atol=1e-10)
    checks.append({'condition':condition,'MN9_in_support':MN9 in support,'motor_cells_in_support':len(set(motor)&set(support)),
                   'footprint_rows':len(fp),'footprint_sha256':sha256(footprint)})
pd.DataFrame(rows).to_csv(S/'per_seed_readouts.csv',index=False)
audit={'checked_utc':now(),'trials_verified':210,'paired_inputs_verified':180,'delivered_input_pairs_equal':delivered,
       'lesion_summaries_verified':6,'checks':checks,'reference_p_values':'absent','source_manifests':sources,
       'command':'.venv/Scripts/python.exe scripts/pcdr_verify_replication.py','code_sha256':sha256(__file__)}
atomic_json(S/'completion_audit.json',audit)
mode=next(r for r in results if r['condition']=='mode');others=[r for r in results if r['condition']!='mode']

prior=json.loads((ROOT/'results/pcdr/optimized_pilot_20260921/analysis/results.json').read_text())
lines=['# Fresh seed replication completed','', 'Completed '+summary['finished_utc']+'. Verified '+now()+'.', '',
'- All 210 trials and 180 paired-input comparisons passed verification. All six 127,400-neuron mean footprints agree with independently recomputed rates; all recorded trial output hashes match. No reference p-values were computed.',
'- This 30-seed replication uses seeds 631001–631030 and the same six frozen lesion sets. It is separate from the earlier five-seed pilot. It checks stochastic-input reproducibility, not biological replication, a random-control null, or confirmation.',
'- MN9 belongs to the eigen-set but none of the comparisons. The eigen-set contains 13 motor cells; comparisons contain 5,4,3,3,4. Cell-class and readout membership remain unmatched. Optimized sets overlap and are not uniform random draws.',
'', '## All results on the new seeds','',
'| Set | A Hz | F | MN9 change Hz | Motor total change Hz | Motor mean change Hz |','|---|---:|---:|---:|---:|---:|']
for r in results:lines.append(f'| {r["condition"]} | {r["A"]:.3f} | {r["F"]:.4f} | {r["mn9_delta_hz"]:.3f} | {r["motor_total_delta_hz"]:.3f} | {r["motor_mean_delta_hz"]:.3f} |')
lines += ['',f'- Eigen-set A exceeds all five comparisons: {all(mode["A"]>r["A"] for r in others)}. Eigen-set F exceeds all five: {all(mode["F"]>r["F"] for r in others)}. These are descriptive orderings, not significance tests.',f'- Off-support response remains {100*(1-mode["F"]):.2f}% of total absolute mean response. This does not establish circuit independence.', '', '## Pilot and replication kept separate','', '| Set | Pilot A | New A | Pilot F | New F |','|---|---:|---:|---:|---:|']
for r in results:
    p=next(x for x in prior if x['condition']==r['condition'])
    lines.append(f'| {r["condition"]} | {p["A"]:.3f} | {r["A"]:.3f} | {p["F"]:.4f} | {r["F"]:.4f} |')
lines += ['', '## Paired seed uncertainty','', '| Set | A 95 percent interval | F 95 percent interval |','|---|---|---|']
for r in results:
    a=r['interval']['A_95pct'];f=r['interval']['F_95pct']
    lines.append(f'| {r["condition"]} | {a[0]:.3f} to {a[1]:.3f} | {f[0]:.4f} to {f[1]:.4f} |')
lines += ['', '- Bootstrap intervals use 2,000 whole-pair resamples and seed 630700. They quantify seed variability conditional on the fixed sets and model, not matching or biological uncertainty. No neurons are counted as independent replicates.', '', '## Process code and evidence','',
'- The supervisor and collector finished independently of chat access. No extra trials, rematching, thresholds or model changes were introduced. Memory waits were permitted; the six-hour deadline was not reached.',
'- Created scripts/pcdr_verify_replication.py with Codex assistance by adapting the prior verifier to 210 trials, 180 pairs and this separate study. It checks every output hash and frozen seed/support/source, recomputes all six readouts and complete mean footprints, and exports all 180 per-seed records. The report uses manifest counts and does not relabel the five-seed result.',
'- Command: .venv/Scripts/python.exe scripts/pcdr_verify_replication.py. All assertions passed. No new significance test or simulation was run during verification.',
f'- Scheduled inputs match in all 180 pairs; delivered-input digests match in {delivered}/180. State-dependent delivery is distinct from the required matched schedule.',
'- Evidence directory: results/pcdr/seed_replication_20260921. See amendment.json, jobs.json, completion_audit.json, analysis/results.json, per_seed_readouts.csv and each trial manifest. Code and manifest hashes are in the completion audit. Prior study remains in optimized_pilot_20260921.',
'- Next: CCR environment and replay validation, then distributional/cell-class matching design before broader experiments. No unattended extension is queued. Completed handoff pauses this monitor.',
'', '## Every new paired seed','', '| Set | Seed | A single seed | F single seed | MN9 change Hz | Motor total change Hz |','|---|---:|---:|---:|---:|---:|']
for r in rows:lines.append(f'| {r["condition"]} | {r["seed"]} | {r["A_single_seed"]:.3f} | {r["F_single_seed"]:.4f} | {r["MN9_delta_hz"]:.1f} | {r["motor_total_delta_hz"]:.1f} |')
lines += ['', '- Single-seed A/F above are diagnostics. Declared aggregate A/F average signed neuronal changes across seeds before taking absolute values; do not replace them with the arithmetic mean of these columns.', '']
text='\n'.join(lines)
(S/'FINAL_HANDOFF.md').write_text(text,encoding='utf-8')
(ROOT/'docs/pcdr/SEED_REPLICATION_RESULTS_20260922.md').write_text(text,encoding='utf-8')
print(json.dumps({'mode_A':mode['A'],'mode_F':mode['F'],'MN9':mode['mn9_delta_hz'],'motor':mode['motor_total_delta_hz'],'delivered_equal':delivered,'others':[(r['A'],r['F']) for r in others]}))
