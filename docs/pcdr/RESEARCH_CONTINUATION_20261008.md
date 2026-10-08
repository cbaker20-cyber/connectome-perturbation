# Returning to the eigencircuit question — 8 October

Subsequent work: the proposed [bounded distribution-matching study](DISTRIBUTION_MATCHING_20261008.md) has now completed. The proposal below records the earlier decision; use the linked results for current status.

Three local analyses are complete. The selected group's response ordering persists across the four tested fine steps and all 30 paired seeds against the existing three comparisons. Those comparisons share 50 of 51 cells. A new baseline-only search found twelve valid comparison sets with substantially less overlap with the old family, but considerable internal overlap and distributional imbalance remain. No new CCR simulation or upload was created.

The original question is still whether concentrated eigenvector support predicts localized outgoing-lesion responses beyond degree/strength, strong connections and recruitment. The [separate G/H intervention](SEPARATE_PATHWAY_RESULTS_20261008.md) answered a selected burst-mechanism question; it did not answer this predictive question. The work below returns to that distinction.

## 1. Does the existing response ordering survive finer steps?

Used the previously verified default-network tables for 30 seeds, four lesion conditions and steps 0.0008, 0.0004, 0.0002 and 0.0001 ms. Input hashes match the completed raw-spike review. This analysis consumes those checked summaries; it does not rerun that full 620-trial verification or claim an independent simulator implementation.

Primary aggregate A and F remain summaries of the signed response averaged over seeds before taking absolute values. Per-seed contrasts are reported separately. Each comparison uses the same seed and same step, preserving the shared baseline. Every declared seed, comparison and step is retained. These are retrospective descriptions without new acceptance thresholds or p-values.

| Quantity | Observed result |
|---|---|
| Same-step A ordering | Mode exceeds comparison in all 360 contrasts: 30 seeds × 3 comparisons × 4 steps |
| Same-step F ordering | Mode exceeds comparison in all 360 contrasts |
| Smallest individual A gap | 4.510 Hz |
| Smallest individual F gap | 0.610 percentage points |
| Aggregate A gaps across the 12 step/comparison combinations | 9.790–10.418 Hz |
| Aggregate F gaps across those combinations | 3.122–3.496 percentage points |

The counts of 360 are not independent trials: the same 30 seeds, baselines, memberships and neighboring steps are reused. The three comparison sets are also highly overlapping. These results establish a persistent descriptive ordering against those fixed alternatives, not significance against a sampled reference distribution.

A deliberately stricter description compares the minimum mode value across the four steps with the maximum comparison value across the four steps, within each seed. All 90 A margins are positive. For F, 89 of 90 are positive. The exception is seed 631407 versus motor_004: mode F at 0.0008 ms is 0.2259875, while comparison F at 0.0004 ms is 0.2271925, a difference of −0.1205 percentage points. This crosses different resolutions; the matched-step ordering never reverses. It must not be hidden behind a claim that every possible cross-step contrast is positive.

For aggregate mean responses, even the minimum-across-steps mode exceeds each maximum-across-steps comparison. The smallest such margins are 9.697 Hz for A and 3.046 percentage points for F. This envelope covers only the observed steps; it neither bounds error to a continuous-time solution nor predicts smaller untested steps.

At the final halving, median absolute changes in paired A contrasts are 1.049–1.216 Hz, and in paired F contrasts 0.440–0.875 percentage points. The largest individual F-contrast change is 2.522 percentage points. Thus the direction persists while some individual magnitudes change substantially. No adjacent-step strict sign reversals or tie transitions occur for the primary contrasts.

Secondary common-support calculations score every lesion response on the same original 51-cell mode support. Their aggregate mode-minus-comparison gaps are 12.161–12.569 Hz and 6.682–6.994 percentage points. This addresses readout location but does not equalize the lesion memberships or solve confounding. It does not replace the original own-support readouts.

All 18 original full agreement groups still fail. No rule was changed, and no convergence claim follows from the contrast ordering. Evidence: [aggregate contrasts](evidence/2026-10-08/fine_contrasts/aggregate_contrasts.csv), [every paired contrast](evidence/2026-10-08/fine_contrasts/paired_contrasts.csv), [step envelopes](evidence/2026-10-08/fine_contrasts/step_envelopes.csv), [contrast changes](evidence/2026-10-08/fine_contrasts/contrast_changes.csv), [provenance](evidence/2026-10-08/fine_contrasts/complete.json).

## 2. Is extreme comparison overlap forced by the membership counts?

Verified that the fine-study memberships are unchanged across all steps and seeds. Each is disjoint from the mode; every pair of the three comparisons shares 50 cells. Revisited the original baseline feature table and exclusions without reading lesion outcomes for the new membership calculation.

For a stratum containing N eligible cells, a set requiring k cells must share at least max(0,2k−N) cells with another set with the same required count. Against an existing reference containing r eligible cells in that stratum, the bound is max(0,k−(N−r)). These bounds ignore feature balance and are attained for the count constraints alone.

The existing eligible pool has 126,935 cells. Eight recruited excitatory motor cells are available and eight are required, so all eight are forced. Four recruited inhibitory motor cells are available and three are required, forcing at least two shared cells between any two matched sets. The other five strata add no forced overlap. The resulting lower bound is **10 shared cells**, not 50.

This is a count-only bound. The six feature-balance constraints may force more overlap; the result does not show that fully balanced sets can reach ten. It does show that exact composition counts alone cannot explain the observed 50-cell overlap. Evidence: [declared count analysis](evidence/2026-10-08/comparison_capacity/protocol.json), [stratum counts and exact forced IDs](evidence/2026-10-08/comparison_capacity/complete.json). An exhaustive small-subset test verifies both bound formulas, including empty strata.

## 3. Can the original mean-balance rule admit a different comparison family?

Recorded a new baseline-only search protocol before execution. The objective minimizes fractional membership in the union of the three old comparisons. Retained the original 51-cell target, exclusions, exact sign/recruitment/motor counts and conservative sufficient mean constraints for the six log1p features. The old baseline features and recruitment labels remain frozen; this does not establish matching of recruitment measured anew at the finest step.

Budget: one linear program, 60 seconds internal and 90 seconds external including enumeration; no automatic retry. Fractional membership is a computational intermediate, never a neuronal intervention. The solver returned nine fractional entries. Enumerated all 512 completions, retaining all twelve sets that met the exact counts and the original pooled population-variance SMD ≤0.1 rule. Twenty-four completions met the counts. No threshold was relaxed and no lesion outcome entered the objective or acceptance.

The worker finished successfully in 4.75 seconds including loading, optimization and enumeration. Its fractional constraints passed independent residual checks. The retained warning says the installed SciPy passes `threads=1` to HiGHS; single-thread environment limits were also set. Actual environment and process records are retained.

An independent verifier reread features and exact string IDs, checked all frozen input/output hashes, exclusions, 51 unique members, stratum counts, distinctness, balance and overlap. It recalculated SMD without the search's shared SMD helper. All twelve pass, with largest SMDs ranging from 0.06768 to 0.09547. They share 20–22 cells with the union of the old comparisons. This establishes feasible comparisons well outside the previously tested family under the original mean-balance rule.

However, the new twelve share 47 cells with each other; pairwise overlaps are 48–50. They are another closely related optimized family, not twelve independent references. Distributional checks also show:

| Feature, log1p scale | Candidate/target variance-ratio range | Largest empirical CDF gap |
|---|---:|---:|
| Incoming degree | 6.895–7.182 | 0.353 |
| Outgoing degree | 3.241–3.340 | 0.255 |
| Incoming strength | 2.899–3.018 | 0.255 |
| Outgoing strength | 1.549–1.621 | 0.196 |
| Baseline firing rate | 0.909–0.930 | 0.235 |
| Strong outgoing mass | 0.963–0.996 | 0.137 |

Passing pooled mean balance still permits materially different distributions. These are descriptions, not retroactive rejection criteria. All twelve candidates remain saved, including less favorable diagnostics. There are no lesion results for them. Evidence: [protocol](evidence/2026-10-08/diverse_comparisons/protocol.json), [all count-valid assignments](evidence/2026-10-08/diverse_comparisons/assignments.csv), [all accepted memberships](evidence/2026-10-08/diverse_comparisons/members.csv), [independent verification and distributions](evidence/2026-10-08/diverse_comparisons/verification.json). The full fractional vector and logs remain under results/pcdr/diverse_comparisons_20261008.

## Research decision

We can now separate two obstacles. The response ordering against the existing alternatives persists across the tested steps; lack of trajectory convergence still limits numerical interpretation. Independently, comparison design remains too narrow and poorly matched in distribution to establish eigenmode specificity. More seeds on the existing sets would not address that second obstacle.

Do not immediately simulate these twelve new sets. That would add another descriptive family without resolving the reason the old comparison was weak. The next baseline-only design should constrain distributional mismatch prospectively and seek several distinct families, with overlap and infeasibility reported. One concrete approach to evaluate is minimizing a maximum empirical-CDF gap on the six fixed log1p features subject to unchanged count rules and explicit overlap constraints. This is proposed, not implemented here; its objective, candidate-pool construction, resource limits and independent checks must be recorded before a solver run. Distribution constraints must not be tuned to obtain desired lesion effects, and optimization still will not create a calibrated random null.

No new convergence standard or confirmation claim is introduced. The exact continuous-time response, biological validity, the generality of the selected burst mechanism and the original eigencircuit-specific hypothesis remain unresolved. The original question is preserved rather than replaced with burst suppression.

## Reproduction and implementation checks

From the repository, prefix each command with `.venv/Scripts/python.exe` and choose unused output paths:

```text
scripts/pcdr_fine_contrasts.py --out <contrast-output-directory>
scripts/pcdr_comparison_capacity.py --out <capacity-output-directory>
scripts/pcdr_diverse_comparisons.py --out <search-output-directory>
scripts/pcdr_verify_diverse.py --study <search-output-directory> --out <verification.json>
```

The default fine plan is the original downloaded file whose bytes match the previous verification hash. The repository plan parses identically but has different bytes; the first contrast invocation correctly stopped at that hash mismatch. No frozen file or hash was rewritten. An initial test fixture attempted to put infinity into a pandas integer column and failed before reaching the analysis; defining that fixture's A column as float corrected the test. No scientific output resulted from either failed attempt.

Across focused invocations, 34 tests passed: 28 for the new analyses plus six existing LP/completion tests. Coverage includes paired ordering, ties, strict sign reversals, shuffled input order, changed verified files, missing/duplicate keys, undefined/nonfinite readouts, exact neuron-ID precision, changed membership, exhaustive overlap bounds, a known constrained LP optimum, infeasibility, and distribution differences with equal means. Raw simulation evidence and the current upload remain unchanged. Code, analysis and documentation were prepared with Codex assistance; this is not an independently student-written submission.
