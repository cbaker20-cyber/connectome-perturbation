# Baseline count disagreement — 9 October 2026

At the final timestep halving, 96.43% of pooled baseline count disagreement occurs in neurons active at both steps. Only 3.57% comes from cells active at one step and silent at the other. This narrows the default-baseline problem to count differences largely within the shared active population; it does not identify their initiating cause.

## Timing-code question and prior coverage

The user asked whether timing drift might be an implementation mistake and requested no repeated audits. Reviewed the current fine simulator and analysis code against the recorded checks in [fine-step tests](FINE_TIMESTEP_TESTS_20260929.md), [mechanism review](BURST_MECHANISM_REVIEW_20261005.md), [earlier saved-output analysis](FINE_DIFFERENCES_20261005.md) and [local replay memo](OVERNIGHT_DECISION_20261009.md). No new discrepancy was identified in this targeted review. Those existing checks already cover input-grid conversion, recording-window continuity, delay/refractory divisibility, threshold/synapse/reset scheduling, and exact selected-prefix reproduction. They are bounded implementation evidence, not a proof that all code is error-free. No simulator audit suite or network simulation was repeated.

The earlier conversational suggestion that the remaining disagreement could be timing drift needs qualification: the failed response-vector comparison uses full-second spike counts. Moving spikes between bins while retaining each neuron's total cannot explain that count disagreement. Timing changes can still change subsequent spikes, or move spikes across the observation endpoint; counts do not exclude those mechanisms. Earlier 1/5/10/20-ms bin comparisons already exist and were not repeated.

## New completed analysis

Recorded a protocol before reading the new partition results. Used all thirty default baseline seeds at 0.0002 and 0.0001 ms, sixty archived trials, with no seed selection. Checked the archive and plan hashes, neuron inventory, trial specifications and each consumed spike/rate hash. Counted saved spikes by exact string neuron identifier and required agreement with saved one-second rates. Stimulated neurons are included.

For each neuron, partition its absolute count difference into exactly one category: active only at the coarser step, active only at the finer step, or active at both. Silent-at-both cells contribute zero. No temporal alignment, new tolerance, p-value or simulation was used.

| Component | Pooled count L1 across 30 seeds |
|---|---:|
| Active only at 0.0002 ms | 273 |
| Active only at 0.0001 ms | 311 |
| Active at both | 15,796 |
| Total | 16,380 |

Each trial lasts one second, so a spike-count difference is numerically equal to its rate difference in Hz. The table sums absolute differences over neurons and seeds, not a net population-rate change. The pooled fractions weight each seed by its total disagreement; they are not average per-seed fractions.

Median active-cell counts are 379.5 at the coarser step and 378.5 at the finer step. Median coarse-only and fine-only cell counts are 5.5 and 6.5; the median number of shared active cells with unequal counts is 258.5. Median shared-active count L1 is 557.5, and median total L1 is 578.5. These separate medians need not add. Similar active-population sizes alone would not establish matching membership; the cellwise partition supplies that distinction here.

## Verification and limits

Nine known-answer/failure tests passed in 0.45 seconds, covering mixed categories, silence, identical counts, invalid shapes/values, unsigned subtraction and large integer sums. A separate loop recomputed every partition from the saved changed-cell table; each changed-cell count matched separately read saved rates. All thirty total distances match the previously verified baseline decomposition, across all four reused comparison rows per seed. Those reused rows are not independent replicates. Full records are in results/pcdr/baseline_counts_20261009; the [compact snapshot](evidence/2026-10-09/baseline_counts/snapshot.json) includes every changed-cell count, paired summaries, provenance and verification.

Activity labels apply only to the one-second observation window. This does not demonstrate persistent recruitment differences, persistent rates, pure timing drift, chaos, or a specific code defect. Full-second count differences can include endpoint effects; the present analysis does not quantify them. All eighteen original full convergence groups remain failed. The original eigencircuit-specific question and comparison limitations remain unresolved.

The next useful diagnostic is to determine where the baseline count differences accumulate over time, including whether the end of the observation window accounts for much of them. Use saved outputs and all seeds with fixed windows, retaining the previously computed bin evidence; do not choose a visually dramatic seed as representative. A targeted state/event replay would require a recorded selection rule and would remain diagnostic. No new CCR run or upload is prepared by this analysis.

Reproduce with `.venv/Scripts/python.exe scripts/pcdr_baseline_counts.py --out <unused-directory>` and `tests/test_pcdr_baseline_counts.py`. Code, analysis and documentation used Codex assistance; separate arithmetic verification is not independent human review.
