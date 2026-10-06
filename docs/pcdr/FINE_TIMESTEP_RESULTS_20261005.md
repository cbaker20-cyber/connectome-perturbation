# Completed smaller-step study — 5 October 2026

The [subsequent local analysis](FINE_DIFFERENCES_20261005.md) completes the spike-based follow-ups proposed below. It does not change this study's agreement decision.

The study completed all 620 planned trials. The selected 51-neuron group's average lesion effect remained similar across 0.0008, 0.0004, 0.0002 and 0.0001 ms. The full, previously declared agreement criteria failed. Stable averages do not establish stable individual trajectories, a uniquely defined functional circuit, or biological validity.

This follows the [29 September meeting feedback](MEETING_REFLECTION_20260929.md), [local implementation checks](FINE_TIMESTEP_TESTS_20260929.md), and the frozen [run design](CCR_FINE_RUN.md) and [plan](CCR_FINE_PLAN.json). Memberships, input schedules, seeds and tolerances were retained. No candidate was selected again from these results.

## What ran and what was checked

There were 600 default-network trials: 30 seeds, five conditions (baseline, selected group, motor_003, motor_004, motor_005), and four steps. Sixteen trials revisited two altered-weight cases with their baselines. Four original-step exact replays brought the total to 620. Each scientific trial simulated one second. The 21 sugar-input neurons received the saved stimulation schedule; they were not the lesion group. Lesions suppress outgoing transmission from their specified cells.

The downloaded archive is `CCR_fine_results.zip`, SHA256 `2e6adf875a9c0f9effc62e78b1700cd8eecae7161b15352a05e13d1c02c85c8b`. Its CRCs passed. Raw evidence is retained locally under `results/pcdr/fine_download_20261005`. The final controller reports completion at 13:13 UTC (9:13 a.m. Eastern) on 5 October, job 26356255. That timestamp describes collection completion, not the start of the whole multi-session study.

The local checker read all 620 raw trial outputs, verified recorded hashes and source-input identity, checked neuron IDs and spike times, reconstructed rates and 10 ms population counts, and reproduced 488 baseline/lesion pairs, 24 mean-result rows and 366 adjacent-step comparisons. All four original-step spike and delivered-input replays matched exactly. These checks establish consistency of the saved evidence; they do not prove the model equations or hypotheses correct. Shared readout and event-validation helpers remain dependencies, so this is not a wholly separate simulator implementation.

## Selected-group averages

For each seed, the response is lesion minus baseline firing rate for each neuron. First average those signed response vectors across the 30 seeds, then take absolute values. A is the mean absolute response inside the selected group. F is the fraction of the whole-network absolute response inside that group. This order matters: opposite effects across seeds can cancel. These are not means of per-seed absolute responses.

| Step (ms) | A (Hz) | F, expressed as percent | Mean MN9 rate change (Hz) |
| --- | ---: | ---: | ---: |
| 0.0008 | 22.443 | 23.085% | -80.567 |
| 0.0004 | 22.535 | 23.057% | -82.600 |
| 0.0002 | 22.635 | 23.033% | -83.000 |
| 0.0001 | 22.508 | 22.977% | -82.233 |

At the finest step, about 77% of this absolute mean response lies outside the selected group. A larger internal response than the comparison groups therefore does not mean the effect is confined to the selected neurons.

At 0.0001 ms, motor_003, motor_004 and motor_005 had A values of 12.140, 12.548 and 12.540 Hz, and F values of 19.663%, 19.730% and 19.481%. The selected group exceeded these three comparisons descriptively. The existing overlap and matching limitations remain; this is not a calibrated random-control significance test.

## Where agreement failed

### Component check added 6 October

Rechecked all 366 saved comparison rows against their recorded hashes and split the existing decision into its parts. No tolerance changed. For the selected group at the final halving (0.0002 to 0.0001 ms), the pass counts are:

| Requirement | Passing individual pairs |
| --- | ---: |
| Internal response amplitude A | 24/30 |
| Response concentration F | 28/30 |
| Full neuronwise response | 1/30 |
| Population activity in 10-ms bins, both baseline and lesion | 1/30 |
| All requirements together | 1/30 |

The median individual full-response difference is 13.73%; the median population difference is 15.41%. Both exceed the declared 5% tolerance. These comparisons allow differences; they do not require identical spike times. At the preceding halving, no selected-group pair passes either of these two requirements. The complete group rule requires at least 29 of 30 joint passes as well as a passing mean response. None of the 18 condition-by-halving groups passes the full rule.

The observations are usable as results at the stated model settings and steps. They support approximate stability of the tested average summaries, not convergence of individual responses or a continuous-time limit. They also do not validate biological circuit function or resolve imperfect comparison-group matching. Failed convergence does not make every saved number meaningless; it limits the claims those numbers support. Explaining the altered-weight burst will not automatically resolve the separate default-network agreement failures.

`pcdr_agreement_breakdown.py` reproduces every saved individual pass/fail decision from the component thresholds and joins each comparison to its finer-step amplitude. Tests cover inclusive boundaries, undefined F, missing matches, duplicate rows and conflicting saved decisions. [Component counts and input hashes](evidence/2026-10-06/agreement_breakdown/components.json). The original study tables below remain unchanged.

The rules required both final halvings to pass. For each adjacent comparison, A had to differ by at most the larger of 1 Hz and 5% of finer-step A; F by at most 0.01; and the full response vector by at most 5% in relative L1 distance. Both baseline and lesion population time courses also had a 5% relative L1 tolerance. A group required a passing mean response and at least 95% of individual paired trials passing the response and population conditions together. Undefined F failed. These were chosen practical tolerances, not published biological standards.

The selected group's mean response vector differed by 2.95%, 2.91% and 2.21% across successive halvings. All three mean comparisons passed. Individual joint passes were only 0/30, 0/30 and 1/30. None of the 18 condition-by-halving groups met the complete criteria.

| Condition, default network | Final-halving mean response difference | Median individual response difference | Joint individual passes |
| --- | ---: | ---: | ---: |
| Selected group | 2.21% | 13.73% | 1/30 |
| motor_003 | 5.10% | 23.38% | 1/30 |
| motor_004 | 3.56% | 24.51% | 0/30 |
| motor_005 | 3.29% | 21.06% | 1/30 |

Relative response difference is the sum of absolute neuronwise differences between the two response vectors, divided by the larger of 1 Hz and the finer vector's absolute sum. It is not a percentage error relative to a known exact solution. The finest step is the comparison reference, not a demonstrated exact answer.

## Altered-weight case that still needs explanation

With weight scale 1.2 and inhibitory scale 0.8, seed 631430 produced the following total spike counts. The intervention was MN9-only outgoing silencing.

| Step (ms) | Baseline spikes | Lesion spikes |
| --- | ---: | ---: |
| 0.0008 | 21,318 | 22,181 |
| 0.0004 | 21,534 | 239,568 |
| 0.0002 | 21,648 | 21,694 |
| 0.0001 | 21,284 | 21,401 |

The large burst at 0.0004 ms is nonmonotonic: it does not appear at either finer step in this case. Those finer runs nevertheless fail the response agreement criterion (113.03% relative difference). A relative difference can be large when the net response is small; whole-trial counts and the neuronwise response are different quantities. This one seed cannot establish how often the burst occurs. It also does not establish chaos or identify a specific implementation defect. The other altered-weight case, mode-without-MN9 at seed 631405, likewise failed final-halving agreement.

## Interpretation and next work

The reported meeting recommendation was useful: the smaller steps revealed a distinction between stable aggregate effects and unstable paired trajectories that an average alone would miss. We should present that distinction directly and retain the failed criteria. We should not loosen the thresholds after observing the results or claim that a still smaller step must solve the problem.

The implemented subthreshold update uses the linear/exact method, rather than forward Euler. Brian2 documents these as different methods. Clock-based spike detection, resets and synaptic scheduling can still make the network depend on the step. See [Brian2 2.9 numerical integration](https://brian2.readthedocs.io/en/2.9.0/user/numerical_integration.html) and [execution scheduling](https://brian2.readthedocs.io/en/2.9.0/user/running.html#scheduling). This explains why exact subthreshold evolution does not settle network agreement; it does not diagnose the cause of the observed burst.

Next use the downloaded spikes locally to locate when population activity separates, identify the neurons contributing most to adjacent-step response differences, and compare those differences with variation across seeds. Treat these as descriptive follow-ups chosen after seeing these results. In particular, examine all four versions of the burst case, alongside their baselines. Recorded spikes can identify when outputs separate, but cannot reconstruct unrecorded membrane voltages or prove which threshold event caused the divergence.

Only after that analysis should a targeted simulation be specified, if needed, with event/voltage recording near the relevant time. A separate question about stability of response distributions would need its own written criteria; it would not replace the failed trajectory comparison. Better-matched comparison groups remain necessary before claiming an eigencircuit-specific effect.

The median recorded elapsed time per completed worker was approximately 1.90, 3.78, 7.54 and 15.12 hours at the four successive steps. These are timings under the actual CCR workload, not isolated CPU benchmarks or total study duration. Full-duration concurrent runs were much slower than the local short-prefix estimate suggested. Future large runs need measured full-duration throughput and restart planning before setting expectations.

## Reproduction

Run from the repository root using the recorded local Python environment:

```powershell
.venv/Scripts/python.exe scripts/pcdr_check_fine.py --study results/pcdr/results_ccr_20260927/raw_download/expanded_sensitivity --followup results/pcdr/fine_download_20261005 --out results/pcdr/fine_verified_20261005
```

The output directory must not already exist. The original study, model data and root-level downloaded ZIP are required. Full raw evidence stays local; the compact [evidence directory](evidence/2026-10-05) contains checked tables, environment information and hashes. It cannot replace the spike files for recomputation. Simulation used Python 3.11.5 on Linux; local checking used Python 3.11.9 on Windows, with the same recorded scientific package versions. No new scientific simulation was run during this analysis.
