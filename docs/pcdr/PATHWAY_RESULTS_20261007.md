# Two-connection intervention: results reviewed 7 October

Update: the late-switch comparison has also completed. See the final section below for verified results; the earlier sections preserve the time-zero experiment and its original follow-up proposal.

Removing two selected connections from the start of the simulation prevented the broad late recruitment seen in the 0.0004-ms reference. This is an intervention result in one selected model case. It does not establish a biological circuit, explain the first difference between time steps, or resolve the failed convergence criteria.

## What was compared

Four 750-ms trials used seed 631430, weight scale 1.2, inhibitory scale 0.8 and the existing MN9-only outgoing lesion. The same 21 sugar-input cells received the archived stimulation. At each of 0.0004 and 0.0002 ms, an unchanged reference was paired with a trial setting two directed connection weights to zero: CRE011 cell 720575940628695043 to cells 720575940629667639 and 720575940623862015. These connections contain 286 and 237 annotated synapses, respectively. The intervention did not directly silence either target or remove the source cell's other outputs.

These connections were selected from the preceding state and input reconstruction, after seeing the unusual burst. Their combined removal tests whether that selected pathway contributes to the observed outcome. It is not an independently selected confirmation sample. The [preceding record](SOURCE_RESET_CHECKS_20261006.md) documents selection and preparation.

## Declared measurements

The window is [650,730) ms. Input cells are excluded. Newly recruited cells must fire in that window and have no earlier spike before 650 ms. Counts were recalculated from raw spike files using integer ticks and per-cell first spikes, independently of the simulation's endpoint helper.

| Step (ms) | Condition | Non-input spikes | Newly recruited non-input cells |
|---|---|---:|---:|
| 0.0004 | Reference | 15,093 | 7,623 |
| 0.0004 | Two connections removed | 1,381 | 0 |
| 0.0002 | Reference | 1,435 | 4 |
| 0.0002 | Two connections removed | 1,436 | 2 |

At 0.0004 ms, the spike reduction is 13,712, or 90.85%. At 0.0002 ms, the difference is one additional spike, or 0.070%. Neither contrast has a sampling uncertainty estimate: there is only one selected seed at each step. No p-value is assigned.

Both target cells are silent throughout both intervention runs. However, their absence changes the network well before the measured burst. The first changed spike relative to the same-step reference is the missing target-720575940629667639 spike at 105.376 ms (0.0004-ms step) or 105.7838 ms (0.0002-ms step). The common source's later spike history also changes. Therefore, this result cannot separate a late triggering role from effects accumulated over the previous half-second.

Similar totals also do not mean the same neuron-by-neuron activity. Across the full 750 ms, 9,951 cells change their spike count in the coarser comparison and 357 in the finer comparison. The sums of absolute per-cell count differences are 29,586 and 705, respectively. These are additional descriptive checks, not declared acceptance criteria.

## Check for activity displaced beyond the measurement window

An additional check, chosen after inspecting the results, counted [730,750) ms. The coarser reference has 15,250 non-input spikes and 1,850 cells firing for the first time; its intervention has 274 spikes and no first-time cells. The finer reference and intervention have 322 and 331 spikes, respectively, with two and zero first-time cells. Thus, no comparable burst appeared in the intervention during the remaining recorded 20 ms. Activity after 750 ms is unknown. The original [650,730)-ms endpoints were not changed.

For reproduction, `pathway_timecourse.json` excludes input IDs, rounds `t*1000/dt` to integer ticks, counts events before tick `650/dt` and from tick `730/dt`, counts first spikes from tick `730/dt`, and bins all non-input events into fifteen consecutive half-open 50-ms windows. These supplementary counts can be checked directly against the same archived Parquet files.

## Verification and execution

The result ZIP contains 54 files and passes CRC checks. Its SHA-256 is `926b934aaa8fd535c3cc5f08881202d90f8b2ace4b0822af735e3ec81562df2d`. The source inventory and every source byte match the uploaded package, SHA-256 `f1da39cd5deed199401054335833a8ef9f7b68ed63722b12e9943b99ac082674`. Plan, model/data, original reference and individual output hashes agree. Python is 3.11.5 and the recorded simulation packages match the plan.

All four trials reached 750 ms with successful process exits and empty stderr. Scheduled and delivered inputs were compared directly with the archived physical input tape and earlier delivered records. Both unchanged references reproduce the earlier spike prefixes exactly. Removed-connection records match the original connectivity rows and the neuron ID/index mapping. The temporary modified connectivity itself was not retained; selective modification is supported by the archived implementation, its tests and the recorded removed rows, not by a saved hash of that temporary file.

Spike checks cover exact string IDs, valid times, time order, the time grid, duplicate neuron/time events and non-input refractory spacing. Stimulated cells have zero refractory duration in this model and are excluded from the 2.2-ms spacing check. Saved endpoints, selected-cell histories and summary manifests agree with the underlying files. Deliberately altered spike bytes and a missing archived source are rejected by the reviewer.

The two coarser trials took about 1.97â€“1.98 hours each; the finer trials about 3.70â€“3.73 hours each. They ran concurrently and finished on 6 October at 21:47 UTC (5:47 p.m. Eastern). Per-worker peak memory was 3.00â€“4.01 GB. The requested four cores and 32 GB were sufficient.

Ten new reviewer tests passed. The complete `tests` directory passed 444 tests, with three skipped and 255 dependency deprecation warnings. Test success verifies implementation behavior; it does not establish convergence or physiological validity.

## Interpretation and next comparison

The narrow supported statement is: under this seed, altered-weight network, MN9 lesion and 0.0004-ms implementation, the joint time-zero removal prevents the observed late recruitment. It does not show that either individual connection is necessary, that the pair alone is sufficient to cause recruitment, or that another intervention would not produce the same suppression. Selection after observing the burst limits generalization. The burst is absent in the unchanged finer reference, so this remains a study of a step-sensitive model outcome.

The most informative next comparison is to preserve the reference trajectory until 600 ms and then disable the same two connections, at both existing steps. The cutoff precedes the traced 613.3504-ms source spike in the coarser run and the 600.2258-ms source spike in the finer run. It is deliberately selected from the existing trajectories and must be reported as such. The unchanged pre-600-ms history must match exactly; the late measurement window and final time should remain fixed. A no-change switch must reproduce the entire reference, not just its early prefix.

Before running that comparison, test switch timing, already queued synaptic events, refractory handling and preservation of external stimulation on small networks. The two selected source-to-target connections have no source spikes in the final 1.8 ms before 600 ms in the saved references, so no selected-edge event is expected to be in flight at this cutoff; the implementation must still define and test delivery-time behavior explicitly. Do not infer it from a weight assignment alone.

If late joint removal suppresses recruitment, compare each connection separately under the same timing to distinguish their contributions. If it does not, examine the earlier trajectory changes rather than describing the pair as a late trigger. These tests are proposed, not implemented or run here. A new upload is not needed for the present local review. Broader seed/control comparisons and the existing convergence failures remain separate questions.

## Relation to the numerical methods

The model's linear state update is not forward Euler: Brian2 documents `linear` as an alias for exact integration of linear equations. Exact between-event integration does not remove the clock resolution of spike timing and propagation. This result must therefore be described as sensitivity of the full spiking simulation, not evidence of an Euler implementation error. [Brian2 2.9.0 integration documentation](https://brian2.readthedocs.io/en/2.9.0/user/numerical_integration.html).

Brian2 also distinguishes refractory duration from clamping selected state variables during refractoriness; incoming writes to clamped variables are ignored. The recorded model implementation and input checks preserve these choices. They were not changed to obtain the suppression result. [Brian2 2.9.0 refractory documentation](https://brian2.readthedocs.io/en/2.9.0/user/refractoriness.html).

The original model and eigencircuit papers still motivate the broader question, but do not validate this selected intervention: [Shiu et al.](https://doi.org/10.1038/s41586-024-07763-9), [Pospisil et al.](https://doi.org/10.1038/s41586-024-07982-0). This follow-up explains a limitation encountered while testing that question; it is not an eigencircuit-specific test.

Evidence: [independent review](evidence/2026-10-07/pathway_review.json), [additional time-window counts](evidence/2026-10-07/pathway_timecourse.json), [failure checks](evidence/2026-10-07/pathway_failure_checks.json), and [review code](../../scripts/pcdr_review_pathway.py).


## Second experiment: removal at 600 ms

The four late-switch trials finished on 7 October at 19:59:37 UTC (3:59 p.m. Eastern), about 2 hours 28 minutes after controller launch. Retrieved the result ZIP through OnDemand Files after the compute session ended. It contains 57 members, passes CRC checks and has SHA-256 `650315b319875f910b625a4090d64f2d565b777b7ba2b2bbb181f77ffa10bcff`. Source bytes and inventory match the late-switch upload, SHA-256 `5cb352017aa8142a8ee37b3b889eff1c3f1fce44b3019bf0634c321b94c1db89`.

All four spike histories before 600 ms exactly match the original saved reference at their respective steps. Both no-change switches also reproduce the entire 750-ms reference exactly. Scheduled and delivered external input matches the original tape in every trial. The switch records identify the intended connections and their original scaled weights, 94.38 and 78.21 mV. The intervention sets those weights to zero at 600 ms; the no-change controls retain them. The reviewer independently checks these values against the original connectivity and ID/index mapping. All output hashes, packages, process exits, progress records, spike-format checks and recalculated endpoints pass. Worker stderr is empty.

| Step (ms) | Condition | Non-input spikes in [650,730) ms | Newly recruited cells |
|---|---|---:|---:|
| 0.0004 | No-change switch | 15,093 | 7,623 |
| 0.0004 | Pair removed at 600 ms | 1,442 | 1 |
| 0.0002 | No-change switch | 1,435 | 4 |
| 0.0002 | Pair removed at 600 ms | 1,459 | 6 |

The coarser spike count decreases by 13,651 (90.45%). The finer count increases by 24 (1.67%). As before, these are single selected-case contrasts with no sampling inference. The default-network convergence failures remain unchanged.

The first changed spike is the missing target-720575940629667639 spike at 616.7112 ms in the coarser comparison and 603.6980 ms in the finer comparison. Both targets retain their earlier spikes but have no spikes after 600 ms in either intervention. The source's first post-switch spike is unchanged at 613.3504 or 600.2258 ms. In the coarser run, its subsequent history changes: 630.746 and 731.5688 ms replace the reference's longer sequence. This supports an effect propagated through the recurrent network; it does not isolate every feedback route.

The additional [730,750)-ms check gives 15,250 versus 256 spikes (1,850 versus zero newly recruited cells) at 0.0004 ms. At 0.0002 ms it gives 322 versus 319 spikes (two versus zero new cells). No comparable burst appears during the final 20 recorded milliseconds. Later activity remains unobserved. Full-run per-neuron counts change for 9,845 cells in the coarser comparison and 199 in the finer comparison; sums of absolute count differences are 29,041 and 232. These supplementary descriptions do not replace the declared window.

This comparison addresses the principal limitation of time-zero removal: suppression does not require altering the trajectory before 600 ms. Under this seed, parameter setting and step, disabling the pair after the identical earlier spike history prevents the broad observed recruitment. It remains a joint intervention. It neither identifies which individual connection matters nor shows that the pair alone can generate the burst. The cutoff and connections were selected from the prior trajectories, and the untreated finer-step run lacks the burst. The result concerns a step-sensitive simulated outcome, not a demonstrated biological mechanism or eigenmode-specific effect.

The next comparison should remove each connection separately at 600 ms, retain the same two steps and endpoints, and include unchanged-switch references. That distinguishes whether either removal alone suppresses recruitment or whether joint removal is required in this case. The previous result is not a reason to relax convergence thresholds or expand to a broad seed sweep before resolving this distinction. No new cluster job or upload has been prepared for separate-edge removal yet.

Validation of the extended reviewer: 12 focused tests passed. They include wrong timing, wrong targets/order, floating-point indices, altered scaled weights, incorrect removal flags/outcomes and duplicate original connections. A deliberately changed switch time was rejected even after updating its recorded hash and summary; this checks scientific specification beyond file integrity. The original time-zero review still reproduces its saved JSON exactly. Full-network simulations were not rerun locally.

Reproduce the new review with `.venv/Scripts/python.exe scripts/pcdr_review_pathway.py --late --archive CCR_late_pathway_results.zip --package results/pcdr/late_package_validation_20261007/original_upload.zip --out <new-output.json>`. The additional time-course calculation follows the same integer-tick method documented above and saves post-600-ms histories for the source and two targets. Evidence: [late review](evidence/2026-10-07/late_review.json), [late time-course checks](evidence/2026-10-07/late_timecourse.json). Per-worker runtime was 74.6–75.0 minutes at 0.0004 ms and 148.2–148.3 minutes at 0.0002 ms; peak memory was 2.99–3.35 GB. Differences from the earlier node's runtime should not be attributed to the scientific intervention without a controlled performance comparison.
