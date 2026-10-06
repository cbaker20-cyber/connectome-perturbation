# Shared source cells: inputs and resets, 6 October

This is an assisted technical analysis of existing recordings, not a student-written submission or a new frozen experimental plan.

## Question and method

The previous reconstruction identified two shared sources, 720575940629667639 and 720575940623862015, whose activity contributes to three downstream first spikes in the selected altered-weight case. Both shared sources had already fired before 600 ms. Starting from the model's initial state without accounting for resets would therefore be incorrect.

Reconstructed voltage separately after the last reset preceding each comparison. In this implementation a spike resets voltage to -52 mV and drive to zero. Inputs during refractoriness are rejected; accepted later inputs contribute through the same exact linear response used in the earlier checks. Because both reset values are equilibrium values in the absence of input, the initial refractory interval adds no voltage or drive contribution. Events on the comparison tick are excluded because threshold testing precedes synaptic delivery. The current crossing itself is not treated as a previous reset.

Comparison times are the union of the two cells' observed spike times between 600 and 640 ms, evaluated on both grids. This gives 12 comparisons, including the finer run's earlier spikes, rather than selecting only the coarser run's crossings. Connectivity and archive hashes were checked. No new simulation, parameter fit or neuron selection search was performed.

## Results

For readability, G denotes 720575940629667639 and H denotes 720575940623862015 only in this table. Threshold is -45 mV. Coarser is 0.0004 ms; finer is 0.0002 ms.

| Cell | Coarser spike time (ms) | Coarser voltage (mV) | Finer voltage at the same time (mV) |
| --- | ---: | ---: | ---: |
| G | 616.7112 | -44.999869 | -51.872872 |
| G | 634.7532 | -44.999476 | -51.994208 |
| H | 618.6280 | -44.999638 | -52.577550 |
| H | 635.9712 | -44.999620 | -52.394260 |

Both cells are outside refractoriness at all comparison times. Thus an active refractory block at those four times does not explain the absent finer spikes. Previous resets still matter: G and H fired at 603.6980 and 605.6464 ms in the finer run. Their histories are not otherwise identical.

The largest positive contribution at each of the four coarser crossings comes from CRE011 cell 720575940628695043. Its arrivals at 615.1504 and 633.2560 ms contribute 6.073762 and 5.871700 mV to G, and 8.905062 and 7.614337 mV to H. Signed contributions from other cells complete the totals; a positive contribution larger than 7 mV can be partly offset by inhibition. In the finer run its earlier arrival at 602.0258 ms contributes 6.419448 mV at G's earlier crossing and 9.115620 mV at H's earlier crossing. Those contributions are subsequently removed by the postsynaptic resets.

All 12 reconstructed voltages match recorded values within 2.99e-10 mV. This adds a check spanning repeated spikes and resets to the previous checks before first firing. Tests explicitly cover exclusion of events before/on reset, exclusion of comparison-tick events, acceptance at refractory release, empty events, missing reset history and unsorted history.

## What this establishes and what remains open

The different incoming spike histories and resets quantitatively account for the recorded voltages of these two cells. The source is a previously identified CRE011 cell, so the traced pathway returns to a cell already under investigation. This is not evidence that it was the first cause of divergence. The calculations do not show what would happen if its spikes were removed: the rest of the network could respond differently.

The original question remains whether eigencircuit support predicts localized lesion responses beyond simpler connectivity explanations. This selected burst is a numerical reliability issue affecting that interpretation, not confirmation of an eigencircuit. Stable group averages and unstable individual trajectories must remain separate statements.

The next useful technical comparison is a targeted intervention with a declared endpoint, rather than further unrestricted source ranking. Before any CCR submission, specify whether the intervention tests this pathway's contribution to the burst or the original eigencircuit localization claim; these are different questions. A pathway test would need matched stimulation, both time steps, unchanged reference runs, and downstream trajectories recomputed after intervention. Its outcome would still apply to this selected case. No such intervention was run or presented as a result here.

The model and event-order rationale are covered by the previously checked [Shiu methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC11446845/) and [Brian2 refractory documentation](https://brian2.readthedocs.io/en/2.9.0/user/refractoriness.html), with the actual implementation additionally checked against saved states. See the [prior source review](UPSTREAM_INPUT_CHECKS_20261006.md) for the distinction between exact subthreshold integration and network trajectory agreement.

Code: `scripts/pcdr_source_resets.py`. Evidence: [12 comparisons and provenance](evidence/2026-10-06/source_resets/summary.json) and [complete signed source contributions](evidence/2026-10-06/source_resets/contributions.csv).
