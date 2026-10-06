# Shared source cells: inputs and resets, 6 October

This is an assisted technical analysis of existing recordings, not a student-written submission or a new frozen experimental plan.

## Method

Checked the two shared sources identified in the previous analysis: 720575940629667639 and 720575940623862015. Both had fired before 600 ms, so each calculation starts from its last reset (-52 mV, zero drive). Inputs during refractoriness and on the comparison tick are excluded. The zero-drive reset means the refractory interval itself adds nothing to voltage.

Used the union of their spike times between 600 and 640 ms: six times, checked in both runs. Archive and connectivity hashes matched. No new network simulation was needed.

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

All 12 reconstructed voltages match the recordings within 2.99e-10 mV. Boundary tests cover resets, refractory release and event ordering; failure tests cover missing and unsorted histories.

## Interpretation

Incoming spikes and previous resets account for these recorded voltages. The largest source is a CRE011 cell already identified earlier. This does not locate the first divergence or show what happens when the network responds to an intervention. The eigencircuit question remains open; stable group averages do not establish stable individual trajectories.

## Next test, prepared locally

A focused intervention can remove the CRE011 source's connections to these two cells while retaining its other outputs. The source has 749 outgoing connections in this dataset. These two carry counts of 286 and 237, totaling 523 of its 7,287 absolute outgoing counts (7.18%). Their model increments are 94.38 and 78.21 mV at the selected weight settings; these increments act on drive, not directly on voltage.

The local connectivity check changed exactly two of 14,687,178 rows and left the original file unchanged. A three-cell simulation showed that removing one directed connection stops its target from firing while the other target still fires. Scheduled and delivered external input remained identical. Temporary connectivity files are removed after success or failure. The existing simulator was left unchanged so earlier replay records remain usable.

The proposed full-network comparison is reference versus these two removed connections at 0.0004 and 0.0002 ms, using the same saved stimulation, seed 631430, weight settings and MN9 outgoing lesion as the diagnostic. Run through 750 ms, with spike count and newly recruited cells in 650–730 ms as descriptive endpoints. Check whole-prefix input equality and the two source-cell spike histories. Removing edges from time zero tests their contribution across the trajectory; it does not isolate a late event. A late-onset intervention would answer a different question and is not implemented here.

This is a selected-case pathway test, not a random-control comparison or a test of eigencircuit specificity. Suppression would support a contribution of this route; persistence would show these two connections are not required for the burst under that intervention. Neither outcome settles why the first timing difference arose. The full-network intervention has not run, and no new upload package was created.

Code: `scripts/pcdr_edge_intervention.py`. [Connectivity check](evidence/2026-10-06/edge_intervention/connectivity_check.json).

The model and event-order rationale are covered by the previously checked [Shiu methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC11446845/) and [Brian2 refractory documentation](https://brian2.readthedocs.io/en/2.9.0/user/refractoriness.html), with the actual implementation additionally checked against saved states. See the [prior source review](UPSTREAM_INPUT_CHECKS_20261006.md) for the distinction between exact subthreshold integration and network trajectory agreement.

Code: `scripts/pcdr_source_resets.py`. Evidence: [12 comparisons and provenance](evidence/2026-10-06/source_resets/summary.json) and [complete signed source contributions](evidence/2026-10-06/source_resets/contributions.csv).
