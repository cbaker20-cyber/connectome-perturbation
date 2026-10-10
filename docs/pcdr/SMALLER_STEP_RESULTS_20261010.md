# Smaller-step pilot: verified results — 10 October 2026

**Four 10-ms runs completed; none of the twelve one-second scientific trials started.** This is a successful reproduction/capacity check, not a completed convergence experiment. The controller stopped normally at 16:00:51 UTC with `budget_insufficient`, before the 16:30 UTC deadline. The later deadline memo described uncertainty before the ZIP was available; this report supersedes that operational uncertainty.

## What changed, held fixed and completed

All four runs use original seed631401 and the first10ms of its saved physical stimulation. The references retain0.0001ms; new baseline probes change only timestep. Model/source, signs, weights, schedules and selected support remain frozen. The second reference applies the original mode output lesion. No new-step mode-lesion prefix ran. Recorded allocation: job26427313, cpn-d02-23,3CPUs,32000MB, one serial worker; these are controller records, not a fresh scheduler query.

| Run | Step (ms) | Duration | Spikes / active cells | Non-input spikes | Runtime (min) | Peak GB | Individual conclusion |
|---|---:|---:|---:|---:|---:|---:|---|
| reference_baseline_0.0001 | 0.000100 | 10 ms | 26 / 18 | 3 | 4.00 | 2.713 | Exact archived spikes and delivered inputs reproduced |
| reference_mode_0.0001 | 0.000100 | 10 ms | 26 / 18 | 3 | 4.03 | 2.712 | Exact archived spikes and delivered inputs reproduced |
| probe_5e-05 | 0.000050 | 10 ms | 26 / 18 | 3 | 7.96 | 2.787 | Baseline capacity prefix completed; no full lesion footprint |
| probe_2.5e-05 | 0.000025 | 10 ms | 26 / 18 | 3 | 15.75 | 3.057 | Baseline capacity prefix completed; no full lesion footprint |

Every run has23 scheduled and23 delivered external events; physical input identities/times match the original saved tape. Both references also have identical baseline/mode output over this short prefix. This does not imply a zero one-second lesion effect.

## Comparison of the baseline prefixes

| Halving (ms) | Per-neuron count L1 difference | Shifted spikes /26 | Mean absolute time difference (ms) | Maximum (ms) |
|---|---:|---:|---:|---:|
| reference_baseline_0.0001 → probe_5e-05 | 0 | 26 | 0.000051923 | 0.000100000 |
| probe_5e-05 → probe_2.5e-05 | 0 | 26 | 0.000026923 | 0.000050000 |

Ordered neuron identities agree, allowing the stated ordinal spike-time comparison. A separate common-integer-grid event-set comparison finds52 symmetric-difference events between each new-step baseline and the original baseline: all26 times move, despite equal per-cell counts. Only three spikes per run are from non-input neurons. Timing differences shrink in this short early window; this is not evidence that the later recurrent response or full one-second footprint converged. No A/F or original convergence pass is assigned to these prefixes. The JSON `exact_reference:false` for probes means they were not same-step reference tests, not that they failed one.

## All twelve planned scientific trials

All rows below were blocked by the same capacity gate, not selectively dropped for their outcomes. Each would have lasted one simulated second. No trial-specific rate, footprint or convergence result exists.

| Seed | Condition | Step (ms) | Execution | Convergence |
|---:|---|---:|---|---|
| 631401 | baseline | 0.000050 | Not started | Not evaluated |
| 631401 | mode | 0.000050 | Not started | Not evaluated |
| 631402 | baseline | 0.000050 | Not started | Not evaluated |
| 631402 | mode | 0.000050 | Not started | Not evaluated |
| 631403 | baseline | 0.000050 | Not started | Not evaluated |
| 631403 | mode | 0.000050 | Not started | Not evaluated |
| 631401 | baseline | 0.000025 | Not started | Not evaluated |
| 631401 | mode | 0.000025 | Not started | Not evaluated |
| 631402 | baseline | 0.000025 | Not started | Not evaluated |
| 631402 | mode | 0.000025 | Not started | Not evaluated |
| 631403 | baseline | 0.000025 | Not started | Not evaluated |
| 631403 | mode | 0.000025 | Not started | Not evaluated |

## Cost and defensible next experiment

The frozen screen doubles the10-ms runtime and scales it to one second:26.52hours/trial at0.00005ms,52.51hours/trial at0.000025ms; six of each total474.22serial worker-hours. The controller had1015seconds of allowed scientific budget remaining after reserves/allocation limits. Its refusal was expected under that rule; it was not a scientific failure. Prefix peak memory2.71–3.06GB is not a measurement of full-duration memory; the plan budgets at least16GB/worker plus8GB reserve.

Recommendation: retain the twelve-trial design as the next bounded numerical pilot, rather than jumping to still smaller steps or another intervention sweep. First amend execution prospectively for an explicit multi-day allocation and a validated small concurrency cap, with fixed source/input/readout criteria. For example, four workers under the current scheduling estimates need an optimistic balanced wall time around132hours, excluding queue/setup/slowdown. This is scheduling arithmetic, not measured concurrent throughput. A72-hour allocation is not enough under that four-worker screen; shorter allocations need validated restart or separately submitted trials. A16-core allocation does not make the existing serial launcher parallel. Do not edit its frozen deadline or resume it blindly.

A practical first wave would be baseline/mode for seed631401 at both new steps (four full trials), with the seed fixed by the existing plan, not chosen for favorable results. Validate actual full-trial time/memory before releasing the remaining eight. Evaluate complete pairs only; keep all failures, and do not turn early stopping into a pass. Even twelve successful trials would be a three-seed pilot, not satisfaction of the original30-seed criterion. Expansion needs a separate resource decision. No new launch was performed in this review.

If full-pair disagreements do not shrink, do not keep halving indefinitely. Retain the negative numerical result and discuss an independently validated event-handling reference, or a separately designed question about ensemble-average footprints. Neither is ready or a retrospective replacement for failed criteria. A two-week deadline cannot guarantee convergence.

Brian2 documents exact linear subthreshold integration separately from clocked execution of thresholds, synapses and resets. This makes timestep-dependent events possible; it does not prove a particular source of our late disagreement. Sources checked10October: [integration](https://brian2.readthedocs.io/en/2.9.0/user/numerical_integration.html), [scheduling](https://brian2.readthedocs.io/en/2.9.0/user/running.html#scheduling).

## Verification and provenance

Read the downloaded ZIP without executing its code or extracting over existing research. CRC and unique-member checks pass. All46 included package files match the current validated upload byte-for-byte; all12 parquet output hashes match their measurements. Separate local comparisons reproduce both old reference prefixes, physical input pairing, bounds, ID strings, grid membership, no duplicate events and successful worker exit records. Capacity arithmetic is independently recomputed. The result ZIP is a partial package snapshot; it does not include every full dataset needed to rerun the network. It is preserved locally unchanged.

Result archive SHA256: `2f61b39cd9267a391a000ad15a295feb21305b836c7af7770309243bfa64c278`.

Verification: [machine-readable record](evidence/2026-10-10/smaller_results/verification.json). Checker: `scripts/pcdr_check_smaller_results.py`; refuses an existing output directory and records any exception before propagating it. No failed verification attempt occurred in this review. Existing preparation failures remain in the earlier pilot record. Local/software analysis used Codex assistance; these checks are not independent human review.

Verifier failure tests also passed: deliberately changed source bytes and changed parquet bytes were rejected before interpretation; an existing verification output directory was refused. Fixtures and stderr are preserved locally; these are intentional tests, not failed scientific trials. See evidence/2026-10-10/smaller_results/failure_tests.json.
