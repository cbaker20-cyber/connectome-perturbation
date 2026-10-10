# Adviser meeting brief — 10 October 2026

**Later verified result:** the downloaded pilot ZIP contains four completed10-ms reference/capacity runs and zero completed full scientific trials. Both old references match exactly; the capacity gate declined the twelve-trial panel. Earlier pending/active statements below describe their observation time. Use [verified results](SMALLER_STEP_RESULTS_20261010.md) and [current adviser summary](ADVISER_FOLLOWUP_20261010.md).

## Brief recap for James

The question remains the one in [the eigencircuit study plan](PLAN.md#question):

> Do concentrated eigenvector supports of the materialization-630 Shiu matrix predict localized firing-rate responses to output lesions, beyond connectivity, strong connections, and recruitment?

The output-lesion footprint is the neuron-by-neuron lesion-minus-baseline firing-rate response. Localization and comparison groups test the question above; they are not replacement questions. The [29 September meeting record](MEETING_REFLECTION_20260929.md) says James and Dr. Muldoon recommended substantially smaller timesteps, with 0.0001 ms as an example. It does not attribute our later numerical tolerances or detailed job design to them.

## New information since that recorded meeting

1. **The recommended finer-step follow-up completed:** 620 trials reaching 0.0001 ms. Selected-support mean A/F remained similar, but all 18 full numerical agreement groups failed. Thus the footprint is not established numerically converged under the declared rule.
2. **Saved-output diagnostics narrowed the issue:** differences occur in baseline as well as lesion runs, mostly within shared active cells, and are not confined to the last recording boundary. Selected local replays reproduce saved spikes. These findings do not identify a complete initiating cause or repair convergence.
3. **Selected altered-case interventions completed:** the eight separate G/H connection trials were verified; either removal interrupts recruitment in the selected coarser-step case. This is a conditional mechanism result, not general eigencircuit evidence or convergence.
4. **A further bounded pilot is active:** supplied CCR output shows 27 tests passed and a mode reference worker at 0.0001 ms. The new 0.00005/0.000025 ms work is gated by reference reproduction and capacity. No new scientific completion or convergence is confirmed.

Discussion: What do these numerical results permit us to say about the original output-lesion footprint question, and which next experiment would most directly resolve its remaining uncertainty?

## Current CCR work — status reported during this meeting preparation

The user supplied CCR terminal output showing **27 tests passed, 52 dependency deprecation warnings, in 31.25 seconds**, followed by an active pilot controller (PID 638663) and a `reference_mode` worker (PID 674985) at **0.0001 ms** on **cpn-d02-23**. Installation and dependency checks passed. This is user-supplied terminal evidence; allocation ID/resources, progress JSON, reference agreement and result files have not yet been independently retrieved. The mode worker being active does not by itself certify the preceding reference outcome.

The bounded pilot first checks saved baseline/mode reference reproduction, then measures 10 ms prefixes at **0.00005 and 0.000025 ms**. The prepared scientific panel is three original seeds, baseline/mode, two new steps: twelve one-second trials. Those trials may start only if the reproduction and resource/time gates pass. **No new scientific trial completion or convergence result is confirmed.** The authorized block ends at **12:30 p.m. Eastern / 16:30 UTC on 10 October**. All eighteen earlier full agreement groups remain failed. Short probes and passing software tests are not convergence evidence.

Suggested spoken update: “We are now checking whether the finer-step pilot reproduces the archived reference and is computationally feasible. The software tests passed on CCR and a reference worker is active. We do not yet have new convergence results.”

## Evidence to bring

Use the [full results table and explanation guide](MEETING_RESULTS_TABLE_20261010.md) for every research stage, all eighteen agreement groups, numeric lesion/intervention results and definitions of convergence and the readouts.

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

Bring the [concrete numerical-study proposal](NUMERICAL_DECISION_PROPOSAL_20261010.md). It specifies a possible twelve-trial feasibility gate and what expansion would require, alongside event-handling-reference and separately designed ensemble alternatives. Archived timing gives a roughly 545-worker-hour illustrative estimate even for that small two-halving pilot; this is not measured new-step performance or an approved allocation. The bounded smaller-step package is now prepared and its CCR reference worker is active, as described above; the twelve scientific trials are not confirmed completed.

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

The smaller-step reference/capacity pilot is now active on CCR. Solver replacement and broader experiments remain proposals, not completed evidence. This brief summarizes records through 10 October and does not certify competition compliance.
