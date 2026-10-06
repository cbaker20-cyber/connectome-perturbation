# Incoming-input calculations, 6 October

Technical analysis record; this is not an STS submission draft. These calculations continue the saved-data checks without a new simulation. The three targets were selected retrospectively from the preceding first-spike decomposition.

## Reconstruct before the first spike

The three upstream targets had no spike before the crossing being examined and receive no direct Poisson stimulation. Their initial voltage is −52 mV and drive is zero. Until their first spike there is no reset or postsynaptic refractory interval. Every incoming event can therefore be summed using the model's linear response, starting at time zero. The source spike trains remain those observed in the saved network run.

This extends the earlier analysis: missing voltage recordings do not prevent a conditional reconstruction for a never-fired cell with a known initial state. They do prevent claiming that the reconstructed voltage was directly recorded. The method does not by itself locate the first network-wide discrepancy or test a lesion.

Used all incoming signed connections, the actual 1.2 weight multiplier and 0.8 inhibitory multiplier, the 1.8-ms delay and the MN9 outgoing lesion. Kept root IDs as strings and event times as integer ticks. An arrival at the evaluated threshold tick contributes no voltage yet. Reject targets with any earlier spike, external stimulation, or incompatible input data. For the finer run, evaluated the same physical times as the coarser first spikes.

| Target root ID | Coarser first spike (ms) | Coarser voltage (mV) | Finer voltage at that time (mV) | Finer distance below threshold (mV) |
| --- | ---: | ---: | ---: | ---: |
| 720575940638633806 | 640.1388 | −44.999991187 | −49.955751237 | 4.955751 |
| 720575940629910636 | 641.9756 | −44.999894074 | −50.312123164 | 5.312123 |
| 720575940611439473 | 639.9664 | −44.999814378 | −49.689648934 | 4.689649 |

Coarser means 0.0004 ms and finer means 0.0002 ms. The coarser reconstruction is below threshold at the preceding tick and above at the saved first-spike tick for all three cells. The finer cells remain silent through the available 750 ms. This calculation checks the voltage at these paired times; it does not compute the maximum voltage at every earlier tick.

## Source contributions

Two common sources supply the largest positive differences in the reconstructed voltage:

| Target | Difference contributed by 720575940629667639 (mV) | Difference contributed by 720575940623862015 (mV) |
| --- | ---: | ---: |
| 720575940638633806 | 4.734234 | 0.669677 |
| 720575940629910636 | 4.403160 | 1.714522 |
| 720575940611439473 | 1.915360 | 3.432544 |

Each entry is that source's coarser-minus-finer contribution, including all its arrivals before the target's comparison time. It is not a fitted coefficient or effect of deleting that source. Other signed contributions account for the remaining net difference; the displayed positive differences can exceed the net difference when other sources contribute in the opposite direction.

Source 720575940629667639 fires at 616.7112 and 634.7532 ms in the coarser run, versus 603.6980 ms in the finer run during 590–645 ms. Source 720575940623862015 fires at 618.6280 and 635.9712 ms versus 605.6464 ms. Both sources first fire near 105–107 ms, long before the broad recruitment window. The source timing histories and full signed tables are saved, rather than inferring an initiating event from a large contribution alone.

## Validation and limits

Applied the same time-zero reconstruction to the two previously recorded first-spike targets in both runs. All four comparisons match recorded voltage within 2.92 × 10⁻¹⁰ mV. These checks test the complete incoming-history calculation separately from the earlier reconstruction starting at 600 ms. Unit tests cover same-tick exclusion, simultaneous arrivals, inhibitory sign, empty input and invalid values. The response formula is also checked independently by numerical integration in the earlier tests.

No new parameter, random seed or spike trajectory was generated. The results describe this one selected altered-weight case and do not establish a general biological mechanism or eigencircuit-specific effect. The candidate-source rankings are based on already observed outcomes. Any network-level causal statement requires an intervention in which downstream spike trains are allowed to change.

Code: `scripts/pcdr_upstream_inputs.py`. [Summary and recorded checks](evidence/2026-10-06/upstream_inputs/summary.json), [signed source differences](evidence/2026-10-06/upstream_inputs/source_differences.csv), [source spike times](evidence/2026-10-06/upstream_inputs/leading_source_times.json), and [final implementation verification](evidence/2026-10-06/upstream_inputs/verification.json). The initial summary and tables were preserved; a second execution after adding source-history output produced identical numerical results.

## Literature checked against the calculation

The [Shiu model methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC11446845/) specify the voltage/drive equations, resting/reset/threshold values, delay and drive reset. Its limitations section warns against treating absolute firing rates as accurate biological predictions. These facts support using the published model for a controlled calculation, not interpreting this particular burst as measured fly physiology.

[Brian2 2.9.0 refractory documentation](https://brian2.readthedocs.io/en/2.9.0/user/refractoriness.html) explains state clamping and rejection of changes to refractory variables. The earlier local boundary tests and recorded-state comparisons verify the behavior actually used here. [Hanuschkin et al. (2010)](https://www.frontiersin.org/journals/neuroinformatics/articles/10.3389/fninf.2010.00113/full) distinguish exact subthreshold integration from spike-time handling. That distinction applies here: agreement with the linear solution is not proof of network trajectory convergence. These are reading notes on previously used sources, not a submission bibliography.
