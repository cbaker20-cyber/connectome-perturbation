"""Verify every completed optimized-pilot trial and recompute all readouts."""
from pathlib import Path
import sys,json
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from eigencircuits.common import now,sha256,atomic_json,MN9
S=ROOT/'results/pcdr/optimized_pilot_20260921'
plan=json.loads((S/'jobs.json').read_text());summary=json.loads((S/'summary.json').read_text())
assert len(plan['jobs'])==35 and summary['primary']==[] and summary['status']=='complete'
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
audit={'checked_utc':now(),'trials_verified':35,'paired_inputs_verified':30,'delivered_input_pairs_equal':delivered,
       'lesion_summaries_verified':6,'checks':checks,'reference_p_values':'absent','source_manifests':sources,
       'command':'.venv/Scripts/python.exe scripts/pcdr_verify_optimized.py','code_sha256':sha256(__file__)}
atomic_json(S/'completion_audit.json',audit)
mode=next(r for r in results if r['condition']=='mode');others=[r for r in results if r['condition']!='mode']
lines=['# Completed optimized comparison pilot 21 September 2026','','## Findings and scope','',
 '- All 35 frozen trials completed at 20:07:50 UTC. The independent verifier checked all trial output hashes, 30 baseline/lesion input pairings, six summaries and all six 127,400-neuron footprints.',
 f'- The eigen-set had A = {mode["A"]:.3f} Hz and F = {mode["F"]:.4f}. Both exceed all five optimized comparisons in this pilot. This is descriptive support for the predicted ordering in this selected mode and model context, not confirmation or a calibrated significance result.',
 f'- Only {100*mode["F"]:.2f}% of the absolute mean response lay inside the eigen-set; {100*(1-mode["F"]):.2f}% lay outside. A higher concentration than these comparisons does not establish dynamical independence.',
 '- MN9 changed by -82.2 Hz while total motor firing changed by +27.6 Hz (+0.325 Hz per motor cell). The five comparisons had smaller MN9 reductions but larger total motor reductions. These secondary patterns are model readouts, not feeding behavior.',
 '- MN9 itself is in the eigen-set and excluded from every comparison set by the focal-support exclusion rule. Therefore MN9 membership is not balanced. The MN9 contrast cannot establish a special downstream pathway effect. Output-only silencing removes outgoing weights, not the neuron’s incoming drive; rate changes still arise through network dynamics.',
 '- The eigen-set contains 13 annotated motor cells; the five comparisons contain 5, 4, 3, 3 and 4. Motor-class membership was not matched, so secondary motor contrasts also require this qualification.',
 '- Five comparison sets were optimized from baseline features and share 31–37 cells with one another. The mode was selected in an exploratory expanded search. Five seeds measure limited simulation variability; they are not five animals. No random-reference p-values or new significance tests were computed.',
 '', '## All six lesion results','',
 '| Set | A Hz | F | MN9 change Hz | Motor total change Hz | Motor mean change Hz |','|---|---:|---:|---:|---:|---:|']
for r in results:lines.append(f'| {r["condition"]} | {r["A"]:.3f} | {r["F"]:.4f} | {r["mn9_delta_hz"]:.1f} | {r["motor_total_delta_hz"]:.1f} | {r["motor_mean_delta_hz"]:.3f} |')
lines+=['','## Seed uncertainty and footprint interpretation','',
 '| Set | A bootstrap 95 percent interval | F bootstrap 95 percent interval | Off support absolute sum Hz |','|---|---|---|---:|']
for r in results:
    a=r['interval']['A_95pct'];f=r['interval']['F_95pct']
    lines.append(f'| {r["condition"]} | {a[0]:.3f} to {a[1]:.3f} | {f[0]:.4f} to {f[1]:.4f} | {r["off_absolute_sum_hz"]:.1f} |')
lines+=['','- Intervals use 2,000 paired-seed bootstrap resamples, seed 630700. They describe seed variation conditional on these fixed sets and the model; they do not cover uncertainty in mode selection, matching, anatomy or model assumptions.',
 '- Aggregate A and F are computed after averaging signed neuron changes across seeds. The single-seed A and F below are descriptive diagnostics; their arithmetic averages are not substitutes for the declared aggregate estimands.',
 '', '## Every paired seed','',
 '| Set | Seed | A single seed | F single seed | MN9 change Hz | Motor total change Hz |','|---|---:|---:|---:|---:|---:|']
for r in rows:lines.append(f'| {r["condition"]} | {r["seed"]} | {r["A_single_seed"]:.3f} | {r["F_single_seed"]:.4f} | {r["MN9_delta_hz"]:.1f} | {r["motor_total_delta_hz"]:.1f} |')
lines+=['','## Verification process code and next step','',
 '- The queue ran serially from 19:57:10 to 20:07:50 UTC, about 10 minutes 40 seconds including collection. No scientific code, thresholds, seeds or comparison IDs were changed after launch. The original deadline was not reached.',
 f'- All 30 scheduled-input digests matched their baselines. Delivered-input digests matched in {delivered}/30 pairs; the scheduled input is the pairing requirement, while delivered events can depend on neuronal refractoriness.',
 '- New verification code: scripts/pcdr_verify_optimized.py, created with Codex assistance on 21 September. It reads frozen jobs and completed trial manifests; checks hashes, supports, seeds and provenance; reconstructs paired rate differences; recomputes A, F, MN9 and motor readouts; compares every footprint with those calculations; and saves the per-seed table and completion audit. It does not simulate or change data.',
 '- Command: .venv/Scripts/python.exe scripts/pcdr_verify_optimized.py. All assertions passed. Did not rerun simulations or introduce post-outcome inferential tests. The frozen model was unchanged; full-array readout comparisons were the relevant completion check.',
 '- Evidence: results/pcdr/optimized_pilot_20260921/amendment.json, jobs.json, analysis/results.json, per_seed_readouts.csv and completion_audit.json. Each trial directory retains spikes, rates, input records and its manifest. The audit records the exact command, code hash and source manifest hashes.',
 '- Recommended next work: an adviser review of the exploratory result and reference-sampling design before confirmation. Check distributional balance and readout membership as design diagnostics. More seeds alone would not make the optimized sets a random null. Any MN9-membership sensitivity would need a separately stated question and amendment, not a revision of this completed result.',
 '- Finished: original single-cell study, matching feasibility audit and this 35-trial descriptive pilot. Pending: justified confirmatory reference sampling, the 199-control/30-seed study, and declared sensitivity/context extensions. No extra computational stage was started. Pause the monitor after the completed handoff.', '']
text='\n'.join(lines)
(S/'FINAL_HANDOFF.md').write_text(text,encoding='utf-8')
(ROOT/'docs/pcdr/OPTIMIZED_PILOT_RESULTS_20260921.md').write_text(text,encoding='utf-8')
print(json.dumps({'verified':35,'pairings':30,'delivered_equal':delivered,'membership':checks,'mode_A':mode['A'],'mode_F':mode['F']}))
