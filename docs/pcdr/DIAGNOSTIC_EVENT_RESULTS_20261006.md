# What drives the first recorded recruitment

Analysis dated 6 October UTC, continuing the evening of 5 October Eastern. These are local calculations from the returned diagnostic; no further CCR simulations were run.

The new result is an explanation of the immediate input to one recruited cell. In the 0.0004-ms replay, cell 720575940628455942 first fires at 647.9524 ms. Two upstream spikes provide most of the positive voltage contribution at that crossing. Both upstream cells are silent in the 0.0002-ms replay through 750 ms. This advances the explanation of recruitment, but does not identify the first difference between the networks or prove which connections are necessary for the burst.

## Check the event and state calculations first

Reconstructed arrivals from the full saved spike trains, the signed connectivity, the actual weight scaling and the 1.8-ms delay. Removed outgoing edges from the lesioned MN9. Used postsynaptic spikes to determine acceptance during the 2.2-ms refractory period, including rejection on the spike tick. Compared the summed accepted increments with recorded after-synapse minus before-threshold drive at every recorded tick for all 13 recorded non-input neurons. External Poisson targets are excluded from this particular check because recurrent events alone would not describe their stimulation.

The largest absolute difference was 1.14 × 10⁻¹³ mV. Independently evaluated the linear subthreshold solution from each previous end-of-step state, freezing state when refractory. Voltage updates differ by at most 4.27 × 10⁻¹⁴ mV and drive updates by at most 5.69 × 10⁻¹⁴ mV. Recorded spike resets match exactly. The first recorded tick is excluded from the update comparison because its preceding state was not saved; all other recorded ticks are checked, including chunk boundaries.

These comparisons cover 375,000 recorded ticks at 0.0004 ms and 750,000 at 0.0002 ms per neuron. They support correct implementation of the specified updates in the recorded cells and window. They do not prove time-step convergence or biological accuracy, and do not cover unrecorded cells or earlier states. The model and literature context remain in [the mechanism review](BURST_MECHANISM_REVIEW_20261005.md).

## The first spike of cell 720575940628455942

This cell has no earlier spike, so no reset occurs between the first recorded state and its crossing. Its voltage can therefore be decomposed into the decayed initial state plus contributions from each accepted input. For a synaptic drive increment w arriving L milliseconds before the crossing, its voltage contribution is

`w × [5/(5−20)] × [exp(−L/5) − exp(−L/20)]`.

The constants are the model's 5-ms drive decay and 20-ms membrane time constant. This is the continuous linear solution between events used to reconstruct this trajectory, not an Euler approximation. Each arrival begins affecting voltage after its synaptic update. The calculation uses native integer ticks to align those times. Numerical quadrature tests independently check the contribution formula.

| Presynaptic neuron | Source spike (ms) | Arrival (ms) | Drive increment (mV) | Voltage contribution at crossing (mV) |
| --- | ---: | ---: | ---: | ---: |
| 720575940639283278 | 645.3312 | 647.1312 | 128.04 | 4.747433 |
| 720575940623387786 | 643.9632 | 645.7632 | 42.90 | 3.587712 |

All arrivals to the selected cell between 600 ms and its first crossing are accepted; this immediate difference is not explained by the cell blocking those same events during refractoriness. The largest two arrivals are absent in the finer run because their presynaptic cells have not fired. Refractory effects elsewhere in the network remain possible.

The initial state alone would relax to −52.239221222 mV at the crossing time. The signed sum of all incoming contributions is +7.240165152 mV, giving −44.999056069971 mV. Recorded voltage is −44.999056069929 mV, an absolute difference of 4.16 × 10⁻¹¹ mV after accumulating many steps. The spike threshold is −45 mV. The two largest positive contributions sum to more than the net contribution because other inputs include inhibition. Their drive increments must not be mistaken for membrane-voltage jumps.

The older broad-window ranking included cell 720575940628455942 as a contributor back to 720575940639283278. Its first outgoing event cannot arrive until 649.7524 ms, after 720575940639283278 first fires at 645.3312 ms. That feedback therefore cannot explain the latter cell's first spike. Event ordering prevents treating a large later-window contribution as an initiating input.

## What is still unresolved

The earlier state of source 720575940623387786 was not recorded. Source 720575940639283278 was recorded, and its incoming events can be traced further using these files. Another candidate source, 720575940628695043, was already active before 600 ms; its trajectory cannot be decomposed over this window as though no prior resets occurred. The two networks already have different states when recording begins.

The next local task is to follow the recorded upstream cell's first crossing and distinguish inputs before versus after that event. Any additional recording should then target a specific missing interval or cell. Removing a connection from a calculation while holding all other spike trains fixed would be a conditional single-cell calculation; it would not establish that a whole-network lesion prevents the burst. A network intervention would need its own planned comparison. There is still no converged eigencircuit result from this diagnostic alone.

## Follow-up: the upstream cell's first crossing

Continued the same decomposition for recorded cell 720575940639283278. Its first spike is at 645.3312 ms. Three earlier spikes supply the largest positive contributions at this crossing:

| Source | Source spike (ms) | Arrival (ms) | Voltage contribution (mV) |
| --- | ---: | ---: | ---: |
| 720575940638633806 | 640.1388 | 641.9388 | 2.184520 |
| 720575940629910636 | 641.9756 | 643.7756 | 2.181501 |
| 720575940611439473 | 639.9664 | 641.7664 | 1.982269 |

All three are silent in the finer-step replay through 750 ms. Including every signed input reconstructs −44.999909922642 mV versus recorded −44.999909922588 mV, an error of 5.48 × 10⁻¹¹ mV. The three source cells' voltages were not recorded, so this is where the current state-based tracing stops. Their saved spikes and connectivity still permit checking their incoming event histories locally. Any subsequent state recording should be selected after that review, rather than adding cells one at a time without a defined stopping point.

The extended first-spike script permits either of the two analyzed recorded cells, and rejects crossings outside the saved 600–650-ms event interval. Evidence is preserved separately in [upstream_first_spike](evidence/2026-10-06/upstream_first_spike/summary.json); the earlier decomposition is unchanged. This remains retrospective tracing of the same seed and parameter setting.

## Reproduction and evidence

`scripts/pcdr_diagnostic_events.py` produces the recorded-update checks, incoming-source totals, selected event times and source spike histories. Its descriptive windows overlap (600–650 and 640–650 ms); do not add those windows together. Selection of the additional upstream cells was made after inspecting these returned data. No significance test is attached to that selection.

`scripts/pcdr_first_spike.py` reconstructs the selected cell's first crossing and writes all signed contributions. Both scripts require the independently validated returned archive. Fourteen focused tests passed, covering refractory boundaries, a known undriven solution, a quadrature comparison, and rejected mismatches/nonfinite or invalid lags. This is separate from the real-data comparisons above.

Evidence: [event checks](evidence/2026-10-06/diagnostic_events/checks.json), [selected arrivals](evidence/2026-10-06/diagnostic_events/selected_events.csv), [source times](evidence/2026-10-06/diagnostic_events/source_spike_times.json), and [first-spike reconstruction](evidence/2026-10-06/first_spike/summary.json). The full incoming-source and contribution tables are retained beside these files.
