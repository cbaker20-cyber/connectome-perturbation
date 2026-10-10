# Actual states at the first two-spike count gap — 10 October 2026

In all 26 previously selected target cases, the other run's target is available to fire but below threshold when the leading run first reaches a cumulative two-spike lead. None is actively refractory at that comparison tick. Seventeen are below the resting voltage, indicating net inhibitory contributions since the last reset. This narrows the immediate state explanation without identifying the initiating network cause.

## Recorded selection and reconstruction

Retained the 26 targets and prefix limits from BASELINE_REPLAY_20261009.md and the four seeds with no prior selection. For each target, processed the union of saved spike times, handling simultaneous events together, and selected the first absolute cumulative count difference of at least two. This is an exploratory event-selection rule, not a revised convergence tolerance. Selected event times span 131.2182–867.3142 ms, median 412.99145 ms.

Reconstructed voltage immediately before threshold detection from accepted actual presynaptic arrivals since the last observed target reset. Used the already tested linear impulse response, 1.8-ms delay, zero-drive reset and 2.2-ms refractory gating. All 52 native prefixes had previously reproduced their own target spikes without supplied resets; this calculation uses saved resets explicitly to explain individual states. These targets have no direct voltage recordings in the fine-step archive.

When the event falls on a fine-only tick, evaluated the coarse run at its immediately preceding native tick, at most 0.0001 ms earlier, and retained that lag. No interpolation is described as an observed threshold decision. Every leading event has reconstructed previous-native-tick voltage at or below -45 mV and event voltage above -45 mV; all 52 comparison states agree with their saved spike/readiness status.

Other-run voltage ranges from -80.9161 to -45.2999 mV, median -54.3064 mV; threshold is -45 mV and rest is -52 mV. All 26 are ready to fire. Earlier blocked inputs still occur in all 26 leading histories and 25 other histories since their last resets. Thus the result excludes an active refractory block at the selected comparison times, not earlier refractory amplification. Different reset histories also create different integration intervals; their median ages at comparison are 5.8665 ms in the leading run and 14.0826 ms in the other run. No causal percentage is assigned to inhibition, timing or resets.

## Source decomposition and a candidate for discussion

After verifying those states, recorded an additional decomposition of every accepted source contribution at all 52 states, without selecting new target events. Source contributions sum to reconstructed voltage minus rest. They are conditional algebraic contributions, not effects of deleting that source from the network.

Neuron 720575940643867296 is the largest inhibitory contributor in 16 of the 26 other-run states. The supplied annotation labels it CB4058, with predicted top transmitter gaba (confidence 0.7146); its connections are inhibitory in the model. The 16 cases span six distinct targets, including eight occurrences of 720575940618165019 and three of 720575940630868793. These repetitions are not sixteen independent circuit demonstrations. Median inhibitory contribution magnitude from this source in those cases is 24.9936 mV, accounting for a median 87.01% of total inhibitory voltage contribution. Twelve of the sixteen states lie below rest.

This cell belongs to the original selected 51-cell support and was already listed in the earlier CCR report's single-cell response ranking. It is not a newly discovered neuron. Its prominence here is a new selected-state observation. Do not call it the cause of the global numerical failure, an eigencircuit-specific mediator, or a validated intervention target. Strong inhibition and reset-dependent integration are alternative explanations that require explicit comparison. No new lesion or parameter change was run.

## Verification, preserved failure and limits

Three event/state tests passed in 0.54 seconds, including simultaneous count events, absent gaps, reset/release boundaries and initial silence. A separate chronological count walk reproduced every selected gap. A two-state matrix exponential with explicit refractory-interval checks independently reproduced 78 voltages (52 event states and 26 preceding leader states), maximum error 4.98e-14 mV. A separate scalar event loop and matrix exponential reproduced all 923 per-source contributions, maximum error 7.82e-14 mV. These are separate computations, not independent human review.

The first source-decomposition attempt stopped at its sum check because the verification expression added +52 instead of the resting voltage -52. It produced no scientific result table. Preserved its exact source, protocol and failure record in results/pcdr/crossing_sources_20261010. Corrected only that verification expression and reran into results/pcdr/crossing_sources_fixed_20261010; source contributions then passed independent checks. This new analysis error is not an identified error in the archived simulator.

Full outputs: results/pcdr/count_crossings_20261010 and results/pcdr/crossing_sources_fixed_20261010. Compact [crossing evidence](evidence/2026-10-10/count_crossings/snapshot.json) and [source evidence](evidence/2026-10-10/crossing_sources/snapshot.json) retain records, checks and failed-attempt provenance. Scripts: `pcdr_count_crossings.py` and `pcdr_crossing_sources.py`, each with `--out <unused-directory>`; focused tests: `tests/test_pcdr_count_crossings.py`.

For the meeting, this supplies a specific lead: actual voltage states and a recurrent inhibitory source, with reset history as an explicit confounder. It does not connect the earliest microscopic timing shifts to the later count gap or demonstrate a biologically causal mechanism. All eighteen original full convergence groups still fail. Code, analysis, verification and documentation used Codex assistance.
