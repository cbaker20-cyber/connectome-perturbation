# Matching feasibility audit 21 September 2026

## Result and interpretation

- Suitable matched sets exist for the selected 51-cell support. Five distinct sets pass every original size, sign, recruitment, exclusion and SMD requirement. The largest SMD across these examples is 0.07335, below the fixed 0.1 threshold.
- The original nearest-neighbor sampler failed to find them. Incoming synaptic strength failed in all 50,000 replayed proposals. Its smallest SMD was 0.73227; its median was 1.22764. For 859 proposals it was the only failing feature. Baseline firing passed in every proposal.
- In the best rejected proposal, the mean log1p incoming strength was 7.91118, compared with 8.28207 in the target. The failure is a deficit in this proposal. The audit saved absolute SMDs for all proposals, so this direction is not asserted for every proposal.
- This diagnoses failure of the tested sampler, not failure of the eigencircuit hypothesis. There are still no eigen-set lesion results. Optimized examples establish feasibility; they do not define an exchangeable or uniformly sampled null.

## Checks before interpreting the failure

- Verified hashes against the failed run, unique string root IDs, unchanged target IDs and finite nonnegative matching features. No lesion outcome files were read by the audit or optimizer.
- Required silent E, active E, silent I and active I counts were 9, 17, 13 and 12. Available counts were 86,327, 169, 40,258 and 189. The pool excludes the support and the 21 sugar inputs.
- Calculated exact smallest and largest possible means for each feature separately under those counts. Every target mean lay inside its interval. These marginal checks alone cannot establish simultaneous balance.
- Replayed the original 50,000 proposals with seed 630600. The only inserted operation records SMDs before rejection; it consumes no random numbers. Saved the instrumented function and every proposal balance. The original 0/5 outcome and attempt count reproduced.

## Failure counts in the replay

| Feature | Failed of 50000 | Median SMD | Smallest SMD |
|---|---:|---:|---:|
| in_degree | 31385 | 0.13529 | 0.0000123 |
| out_degree | 48218 | 0.26565 | 0.0004013 |
| in_strength | 50000 | 1.22764 | 0.7322711 |
| out_strength | 32433 | 0.12575 | 0.0000006 |
| baseline_hz | 0 | 0.03177 | 0.0000001 |
| strong_out_mass | 16856 | 0.07420 | 0.0000031 |

## Why use an integer selection check

- The original sampler picks nearby cells one at a time. Individual proximity does not guarantee balanced averages for the complete 51-cell set. A joint selection check directly enforces the set-level constraints.
- Used only the union of the original nearest-64 candidate lists: 1,099 cells. This removes the per-target assignment restriction while keeping the scientific set-level requirements. It is an algorithm change, recorded before the solver ran.
- Each candidate has a binary variable: 1 includes the cell, 0 excludes it. Four equality constraints enforce the exact sign/recruitment counts. Six pairs of inequalities bound the transformed feature means.
- Let vT be target population variance of a log1p feature. Required |meanC - meanT| <= 0.099 sqrt(vT/2). Since the original SMD denominator is sqrt((vT + vC)/2) and vC is nonnegative, this sufficient constraint guarantees SMD <= 0.099. The tighter 0.099 gives numerical margin; it does not relax 0.1.
- Example: if vT = 2, an allowed mean difference is 0.099. If vC = 2 as well, its SMD is 0.099/sqrt(2), approximately 0.070. The actual saved sets were checked with their own variances.
- Five fixed random linear objectives used seed 630610. Previously found entire sets were excluded by a constraint allowing at most 50 of their 51 cells. Each solve had a 30-second cap. All five completed successfully. Overlap is allowed by the original design: pairs share 31–37 cells, with Jaccard 0.437–0.569.
- A separate validator recomputed balance from saved IDs, checked exact counts, exclusions, uniqueness and finite SMDs. It did not rely on the optimizer status or call the original SMD function.
- Zubizarreta, Paredes and Rosenbaum (2014), Matching for balance, pairing for heterogeneity, motivates selecting units subject to explicit balance constraints. This fixed-size feasibility program is not a reproduction of their maximum-cardinality design. Source checked 21 September 2026: https://arxiv.org/abs/1404.3584 ; doi:10.1214/13-AOAS713.

## What changes next and what stays unresolved

- Keep the scientific question, support, features and 0.1 limit. The evidence supports changing the selection algorithm rather than loosening balance.
- Recommended next simulation is a separately amended, descriptive pilot using frozen optimized comparison sets and the five unused paired seeds 630901–630905. Compare A, F, MN9 and motor changes; show every set and seed. These five hand-designed comparisons would not supply a calibrated Monte Carlo p-value.
- Before that pilot, freeze the exact algorithm, objectives, IDs, output hashes, readouts and stopping rules. Call it an optimized matched-comparison pilot, not the original random-control confirmation. No new lesion run was launched in this audit.
- A confirmatory reference distribution still needs a defensible sampling scheme and inferential justification. More optimized sets alone do not fix exchangeability. Mean balance also does not guarantee distributional balance or removal of unmeasured structural differences.
- Did not expand eigenpairs, swap the mode, relax matching, rerun baselines, inspect hypothetical lesion effects or resume the paused monitor. These steps were unnecessary for this baseline-only feasibility question.

## Code guide commands and creation record

- New scripts were created with Codex assistance on 21 September 2026. The student must review the code and write their own research report; this record does not claim student authorship of assisted code.
- scripts/pcdr_matching_audit.py: reads frozen feature and selection tables; mean_bounds sorts candidates within each stratum to calculate coordinatewise extrema; instrumented_sampler adds a logging callback to the unchanged sampler; main writes the protocol before data analysis, then saves capacity, bounds, proposal SMDs and the best rejected set.
- scripts/pcdr_matching_witness.py: writes its method before solving; builds the binary selection problem; runs five bounded solves; validates and saves feasibility examples, balances and overlap. It creates no simulation jobs.
- scripts/pcdr_matching_report.py: independently verifies saved witnesses, computes the best proposal mean direction and creates this report.
- tests/test_pcdr_matching_audit.py: compares bounds with exhaustive enumeration on a small example and checks that logging leaves a seeded sampler unchanged. Command: .venv/Scripts/python.exe -m pytest tests/test_pcdr_matching_audit.py -q --disable-warnings. Result: 2 passed in 0.61 seconds.
- Commands, in order: .venv/Scripts/python.exe scripts/pcdr_matching_audit.py ; .venv/Scripts/python.exe scripts/pcdr_matching_witness.py ; .venv/Scripts/python.exe scripts/pcdr_matching_report.py. OMP_NUM_THREADS=1 and OPENBLAS_NUM_THREADS=1 were set for the audit and solver. No Brian2 simulation was started.
- Evidence directory: results/pcdr/matching_audit_20260921. protocol.json records the initial scope and hashes; witness/protocol.json records the optimization amendment. proposal_smd.parquet preserves all rejected balances; witness/members.parquet preserves all witness IDs; independent_validation.json records the independent checks. summary.json files contain timestamps, solver statuses and hashes.
- The original failed controls directory and all prior exports remain unchanged. New outputs refuse to overwrite an existing audit or witness directory.
