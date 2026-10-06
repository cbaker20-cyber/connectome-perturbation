# Returned burst recordings — 5 October 2026

Both instrumented replays finished and reproduced their original spike and delivered-input sequences exactly through 750 ms. Recording the additional variables did not change the observed spike trajectories. The recordings show how different the selected cells' states become, but they do not yet establish the first cause of the difference between time steps.

## What ran

Used the existing allocation 26356255 on cpn-d03-19. Both runs used seed 631430, the w120_i080 weights, the MN9 outgoing lesion, and the same saved stimulation as the corresponding original trial. They simulated from zero to 750 ms and recorded 34 selected cells during 600–750 ms. Selection and its pre-run amendment are preserved in the [mechanism review](BURST_MECHANISM_REVIEW_20261005.md) and lab notebook. The 21 sugar inputs were stimulated; they were not the lesion targets.

| Time step | Whole-network spikes, 0–750 ms | Elapsed time | Peak resident memory |
| --- | ---: | ---: | ---: |
| 0.0004 ms | 44,820 | 73.92 minutes | 3.10 GB |
| 0.0002 ms | 16,180 | 146.89 minutes | 3.51 GB |

These counts cover 750 ms, so they must not be compared directly with earlier full-second totals. The controller completed at 22:58:04 UTC (6:58 PM Eastern). The returned archive is 1,388,458,755 bytes. Its SHA256 is `99027297d3982591eae3eb5876ba99641166070942ec51e1c75b629445aa6ba2`.

## Independent checks after download

The download was initially incomplete and continued growing. Analysis began only after it became a complete ZIP with the same size shown on CCR. Read all 120 members with CRC checking, rejected duplicate names, compared the plan and archived simulation sources against the upload, and checked all 49 output hashes per run. Both manifests describe the planned duration, recording window, neuron list and package versions.

Compared both downloaded spike tables and delivered-input tables with the uploaded original reference tables, using exact values and order. All four comparisons passed. Validated all 90 state files: expected time ticks, neuron indices and array shapes, finite voltage and drive, and Boolean refractory state. For every recorded neuron in both runs, crossings of v > −45 mV outside refractoriness at the before-thresholds phase match the saved spike ticks exactly during 600–750 ms. This gives 68 neuron/run comparisons. Three failure tests also verify rejection of duplicate archive members, a changed plan and an unfinished controller.

The threshold check establishes agreement between recorded state and spike output. It does not establish numerical convergence, biological realism, or correctness of every network interaction. The schedule-specific voltage and synaptic-drive arrays are preserved for further analysis.

## What the recordings show so far

The two CRE011-labelled source cells were added before these replays because the earlier connectivity/spike reconstruction associated them with much of the excitation arriving at the ten selected targets. They remain observation targets, not established causes.

At the first recorded sample near 600 ms, cell 720575940628695043 has voltage −51.543743 mV and drive 0.010479 mV in the 0.0004-ms run, versus −45.854789 mV and 84.170910 mV at 0.0002 ms. These are markedly different starting states. The finer-step cell is initially closer to threshold, even though it is the coarser-step network that later develops the large burst. Thus the observed sequence is not adequately described as the coarser run simply having more excitation at every time.

Cell 720575940628455942 remains below −52.527577 mV throughout the finer-step recording window, well below the −45 mV spike threshold. In the coarser run it crosses threshold. During 640–650 ms its maximum drive is 161.090502 mV in the coarser run; the finer run's maximum is −2.392936 mV. These are maxima over a window, not simultaneous paired measurements. The variable g has voltage units and represents the model's synaptic drive; these numbers are not membrane voltage or a measured biological conductance.

These observations support the earlier description of different recurrent input/activity developing into broad recruitment. They do not show that either selected cell initiates the divergence or that their direct reciprocal connections are necessary. Recording starts after the two trajectories already differ. A smaller time step also does not, by itself, turn one stochastic recurrent trajectory into a verified physiological prediction.

## Next analysis

Use the saved states locally to trace incoming events around the source cells' threshold crossings, including events accepted or discarded during refractoriness and the reset of drive after firing. Compare each within-run transition with the unchanged model equations and event schedule. This can identify the immediate inputs associated with a crossing and test whether the reconstructed delivery matches the recorded change in drive.

If that points to a specific mechanism, define a targeted intervention and its controls before scheduling more CCR work. Tracing the first difference between the two trajectories would require earlier state information or an additional earlier recording; the current files cannot supply that retrospectively. No new CCR run or causal intervention was started during this analysis. The original eigencircuit interpretation remains limited by the earlier failed full convergence criteria.

Reproduction: `python scripts/pcdr_check_diagnostic.py CCR_diagnostic_results.zip <new-output-directory>`. The checker reads the original upload in `exports/CCR_Diagnostic.zip` and the original completeness table. Compact evidence is in [diagnostic_return](evidence/2026-10-05/diagnostic_return/validation.json); `state_windows.csv` contains per-cell ten-millisecond summaries. The original 1.39-GB archive remains local and unchanged.
