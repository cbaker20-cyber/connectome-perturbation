# Conditional downstream crossings — 9 October 2026

All six first outside spike differences pass a conditional voltage-reconstruction check. At the saved crossing tick the reference exceeds -45 mV, while the intervention remains below it; the preceding reference tick does not cross. This is not a free-running replay or a convergence result: observed postsynaptic reset histories are inputs to the calculation.

## Audit and design

Reviewed the archived model and existing `pcdr_input_reconstruction.py`, `pcdr_source_resets.py`, `pcdr_upstream_inputs.py`, `pcdr_recurrent_delivery.py` and `pcdr_first_spike.py`. Earlier checks establish the relevance of refractory gating and reset boundaries. The model uses resting/reset voltage -52 mV, threshold v > -45 mV, membrane time constant 20 ms, g decay 5 ms, refractory period 2.2 ms and synaptic delay 1.8 ms. Both v and g stop updating during refractoriness; reset clears g. Synaptic arrivals at the threshold tick cannot affect that tick's threshold decision because threshold testing precedes synaptic delivery.

Recorded a separate protocol before reconstruction. For each of the six earliest outside differences, use saved reference and intervention presynaptic spike trains, remove the original outgoing-lesion edges, apply the archived weight scaling, delay arrivals and reject arrivals during observed postsynaptic refractoriness. Reconstruct from the most recent reset before evaluation, or from the known resting initial state when there is no reset. Evaluate only the preceding and crossing ticks. No fitted parameters, new intervention or full-network simulation.

The impulse kernel is (exp(-lag/20)-exp(-lag/5))/3 for accepted g increments, with lag in milliseconds. Arrivals at evaluation time are excluded. Earlier-than-reset inputs are excluded because the reset clears g. The four downstream targets are not directly stimulated, and the removed source-to-G/H connections do not directly enter their incoming-edge tables.

## Results

| Step | Removal | Reference crossing voltage (mV) | Intervention at same tick (mV) | Difference (mV) |
|---|---|---:|---:|---:|
| 0.0004 | G | -44.999867684 | -45.006515529 | -0.006647845 |
| 0.0004 | H | -44.999775057 | -45.000196108 | -0.000421051 |
| 0.0004 | Both | -44.999867684 | -45.006515529 | -0.006647845 |
| 0.0002 | G | -44.999977148 | -45.510938343 | -0.510961195 |
| 0.0002 | H | -44.999961306 | -45.019319365 | -0.019358059 |
| 0.0002 | Both | -44.999977148 | -45.510938343 | -0.510961195 |

All targets are outside refractoriness at evaluation. Within each comparison the last reset agrees between reference and intervention. The finer H-first target has no earlier spike; its reconstruction starts from the initial state. Joint-removal rows duplicate the first G-route calculation, so these are six comparisons but four distinct local situations.

A separate two-state matrix exponential evaluates the voltage difference from the single missing upstream input. It agrees with reconstructed intervention-minus-reference voltage to below 5e-15 mV in all six cases. This independently checks the difference, not absolute state or a full trajectory. The previous route audit established that no other changed incoming presynaptic emission can arrive by these first outside differences.

## Limits and next check

These results support the local threshold explanation conditional on saved incoming events and reset histories. The missing input is enough in this conditional calculation to place the intervention below threshold at the reference tick. This does not establish permanent silencing, a unique burst mediator, network counterfactual sufficiency or generality across cases. Absolute voltages are reconstructed, not independently recorded for these four targets in the returned archive.

The next verification is a bounded local replay that generates its own thresholds/resets from saved incoming trains and compares the resulting spike times. Existing kernel and gating tests are necessary but cannot substitute for that check. It remains pending. If it fails, preserve the failure and do not describe this endpoint calculation as complete trajectory reproduction.

Convergence remains unestablished. The original final-halving selected-support counts were A 24/30, F 28/30, full neuronwise response 1/30, population activity 1/30 and all criteria jointly 1/30. The rule requires at least 29/30 joint passes plus a passing mean, and both final halvings must pass. All eighteen full groups failed. The criteria allow differences, including 5% relative L1 response/population tolerances; the failure is not a requirement for identical spikes. Explaining this altered-weight selected case does not resolve default-network convergence or imperfect comparison design.

## Evidence

Twelve focused tests passed in 0.83 seconds across the new endpoint routine and existing source-reset, upstream-input and recurrent-delivery tests. They cover the analytical impulse response, current-tick exclusion, reset exclusion, refractory recovery boundaries and invalid inputs. All six recorded crossing checks passed; the separate matrix-exponential difference check also passed. The archive and prior evidence hashes were verified. Full records: results/pcdr/downstream_crossings_20261009; [compact evidence](evidence/2026-10-09/downstream_crossings/snapshot.json).

Code, tests, audit, analysis and documentation used Codex assistance. Separate numerical calculations are not independent human review.
