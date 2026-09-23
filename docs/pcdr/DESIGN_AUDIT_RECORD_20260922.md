# Composition audit and CCR preparation

## Current research status

Recorded 22 September 2026. This chapter adds the work completed after Chapter 12. Earlier chapters retain the literature, original plan, eigencircuit mathematics, code guide, notebook and every reported simulation result. The five-seed pilot and separate 30-seed replication remain distinct studies.

The replication reproduced the predicted A and F ordering against the five fixed optimized comparisons. It did not establish a calibrated random-reference result. The next useful work concerns comparison design and reproducible cluster execution; more trials of the same sets would not repair their composition or sampling limitations.

No scientific question, lesion support, simulation code, threshold or seed was changed in this audit. No new simulation was launched. The original first-20 selection failure remains part of the record. Confirmation is still pending because the optimized comparison procedure does not define the originally proposed random reference distribution.

## Notes on the baseline audit


- This audit uses baseline features and frozen lesion IDs only. It describes differences that the original mean-balance rules did not constrain. No new simulations or p-values.
- Largest empirical cumulative-distribution gap: 0.275, for optimized_003, in_degree. A gap is a descriptive maximum difference in cumulative proportions, not a significance result.
- The motor label comes from available annotations. Missing annotations remain unavailable; non-motor here includes unavailable classifications and must not be interpreted as a verified biological identity.

| Sign | Recruited | Annotated motor | Needed | Available outside support and inputs |
|---|---|---|---:|---:|
| excitatory | False | False | 7 | 86275 |
| excitatory | False | True | 2 | 52 |
| excitatory | True | False | 9 | 161 |
| excitatory | True | True | 8 | 8 |
| inhibitory | False | False | 13 | 40250 |
| inhibitory | True | False | 9 | 185 |
| inhibitory | True | True | 3 | 4 |

- Every exact motor/sign/recruitment stratum has enough candidates: True. This does not establish simultaneous continuous-feature feasibility.
- Next design step is a separately declared joint matching feasibility check with motor counts added, preserving the original six feature limits. If capacity fails, report it rather than silently merging strata. MN9 membership cannot be exactly matched while the whole focal support is excluded; its secondary interpretation remains limited.
- Code created with Codex assistance: scripts/pcdr_composition_audit.py. ecdf_gap sorts both samples, evaluates cumulative fractions at every unique observed value and returns the largest absolute gap. Main writes a protocol before analysis, then saves all feature quantiles/variances and class counts.
- Evidence: results/pcdr/composition_audit_20260922/protocol.json, distributions.csv, composition.csv, motor_strata_capacity.csv and summary.json. Command: .venv/Scripts/python.exe scripts/pcdr_composition_audit.py. No new distributional acceptance cutoff was chosen from these results.

- The active excitatory motor stratum needs 8 cells and has exactly 8 eligible candidates: all 8 would be mandatory in every exact composition-matched set. Active inhibitory motor counts require 3 of 4. This constrains diversity even though all individual capacities pass. The largest-gap example also has incoming-degree variance ratio 4.092 on log1p values while SMD is 0.042. Do not interpret passing mean balance as matching the entire distribution.

## Bounded joint feasibility check

- Ran .venv/Scripts/python.exe scripts/pcdr_motor_matching_witness.py after the capacity audit. Separate protocol was written before solving. It reuses the baseline-only binary optimizer, rebuilds nearest 64 neighbors within sign/recruitment/motor strata, and retains the conservative 0.099 sqrt(target variance/2) mean bounds. Seed 631100; at most 5 solves, 30 seconds each.
- First solve returned infeasible, so the declared rule stopped subsequent solves. No candidate control sets or lesions resulted. This certifies infeasibility only of this restricted candidate pool with stricter sufficient mean bounds. It does not prove infeasibility under the original pooled-SMD<=0.1 criterion or the full pool.
- Next justified check: full-pool feasibility or direct original-SMD constraints, with method and budget fixed before execution. Do not infer that motor composition explains the effect, relax thresholds, or substitute a mode. Evidence: results/pcdr/composition_audit_20260922/motor_witness/protocol.json and summary.json. Code created with Codex assistance; simulation files unchanged.

## What the matching failure means

- The restricted pool contained 1,125 candidates. The first solver returned status 2 (HiGHS infeasible); zero witnesses were saved. The protocol stopped further attempts at that point.
- The summary JSON contains a generic claim field beginning "Feasible examples". That is inherited template wording, not a result: witness_count is zero and the solver record is infeasible. The saved evidence is preserved; this clarification prevents a reader from mistaking the template for a successful match.
- The conservative bound is a sufficient condition, not the original full feasible region. For transformed feature x with target variance vT, the optimizer requires absolute mean difference no greater than 0.099 times sqrt(vT/2). Because the comparison variance is nonnegative, this is sufficient for pooled SMD below 0.1. It may reject sets that would pass the original SMD rule.
- Searching the full pool or enforcing the original criterion directly remains a future, separately documented design step. No additional matching was run during this document update.

## Separate code guide: new functions and scripts

- pcdr_composition_audit.py: reads frozen baseline features and lesion IDs. Its ecdf_gap function sorts two arrays, evaluates their empirical cumulative fractions at every distinct pooled value and returns the largest absolute difference. For [1, 2] versus [2, 3], the gap is 0.5. The main analysis writes feature distributions, annotation counts, capacity counts and a summary. It does not read lesion effects to choose new acceptance limits.
- pcdr_motor_matching_witness.py: builds candidate neighborhoods within sign, recruitment and annotated motor strata, then uses binary selection variables. A selected cell contributes one to the set; exact stratum totals prevent duplicates and preserve composition. Linear feature-sum bounds enforce the conservative mean criterion. A feasible solution would be an example, not a random draw. The first attempted solve was infeasible.
- pcdr_backend_input_check.py: check(directory) reads NumPy and Cython trial manifests for 30 baseline/lesion seed pairs per backend. It checks completion and equality of seed, scheduled-input digest, input protocol, duration, timestep, frequency, context, lesion IDs and model variant. It returns a check record or raises an error. Identical event counts alone can hide different event times; a digest check addresses that problem. State-dependent delivered events are not required to match.
- Small worked example for mean balance: [0, 2] and [1, 1] have the same mean, so the mean difference is zero, but their spreads differ. This explains why a small SMD does not establish matching of the whole distribution. The real audit also saves quartiles and variance ratios.
- New code was created with Codex assistance. The purpose of these scripts is analysis and deployment validation. None modifies the frozen LIF simulation.

## Commands, verification and skipped work

All commands below were run from C:/Users/Baker/Drosophila_Data during the recorded audit, before this document export.

- .venv/Scripts/python.exe scripts/pcdr_composition_audit.py
- .venv/Scripts/python.exe scripts/pcdr_motor_matching_witness.py
- .venv/Scripts/python.exe -m pytest tests/test_pcdr_backend_input_check.py tests/test_pcdr_composition.py -q --disable-warnings
- Result: two tests passed in 0.83 seconds. The ECDF tests cover ordering, ties and separated samples. The backend test accepts 60 synthetic manifest pairs, then rejects an altered schedule digest.
- The simulator suite was not repeated: this stage changed analysis and a read-only guard, not simulation sources. Actual backend equivalence was not tested; synthetic manifests validate only the guard's logic.
- No cluster job was submitted because account, environment and scheduler details have not been established. No new lesion stage followed the matching failure because no acceptable composition-matched set was obtained under that restricted attempt.
- No p-values were added. There is no calibrated random-reference ensemble for these optimized comparisons, and an ECDF gap is being used descriptively.

## Evidence and provenance

- Baseline features: results/pcdr/corrected_20260919/analysis/features.parquet. Frozen set IDs: results/pcdr/optimized_pilot_20260921/jobs.json.
- Audit records: results/pcdr/composition_audit_20260922/protocol.json, distributions.csv, composition.csv, motor_strata_capacity.csv, summary.json, verification.json and completion_record.json.
- Matching records: results/pcdr/composition_audit_20260922/motor_witness/protocol.json, progress.json, summary.json and members.parquet. The member file is empty because no witness was accepted.
- verification.json records the test command and code hashes. This edition's source_manifest.json records the exact source documents, scripts and evidence incorporated into the export. Previous editions remain preserved.

## CCR readiness


Recorded 22 September 2026. This is a launch checklist, not evidence that CCR has been tested.

1. Obtain actual account, partition, project directory, Python/module environment and node limits. No credential should be stored in a report or repository. No CCR connection or submission has occurred in this continuation.
2. Copy the frozen input/source bundle, verify hashes and recreate the recorded package versions. Keep local historical files unchanged. The existing worker rejects changed sources or packages; prepare a new cluster manifest after documenting any environment amendment, rather than editing an existing manifest to bypass this check.
3. Run one NumPy baseline, its identical-seed replay, a no-input trial and an output-only lesion. Verify scheduled-input equality, deterministic replay, zero undriven spikes, all-neuron outputs and lesion support. Measure construction plus simulation plus output time, peak memory and bytes per trial. Account/partition and resource requests remain unresolved until access exists.
4. Use NumPy by default. For a proposed Cython switch, run the existing full benchmark, then require both benchmark.json passed=true and `python scripts/pcdr_backend_input_check.py --benchmark PATH` to pass. The new read-only check verifies exact input schedule identity across all 60 baseline/lesion backend pairs; equal input counts alone are insufficient. Do not claim backend readiness from the unit test or an unrun certificate. Delivered input events may differ with state and are not required to match.
5. Before a large array, test a small array, a failed/missing job and resume/collection. Each array index owns one frozen condition/seed; no nested parallelism. Keep unique directories and locks. Reject partial confirmation summaries. Set concurrency from measured memory and actual allocation rather than the template example.
6. Freeze the scientific comparison design separately from technical deployment. Existing optimized controls do not justify the original random-reference p-value. More seeds or sets cannot fix this by themselves. The next baseline-only gate is joint motor/sign/recruitment plus continuous-feature feasibility.

## New check and validation

- scripts/pcdr_backend_input_check.py was created with Codex assistance. It reads benchmark manifests, checks completed status and equal seed, schedule digest, drive, duration, timestep, support and model variant across NumPy/Cython, and returns a machine-readable list or an error. It modifies no benchmark or simulation files.
- Test: tests/test_pcdr_backend_input_check.py constructs all 60 synthetic pairs, verifies acceptance, then alters one schedule digest and requires rejection. This validates the guard, not real backend equivalence.
- Current scripts/pcdr_array.sh remains a submission template. Cluster account/partition, transfer/environment setup, integration of certificates into automated dispatch and scheduler fault tests are still pending. No automatic large dispatch is enabled by this checklist.

## Four-week work sequence

The following is a roadmap, not a record of completed runs or permission to change frozen protocols. The overnight replication named in the earlier roadmap is now complete.

## Week one September 22 to 28

- Prepare CCR package with frozen source/data hashes, actual working environment, explicit entrypoints and resource estimates. Keep NumPy initially. Fill account/partition/project and environment paths only from actual CCR access.
- Exercise local preflight, duplicate locks, corrupted/missing trial rejection, resume and collection without changing frozen model files. Add cross-backend scheduled-input identity and lesion-semantic checks before the existing backend equivalence benchmark. Existing aggregate equivalence margins remain numerical tolerances, not biological validation.
- On CCR: one baseline, identical-seed replay, no-input trial and one lesion before an array; measure full wall time, peak memory and disk. Derive requests from measurements with a safety margin. A backend failure retains NumPy.
- Decide and write the next comparison design using baseline-only information. Optimized set ensembles may support conditional descriptive comparisons; increasing their count does not create a randomization test. Do not launch the historical 199-set confirmation under an unjustified null.

## Week two September 29 to October 5

- Run the frozen revised comparisons after feasibility and technical checks. Preserve the existing mode and publish all results. Consider all other three baseline-eligible modes together, subject to unchanged recruitment and matching feasibility; their large supports can make matching impossible. Report such failures without substituting favorable modes.
- Separate outcomes conditional on chosen sets from claims about eigencircuits generally. Share a concise design/results memo with the adviser via the student; no automatic external messages.

## Week three October 6 to 12

- Prioritize sensitivities that can change interpretation: motor/composition matching, baseline recruitment dependence, then fixed-support strong-edge and model-parameter variants. Every changed network gets a matched own-network baseline.
- Keep original supports during pruning. Recomputed supports answer a different structural question. Global suppression does not alone establish the strong-connection account. Do not expand to JO until core design and analysis are stable.

## Week four October 13 to 19

- Reproduce final tables/figures from frozen manifests, audit all claims and failure records, and prepare the student-facing explanation of what the data do and do not establish.
- Reserve time for the student's independent report writing and understanding of eigenvectors, simulation, controls, estimands and uncertainty. Quality, originality and defensibility matter more than run count. A top-40 outcome cannot be guaranteed.
- STS 2027 deadline checked: November 5, 2026 at8PM ET; retain the post-testing period for writing/application work. Source: https://www.societyforscience.org/regeneron-sts/application-requirements/ . Its holistic application includes original independent research and support disclosures.


## Notes on this research record update

- Combined the audit, restricted feasibility result, code purposes, exact commands, testing limits and CCR gates into this chapter. Reworded crowded shorthand for readability without changing results.
- Preserved Chapters 1 to 12 and previous exports. Updated the cover to direct readers to this chapter. Document preparation used Codex assistance; this record supports the student's own understanding and report writing.
- This export adds documentation only. Full-pool matching, actual backend benchmarks, cluster setup and new scientific comparisons remain pending.
