# Motor-composition pilot: all results

22 September 2026. Descriptive follow-up using all nine fixed motor-balanced comparison sets.

All 55 trials and 50 scheduled-input pairs passed independent verification. The ten complete 127,400-neuron mean footprints were recomputed from saved rates. Source and output hashes passed. No random-reference p-values were calculated.

The eigen-set had A = 22.603922 Hz and F = 0.232363. It exceeded 9/9 comparisons on A, 9/9 on F, and 9/9 on both. These are conditional descriptive orderings, not significance tests.

76.76 percent of the absolute mean response was outside the eigen-support. This is inconsistent with describing the support as dynamically independent merely because its response is more concentrated than some alternatives.

## Frozen question and comparison

The question was whether the prior response ordering persists against these nine motor-count-balanced optimized sets. Every set has 51 cells and 13 annotated motor cells, with exact sign/recruitment/motor counts and the original six pooled SMDs <=0.1. The target is the unchanged exploratory rank 33 support. No set was replaced after seeing an outcome.

The pre-lesion audit found incoming-degree variance up to 19.117 times the target and an ECDF gap up to 0.294118. All nine comparisons share 47 cells. MN9 is in the target and excluded from every comparison. Detailed cell types and some annotation availability differ. These facts prevent interpreting this as an isolated causal test of motor count, a representative random-control sample or confirmation of P over D/C/R.

Five fresh seeds 631201-631205 were run separately from earlier studies. The model, inputs, timestep, duration and output-only lesion semantics were unchanged. Thirty-minute local limit, one serial worker, memory/disk guards and no automatic extension were recorded before simulation.

## Every lesion set

| Set | A (Hz) | F | MN9 change (Hz) | Motor total change (Hz) |
|---|---:|---:|---:|---:|
| mode | 22.604 | 0.2324 | -81.8 | 20.0 |
| motor_003 | 12.059 | 0.1940 | 0.2 | -480.4 |
| motor_004 | 12.969 | 0.1985 | -3.2 | -503.2 |
| motor_005 | 12.722 | 0.1959 | -0.6 | -487.8 |
| motor_006 | 12.059 | 0.1940 | 0.2 | -480.4 |
| motor_007 | 12.969 | 0.1985 | -3.2 | -503.2 |
| motor_008 | 12.722 | 0.1959 | -0.6 | -487.8 |
| motor_009 | 12.059 | 0.1940 | 0.2 | -480.4 |
| motor_010 | 12.969 | 0.1985 | -3.2 | -503.2 |
| motor_011 | 12.722 | 0.1959 | -0.6 | -487.8 |

The reported A and F are computed after averaging each neuron's signed paired response over seeds and then taking absolute values. The arithmetic mean of single-seed A/F is not the declared outcome. Motor changes are simulated rates, not feeding behavior.

## Conditional paired-seed differences

Differences below are eigen-set minus comparison, each scored on its own support. Intervals use 2000 shared whole-seed bootstrap resamples, seed 631250. The same resampled seeds are used for each pair of conditions. They describe uncertainty from five stochastic input seeds conditional on these fixed sets. They do not cover uncertainty in the connectome, mode selection, matching or model assumptions, and are not multiplicity-adjusted confirmatory intervals.

| Comparison | A difference (Hz) | A 95% interval | F difference | F 95% interval |
|---|---:|---|---:|---|
| motor_003 | 10.545 | 9.431 to 11.486 | 0.0383 | 0.0294 to 0.0464 |
| motor_004 | 9.635 | 8.424 to 10.694 | 0.0339 | 0.0236 to 0.0427 |
| motor_005 | 9.882 | 8.690 to 10.929 | 0.0364 | 0.0287 to 0.0437 |
| motor_006 | 10.545 | 9.431 to 11.486 | 0.0383 | 0.0294 to 0.0464 |
| motor_007 | 9.635 | 8.424 to 10.694 | 0.0339 | 0.0236 to 0.0427 |
| motor_008 | 9.882 | 8.690 to 10.929 | 0.0364 | 0.0287 to 0.0437 |
| motor_009 | 10.545 | 9.431 to 11.486 | 0.0383 | 0.0294 to 0.0464 |
| motor_010 | 9.635 | 8.424 to 10.694 | 0.0339 | 0.0236 to 0.0427 |
| motor_011 | 9.882 | 8.690 to 10.929 | 0.0364 | 0.0287 to 0.0437 |

Per-set intervals, all 50 per-seed readouts and all ten sets are preserved in the evidence snapshot. No favorable set subset was selected. Paired-seed intervals do not make the nine largely overlapping sets independent.

## Repeated responses checked after completion

The nine distinct membership sets produced only 3 distinct five-seed spike trajectories. This was noticed in the completed result table, so a separate post-result diagnostic was recorded before checking the full outputs. Within each group, every spike event and all 127,400 per-neuron rates were exactly equal for every seed. This is stronger than merely equal A and F.

The repeated groups were motor_003/006/009, motor_004/007/010 and motor_005/008/011. Each group shared 49 cells. Four cells varied in membership across the group, and all four had zero spikes in all five baselines and all corresponding lesion conditions. Their recorded IDs and all inspected rates are saved in response_duplicates/varying_cell_rates.csv.

This means part of the apparent set diversity consisted of substitutions among cells that were silent in these runs. It does not prove they stay silent in new seeds or another input/model condition. Keep all nine completed results in the record; do not count them as nine independent perturbation responses or reinterpret the three patterns as independent biological replicates.

## What this changes and what remains

This adds an actual lesion comparison after matching feasibility and distribution checks. It tests the ordering against fixed alternatives with matching motor counts. It does not establish that motor composition caused any difference from the earlier pilot, because the individual neurons and other distributional properties changed too.

The next design problem is comparison quality and diversity. A prospective design could constrain distributional differences and deliberately seek more distinct eligible sets, then test its feasibility before new lesions. Neither a new numerical balance cutoff nor a different eigen-support should be chosen to improve these completed outcomes. The historical 199-control confirmation still lacks a justified reference-sampling design.

## Code, checks and evidence

Created scripts/pcdr_motor_set_audit.py, pcdr_motor_composition_pilot.py, pcdr_verify_motor_pilot.py, pcdr_motor_response_duplicates.py, pcdr_publish_evidence.py and pcdr_motor_pilot_report.py with Codex assistance. Function explanations are separate in CODE_GUIDE.md. The source model and existing simulator were not changed.

The verifier rereads every saved trial, checks all output hashes, membership IDs, seeds, provenance and model parameters, verifies paired scheduled inputs, then recomputes all ten full footprints and A/F/MN9/motor summaries. The added contrast calculation uses common seed weights before taking absolute responses. Known-answer tests check identical paired contrasts, a constant-response example and undefined concentration for zero response.

Delivered-input digests match in 49/50 pairs. Scheduled-input identity is required; delivered events can differ with network state. Every scheduled pair matched.

Before launch: 31 focused tests passed. For the repository commit: 224 tests passed, 3 skipped, 40 warnings. These are software checks, not biological validation. Verification of the completed study is separate from the unit tests.

Commands: .venv/Scripts/python.exe scripts/pcdr_motor_set_audit.py; scripts/pcdr_motor_composition_pilot.py --prepare; scripts/pcdr_motor_composition_pilot.py; scripts/pcdr_verify_motor_pilot.py; scripts/pcdr_publish_evidence.py; scripts/pcdr_motor_pilot_report.py.

Full local evidence: results/pcdr/motor_composition_pilot_20260922. Compact committed evidence: docs/pcdr/evidence/2026-09-22, with original-source hashes. Trial spikes, delivered/scheduled input tapes, rate tables and source archives remain local. Earlier studies and PDFs remain unchanged.

The distributional objection and supporting literature are recorded in MOTOR_SET_AUDIT_20260922.md. The feasibility method is in FULLPOOL_FEASIBILITY_20260922.md. This report is research support prepared with Codex assistance, not a student-authored STS submission.
