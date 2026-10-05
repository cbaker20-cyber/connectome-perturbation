# Code and literature review of the burst

Later on 5 October: [source attribution below](#follow-up-tracing-the-input-sources) identifies two CRE011 cells supplying much of the increased drive. The current upload records 34 cells, adding those two before full diagnostic execution. References to 32 cells below describe the original validation.

5 October 2026. The best supported working explanation is amplification of small changes in recurrent event timing in the altered-weight network. Refractory gating provides a concrete route for amplification: a shifted postsynaptic spike can change whether a subsequent recurrent input is accepted. We have demonstrated that rule in the implementation and reconstructed its input accounting, but have not identified the event that initiates this particular burst. It would be premature to call this a demonstrated coding error, numerical convergence, chaos, or biological activity.

## What the implementation actually does

The model uses Brian2's linear/exact update for voltage and synaptic drive between discrete events. Its two subthreshold time constants are 20 and 5 ms. It tests voltage against a strict threshold, delivers recurrent events after 1.8 ms, resets voltage and drive on firing, and applies a 2.2 ms refractory period to non-input neurons. Both voltage and drive have the `unless refractory` flag. This means recurrent input can be discarded during refractoriness, rather than queued for later integration. Brian2 documents the read-only behavior of such variables during the refractory period ([2.9.0 documentation](https://brian2.readthedocs.io/en/2.9.0/user/refractoriness.html)).

Small-network tests confirmed that an inhibitory drive increment inside refractoriness is discarded, while the same increment outside it is applied. The seemingly unusual reset assignment to `w` does not erase synaptic weights in this implementation; a test checked that the synaptic weight remains unchanged. Neither feature was introduced by the new recorder. The upstream Shiu model has the same refractory flags, reset expression and linear method. Twelve parameter expressions were compared by parsed syntax, and the retrieved upstream source was saved with SHA256 `fc45837d7122c6ce2a7f3f2f23c515992e4b232aadb919efabb72337fac88e4e`. This identifies the reviewed source, since upstream main can change ([upstream model](https://github.com/philshiu/Drosophila_brain_model/blob/main/model.py)).

The altered-weight implementation multiplies negative weights by 0.8, then all weights by 1.2. Relative to the default, excitation is therefore 1.2 times as large and inhibitory magnitude is 0.96 times as large. The excitation-to-inhibition scaling ratio increases by 25%. It is inaccurate to describe this as inhibition alone being reduced by 20% while everything else is fixed.

MN9 has 83 outgoing rows in the supplied connectivity table, all positive, corresponding to 116 anatomical synapses. Of those rows, 40 target neurons assigned an inhibitory sign in the model (52 synapses), and 43 target excitatory neurons (64 synapses). Removing MN9 output therefore removes excitation to both categories. Indirect disinhibition is possible, but these anatomical counts do not determine the net dynamical effect. There is no direct removal of inhibitory MN9 output here.

The input events remain on the original saved 0.1 ms schedule. Finer simulation steps do not turn that into a newly sampled continuous-time Poisson process. The recurrent delay and refractory duration are integer multiples of every fine step, so ordinary rounding of a non-integral fixed delay is not the explanation. Threshold crossing, reset and refractory eligibility still depend on clocked spike times.

## What the literature supports

[Shiu et al. (2024)](https://doi.org/10.1038/s41586-024-07763-9) describe the current model's constants, drive reset and connectome-derived sign assignments. Their robustness tests concern their selected predictions and stimulation protocols; those results do not guarantee trajectory convergence for this altered-weight lesion case. Their stated physiological simplifications also limit biological interpretation.

[Hansel et al. (1998)](https://doi.org/10.1162/089976698300017845) showed that time discretization can affect synchronization in integrate-and-fire networks. Their Euler/Runge–Kutta results motivate examining event timing, but do not establish that Euler integration caused our result: our implementation uses a different subthreshold update.

[Hanuschkin et al. (2010)](https://doi.org/10.3389/fninf.2010.00113) address precise spike timing in time-driven simulations, including the distinction between subthreshold integration accuracy and event timing. Their methods support this distinction; they do not supply a universal step size at which this fly model becomes correct. A smaller step alone cannot be used as a certificate of accuracy.

These sources support investigating clocked events and recurrent feedback. None identifies the cause of the observed seed-specific burst for us.

## Additional local evidence

Implemented an optional read-only recorder and replayed the first 20 ms of the full 127400-neuron network at 0.0004 and 0.0002 ms. Both produced 147 spikes and matched their archived spikes and delivered inputs exactly. The recorder measures 32 fixed cells at three phases: after integration but before threshold detection, after synaptic processing but before reset, and after reset. Files are written in 10 ms simulation chunks. The recorded schedule is retained.

The two prefix workers took about 122 and 191 seconds while overlapping on this PC, with peak resident memory of 2.84 and 2.94 billion bytes. These measured prefixes validate event preservation and give a memory estimate; they do not include the burst or establish full-duration runtime.

I also reconstructed recurrent arrivals from all saved presynaptic spikes, the signed connectivity, the 1.8 ms delay and observed postsynaptic spike/refractory times. This is conditional reconstruction under the model, not direct voltage measurement or a new intervention. At both steps it reproduced measured drive increments in the 20 ms prefixes to within 8e-15 mV across the 32 recorded cells. Tests cover arrival before firing, at firing, inside refractoriness, exactly at release, and zero-refractory input cells. A spike still blocks input in its own tick before eligibility is updated again.

This corrects an overly broad statement in the preceding note: spikes alone are not state measurements, but with known equations, parameters, initial state and complete event histories we can reconstruct model-predicted inputs, and potentially internal states. We should check those reconstructions against recorded states rather than assume they are either impossible or automatically correct.

For the ten selected non-input cells, the reconstructed drive accounting during 650–700 ms is:

| Step (ms) | Accepted excitatory increments (summed mV) | Accepted inhibitory magnitudes (summed mV) | Blocked excitatory increments | Blocked inhibitory magnitudes |
| --- | ---: | ---: | ---: | ---: |
| 0.0008 | 0.66 | 16.368 | 0 | 0 |
| 0.0004 | 12649.56 | 2972.904 | 2288.55 | 1415.304 |
| 0.0002 | 0.99 | 8.712 | 0 | 0 |
| 0.0001 | 1.32 | 22.440 | 0 | 0 |

These are accumulated weighted jumps across cells and time, not membrane potentials, steady currents, or average voltages. The ten cells were selected for increased pre-burst activity, so these large differences are descriptive and selection-dependent. Both excitation and inhibition are much greater in the burst version. The data do not support simply saying that inhibition vanished. Refractory blocking can be a consequence of increased firing as well as a contributor to feedback. This accounting therefore supports recurrent amplification without establishing the first cause or which pathway is necessary.

## What the next run will test

Prepared two unchanged MN9-lesion replays of seed 631430, with steps 0.0004 and 0.0002 ms, from time zero to 750 ms. Record the fixed 32 cells during 600–750 ms. This directly covers the rise in recruitment without repeating the most expensive step or a broad parameter sweep. The recordings can show threshold margins, accumulated drive and refractory availability around that rise, and validate the reconstructed input accounting there.

Both complete spike and delivered-input prefixes must match the archived trajectories exactly before any state is interpreted. The package retains failures, refuses conflicting controllers, hashes the record files and only creates the result ZIP after both successful checks. A failed recording comparison is a technical failure, not a new biological outcome. State recording may still miss an initiating neuron outside the selected set; even successful records may motivate a further, specifically justified intervention.

The one current upload is `exports/CCR_Diagnostic.zip`. Use [the run directions](CCR_BURST_DIAGNOSTIC.md): 4 cores, 32000 MB, 12 hours, two workers, no GPU. The recorder and local prefix checks are complete. The 750 ms diagnostic replays have not run yet; the package needs to be uploaded and started in CCR. No model equations, lesion memberships, input schedules or previous scientific tolerances were changed to make the burst disappear.

## Reproduction and scope

`scripts/pcdr_state_recorder.py` handles bounded recording. `pcdr_burst_diagnostic.py` handles replay, reference checks and collection. `pcdr_recurrent_delivery.py` reconstructs arrival acceptance from saved spikes and checks it against the measured prefixes. `pcdr_build_burst_diagnostic.py` builds the self-contained upload. The optional hook in the fine simulator does nothing when no recorder is supplied.

Full records are in `results/pcdr/diagnostic_prefix_20261005`, `results/pcdr/recurrent_delivery_20261005`, and `results/pcdr/mechanism_review_20261005`. The compact [evidence directory](evidence/2026-10-05/mechanism) records source hashes, prefix results, recurrent accounting and release checks. The original fine-step archive remains unchanged. This work narrows mechanisms; it has not established a unique cause or repaired the separate limitations of the eigencircuit comparison groups.

## Follow-up: tracing the input sources

Attributed recurrent arrivals to their presynaptic cells in two windows, 600–650 and 650–700 ms, for the original ten non-input recording targets at all four steps. This uses the previously validated refractory accounting and the original fixed 32-cell plan, rather than the subsequently amended recording plan. Archive, spike and connectivity hashes were checked. All 32 accepted/attempted aggregate comparisons agree with the previous reconstruction. Root IDs remain strings; source-cell labels come from the supplied annotation table.

At 650–700 ms, the burst version sends 14938.11 mV of summed excitatory increments toward those ten cells, of which 12649.56 mV is accepted (84.68%). At the finest step only 1.32 mV arrives, all accepted. These are sums over connection events, not membrane voltages. The increased drive is therefore primarily associated with additional arriving events in this window, not simply a greater acceptance fraction for an unchanged input stream. This does not exclude an earlier role for refractory gating in producing the changed spike history.

Two sources, both annotated CRE011, contribute 8201.82 mV, or 64.84% of accepted excitation to these ten targets in 650–700 ms. In 600–650 ms they contribute 2754.51 mV, or 77.60%. The percentages refer only to the selected targets, not all excitation in the brain.

| Source root ID | Full-second spikes at 0.0008 ms | At 0.0004 ms | At 0.0002 ms | At 0.0001 ms |
| --- | ---: | ---: | ---: | ---: |
| 720575940628455942 | 0 | 69 | 0 | 0 |
| 720575940628695043 | 11 | 79 | 9 | 10 |

Cell 720575940628455942 first fires at 647.9524 ms in the burst version; it remains silent for the entire second in the other versions. Cell 720575940628695043 fires at 613.3504, 631.4560 and 647.8732 ms in the burst version, then more frequently. Its firing already differs before the first cell is recruited. The two have reciprocal excitatory connections, with anatomical counts of three in the first-to-second direction and one in reverse. These small direct connections are not by themselves an explanation of the large response. Other incoming pathways and recurrent loops may matter.

This is a useful narrowing of the mechanism: an upstream change in activity supplies much of the drive to the selected pre-burst cells. It does not establish that either CRE011 cell is the initiating cause or that silencing it would eliminate the burst without introducing other changes. A counterfactual intervention has not been run. No causal label is assigned from temporal precedence alone.

Amended the unrun diagnostic plan to record both sources, for 34 total cells. This lets us inspect their voltage, recurrent drive and refractory state during the existing 600–750 ms window. The original 32 targets, input tape, lesion, weights, steps and trial duration remain unchanged. The selection is explicitly based on observed results. The original plan and validations remain preserved, and the new recording plan and prefix validations are recorded in [source-attribution evidence](evidence/2026-10-05/source_attribution). The 750 ms runs are still pending; the one current upload remains `exports/CCR_Diagnostic.zip`, now with this amendment.
