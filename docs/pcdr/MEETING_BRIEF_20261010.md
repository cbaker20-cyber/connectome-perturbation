# Adviser meeting brief — 10 October 2026

## Opening in about one minute

“The original question is whether concentrated eigenvector support predicts localized lesion effects beyond connectivity and recruitment. The selected group still has a larger descriptive localized response than our fixed comparison groups, but the comparisons are imperfect and the numerical convergence criteria failed. All eighteen full agreement groups failed in the 620-trial fine-step study. Recent local analyses explain parts of the failure without repairing it: the baseline itself differs across steps, most count differences occur within the same active cells, and they are not confined to the recording endpoint. Replaying actual incoming histories reproduces selected cells' count differences even at a common target timestep. We have not traced the initiating network cause. I want to decide which numerical requirement is necessary for the scientific claim before another large run.”

This is a suggested explanation of the evidence, not a claim of independent authorship of the analysis or software. Describe Codex assistance accurately.

## Evidence to bring

| Question | Completed evidence | What it does not establish |
|---|---|---|
| Did finer steps establish convergence? | No. All 18 full groups failed. Final-halving selected-support joint agreement: 1/30 seeds versus required 29/30 plus the mean check; both final halvings must pass. | Stable means are not individual-response convergence. |
| Are the aggregate findings entirely absent? | Selected-support means remain similar across tested steps; selected support exceeds the three fixed comparators in the saved same-step comparisons. | Eigencircuit specificity, unbiased random-control significance, or biological function. |
| Is the failure confined to the altered-weight burst? | Default baseline median neuronwise count L1 is 578.5 at the final halving, versus 309.5 for the selected-support lesion. | A unique causal percentage attributable to baseline. |
| Is it mostly different recruited cells? | 96.43% of pooled baseline count disagreement is in cells active at both steps. | Long-run rate differences or persistent recruitment. |
| Is it merely the last few spikes crossing the recording boundary? | At least 97.45% of pooled count L1 remains under arbitrary deletion of saved final-1-ms spikes. Differences are substantial before 900 ms. | Absence of earlier timing-mediated effects or effects of unobserved future spikes. |
| Can local dynamics reproduce it? | 112 native baseline target prefixes reproduce every saved spike tick. In 26 count-selected cases, coarse incoming history at fine dt retains the coarse target count. | The initiating network cause or a free-running network counterfactual. |
| Can we cleanly split timing from count effects? | No. Constructed-mixture results depend on matching rule in 21/26 cases; many violate source refractory spacing. | A defensible percentage assigned to timing versus spike count. |
| Did the latest refractory check resolve the mechanism? | No acceptance changes among 366 exact shared events; only 1.54% coverage of incoming records. | Absence of refractory effects involving shifted events. |

The L1 values above are sums of absolute neuronwise differences, not a typical cell's rate or the population's net rate. A one-second count difference is numerically equal to its rate difference in Hz. Selected cases and repeated target neurons are not independent representative samples of the entire network.

## Actual-history lead and its limits

**Newest local finding, 10 October:** At the first cumulative two-spike gap in each of the 26 selected target cases, the other-run cell is ready to fire but below threshold; 17 are below rest. One model-inhibitory CB4058 cell is the largest inhibitory contributor in 16 cases across six targets. This is an actual-history conditional voltage reconstruction with independent numerical checks, not a network intervention or proof of the initiating cause. Repeated targets and different reset histories limit the inference. See [crossing states and source contributions](COUNT_CROSSINGS_20261010.md). This is a concrete lead to discuss, not a reason to replace the numerical decision with another lesion sweep.

**Concrete actual-history example:** In the smallest selected seed, CB4058 sends eleven arrivals before comparison in each run. Its latest arrival is blocked during target refractoriness in the coarse run and accepted after release in the fine run, contributing −28.2941 mV to the reconstructed fine target voltage. Both source timing and target reset history differ, so this is not a controlled causal test. The [two-run timeline and full-panel table](CB4058_HISTORY_20261010.md) make the proposed timing/reset interaction explainable without fabricated histories.

**Connection to the original comparison problem:** CB4058 is lesioned in the mode but absent from all three fixed comparison lesions. Its large individual-lesion response was already reported at the older coarse timestep. This is a specific influential-cell alternative to eigencircuit specificity, not proof that this cell explains the combined effect. A new test would still need numerical validation and an explicit design; no such new experiment has run.

**Repeated-target sensitivity:** The other-run CB4058 contribution is more negative in the within-target median for eight of fifteen distinct targets, equal for six and opposite for one. Excluding the most repeated target leaves ten supportive, six equal and one opposite case. This supports discussing the lead beyond one repeatedly selected cell, while retaining selection bias and the contrary cases.

## Decisions to ask for

Bring the [concrete numerical-study proposal](NUMERICAL_DECISION_PROPOSAL_20261010.md). It specifies a possible twelve-trial feasibility gate and what expansion would require, alongside event-handling-reference and separately designed ensemble alternatives. Archived timing gives a roughly 545-worker-hour illustrative estimate even for that small two-halving pilot; this is not measured new-step performance or an approved allocation. No new run is prepared.

1. **What numerical claim does the project need?** Should individual paired responses agree across resolution under the existing criteria, or is a separately declared distribution/ensemble question scientifically appropriate? We should retain the original failed result either way. Existing seeds can inform design, not become unacknowledged fresh confirmation.
2. **What single next experiment would change that decision?** If paired convergence remains necessary, agree on a bounded solver/timestep diagnostic, fixed inputs and cases, required state/event records, resource cap and stop rule before CCR. A still smaller step alone has no guaranteed value. A different event-handling solver would require its own implementation validation and is not currently ready.
3. **How should we address comparison validity?** Optimized comparison groups overlap and remain imperfectly balanced. More seeds do not fix that. Decide whether to redesign the comparison study, narrow the descriptive claim, or prioritize a numerical-methods question while retaining the original eigencircuit question as unresolved.

My recommendation for discussion: stop broad intervention and comparison sweeps until the numerical target is agreed. Preserve the original eigencircuit question; treat diagnostic mechanism work as supporting analysis. The saved data already support a careful account of numerical sensitivity and selected local propagation, but that is not the positive eigencircuit claim we originally sought.

## Likely questions and direct answers

**“Was it a coding mistake?”** No specific coding defect explaining the disagreement has been demonstrated. Prior tests cover input mapping, schedule, delays, refractory behavior and selected exact replays. That is bounded evidence, not proof that every implementation detail is correct or biologically appropriate.

**“Does exact subthreshold integration guarantee accuracy?”** It does not establish the clocked spike/reset/recurrent-event trajectories' convergence. The implemented model's event handling still depends on resolution. We have not established a continuous-time reference solution.

**“Did we give up on convergence?”** No criteria were loosened or failures removed. We diagnosed existing results and now need a deliberate decision about what new evidence would establish the required numerical claim.

**“Do the G/H interventions solve this?”** They suppress a selected altered-weight late burst under the tested removals, with verified references and pre-switch histories. They do not resolve default-network convergence or establish eigencircuit specificity. The eight separate G/H trials are complete; no duplicate is needed.

**“Are the new checks independent?”** Separate algorithms and archived-output comparisons reduce shared implementation risk. They are not independent human review. Code and research records used Codex assistance; adviser review remains important.

## Selective supporting records

- [Original fine-step findings](FINE_TIMESTEP_RESULTS_20261005.md) and [unchanged agreement breakdown](OVERNIGHT_DECISION_20261009.md).
- [Baseline versus lesion](STEP_CANCELLATION_20261009.md), [shared active cells](BASELINE_COUNTS_20261009.md), and [endpoint bounds](BASELINE_TIME_20261009.md).
- [Actual-history local replays](BASELINE_REPLAY_20261009.md), [limits of constructed mixtures](HISTORY_PARTS_20261009.md), and [latest narrow refractory check](BASELINE_GATING_20261010.md).

No new full-network experiment, CCR launch, solver replacement or upload is prepared by this brief. The next experiments above are proposals for discussion, not completed evidence. This brief summarizes records through 10 October and does not certify competition compliance.
