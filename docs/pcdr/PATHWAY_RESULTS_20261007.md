# Two-connection intervention: results reviewed 7 October

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

The two coarser trials took about 1.97–1.98 hours each; the finer trials about 3.70–3.73 hours each. They ran concurrently and finished on 6 October at 21:47 UTC (5:47 p.m. Eastern). Per-worker peak memory was 3.00–4.01 GB. The requested four cores and 32 GB were sufficient.

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
