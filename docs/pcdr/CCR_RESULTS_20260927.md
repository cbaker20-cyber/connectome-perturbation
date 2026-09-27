# CCR run, 27 September 2026

## Collected results

The returned bundle contains all 104 planned condition-by-network summaries and 3,120 paired seed readouts. Its design matches the frozen 3,390-job plan exactly. Output hashes match the completed collection record; the 53 reused trial indices match the calibration waves. The CCR smoke certificate passed. The remote collector reports that its trial-file and paired-input checks passed. Locally, source hashes, bundle hashes, coverage, metric identities and signed averages were checked. The underlying neuron-level rates and spikes are still on CCR, so the local audit does not independently reproduce the raw-output checks or bootstrap intervals.

The main result is a larger within-set response for the mode than the three chosen comparison sets, with most of the network change outside the mode. This is not evidence that the 51 cells form an isolated dynamical circuit.

At the default setting:

| Lesioned set | A, Hz | F | Total absolute change, summed Hz | MN9 change, Hz |
| --- | ---: | ---: | ---: | ---: |
| Mode, 51 cells | 22.503 | 0.23029 | 4983.57 | -82.47 |
| Mode without MN9, 50 cells | 21.276 | 0.21378 | 4976.23 | -82.40 |
| MN9 alone | 1.467 | 0.00831 | 176.50 | +1.47 |
| Comparison 003 | 12.078 | 0.19564 | 3148.67 | -4.87 |
| Comparison 004 | 12.540 | 0.20003 | 3197.13 | -4.13 |
| Comparison 005 | 12.486 | 0.19735 | 3226.70 | -5.10 |

A is the mean absolute rate change within the lesion set, calculated after averaging the signed neuron-level changes across seeds. F is the share of total absolute change in that set. For the mode, the recorded seed-bootstrap intervals are A = 22.199–22.832 Hz and F = 0.22899–0.23120. These are conditional simulation intervals, not biological replication or a valid random-control significance test. The comparison sets retain the earlier matching limitations. The mode's off-set share is 76.97 percent.

Removing MN9 from the lesion hardly changes the mean MN9 response at default: the difference is 0.067 Hz. This rules out the narrow explanation that the large MN9 decrease requires directly silencing its own outputs in this condition. The other 50 cells can produce nearly the same MN9 decrease. Outgoing-only silencing does not clamp a cell's spikes. The three lesion sizes and support definitions differ, so their A and F values are not a controlled test of additivity or identical spatial footprints.

Across the nine settings, mode A exceeds each of the three comparisons in all 27 comparisons. Mode F exceeds them in 26 of 27. The exception is overall weight 1.2 and inhibitory multiplier 0.8: mode F is 0.14469, below comparison 003 at 0.17353. The mode's recorded F interval there is wide, 0.10104–0.18455. Do not describe concentration superiority as uniform across the grid or use overlapping/separated individual intervals as a paired significance test. In this setting excitatory weights scale by 1.2 and inhibitory weights by 1.2 × 0.8 = 0.96 relative to default.

![Parameter grid and individual seed responses](evidence/2026-09-27/ccr_results.png)

Some individual seeds at that setting have much larger rate changes than the rest. Comparison 004 at seed 631427 has total absolute change 737,966 summed Hz, against a condition median of 5,839.5. Mode without MN9 at seed 631404 reaches 535,544, versus a median of 7,888.5. MN9-only at seed 631430 reaches 479,264, versus 1,089.5. The mode itself reaches 70,958 at seed 631423, versus 7,882.5. These trials remain included. Their summaries do not tell us whether baseline activity, lesion activity, or both increased, or whether this reflects a numerical or dynamical problem.

The order of averaging matters. At this setting, primary F for mode/comparison 003 is 0.14469/0.17353, whereas averaging the separate per-seed F values gives 0.17568/0.17039. Those are different estimands; the second cannot replace the first to recover the desired ordering. Paired uncertainty for the primary contrast requires neuron-level deltas, which are not in this summary bundle.

At default, 22 of the 51 individual lesions have exactly zero total rate change in every one of the 30 paired seeds. Their F is undefined, not zero. This establishes rate invariance for those perturbations and trials, not identical spike timing or absence of a biological role. The other 29 have a nonzero rate effect in at least one seed. The largest single-cell whole-network changes are:

| Neuron ID | Total absolute change, summed Hz | MN9 change, Hz |
| --- | ---: | ---: |
| 720575940615041430 | 2196.97 | +20.93 |
| 720575940607272649 | 2028.33 | -14.80 |
| 720575940623211725 | 1935.53 | -25.33 |
| 720575940643867296 | 1898.63 | +0.30 |

This ranking describes total response magnitude, not proof that these cells account for the combined lesion. Full individual results, all 27 mode comparisons and every condition's per-seed range are in the evidence directory. Single-cell A measures change in that one cell's firing; it should not be used alone to rank its influence on other neurons.

## What to examine next

Before more simulations, inspect the saved baseline and lesion activity at weight 1.2/inhibition 0.8. Export total spikes, recruited-neuron counts, maximum cell rate and a population spike-count trace in fixed 10 ms bins for all 210 trials at that setting, not just the largest responses. Check time-step and refractory-rate consistency, input pairing and output hashes. Compare the same summaries at default. This is a post-result diagnostic, not an alteration of the completed study. Do not discard the large-response seeds.

Then export neuron-level paired rate changes to compare the full mode, mode without MN9, MN9 alone and individual lesions on the same fixed 51-cell support and the same full-neuron universe. This makes spatial overlap and non-additivity assessable; the current scalar summaries cannot resolve them. A compact sparse table can retain exact zero changes implicitly with a recorded full-neuron universe. Use all 30 seeds and retain condition-specific primary A/F alongside any added fixed-support readouts.

Only after those checks should a new simulation protocol specify held-out seeds, duration or time-step sensitivity. The current evidence motivates a narrower question: how reproducible and spatially confined is this selected mode's perturbation response across model operating conditions? It does not yet validate a structural eigenmode as a biological causal circuit. Pospisil et al. distinguish anatomical connectivity from causal effects and propose perturbation-based effectome estimation ([Nature, 2024](https://www.nature.com/articles/s41586-024-07982-0)). Shiu et al. provide the connectome-based integrate-and-fire sensorimotor model ([paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC11446845/)). These motivate the checks; neither paper supplies a justification for ignoring our comparison-set imbalance or selecting favorable seeds.

CCR selected 24 workers. The interval from its capacity certificate to the final controller update was 2 hours 14 minutes 5 seconds, excluding setup and earlier calibration. Collection took 19 minutes 54 seconds. These measurements support reserving analysis time and automatically chaining collection after the controller completes in a future notebook; they do not guarantee identical runtime on another allocation.

## Earlier execution audit and analysis plan

The following was recorded before the results bundle arrived and is retained as the analysis history.

The downloaded controller records report all 3,390 planned indices complete, with no missing or duplicate indices. There were 3,337 new worker processes, all with exit code zero and no timeout, and 53 reused trials. The controller log contains the complete sequence from 1 through 3,390 without other messages. The last progress update was 05:26:30 UTC, or 1:26:30 a.m. Eastern. This is the controller's completion record, not the time the user saw the disconnected notebook.

Fresh workers took a median 58.57 seconds, with a range of 44.14 to 78.85 seconds. Their summed durations are overlapping worker wall times, not the duration of the study or measured CPU usage. These two files do not establish the selected worker count or when the controller started.

The original downloads remain under results/pcdr/results_ccr_20260927. Their SHA256 hashes and the status audit are in evidence/2026-09-27/controller_audit.json. The audit checked index coverage, each fresh worker's command index and exit status, timeouts, and the controller's numbered completion sequence. This is execution evidence. It does not independently verify the trial files or establish an eigencircuit effect.

## Collection before interpretation

Use a new CCR Jupyter allocation for collection only; an initial request of four cores, 16000 MB and two hours is reasonable but has not been benchmarked for this collector. Open the existing notebook in /user/cbaker4/connectome and run its first two setup cells with the saved Python-module configuration and MPLBACKEND=Agg fix. Keep all simulation files and package pins unchanged. Do not run the study launch cell. The collection command is the existing pcdr_ccr_sensitivity.py collect action on results/expanded_sensitivity.

The collector requires the prepared environment and source/data fingerprints, checks all trial output hashes and rate tables against spikes, and checks baseline/lesion input pairing before computing descriptive summaries. If a lock or provenance error appears, investigate it rather than deleting locks or relaxing validation. Successful collection produces results.json and per_seed.csv. Retrieve those with jobs.json, capacity.json, the smoke certificate, installed library list and controller records. Retain the underlying trials on CCR.

## Analysis order

Keep the frozen 3,390-job design. First verify the nine parameter settings, 30 seeds, condition memberships and expected 104 condition-by-network summaries and 3,120 per-seed comparisons. Check the all-neuron rate universe, own-network baselines and input pairing before interpreting any effect.

Then describe the 51-cell mode's footprint at the default setting and its paired differences from each of the three existing comparison sets. Report A (mean absolute change within the lesioned set), F (fraction of total absolute change within that set), total change and off-set change together. A high within-set change is not by itself evidence of confinement.

Compare the full mode with mode-without-MN9 and MN9 alone, then examine all 51 individual lesions at the default setting. Do not treat individual effects as additive. If neuron-level combined-versus-single comparisons are needed, calculate them from retained rate tables under a recorded analysis procedure; aggregate A and F alone do not establish interaction or synergy.

Report every setting in the full 3 by 3 parameter grid, including reversals or weak responses. Do not choose a new mode, remove a comparator or select a favorable setting based on these outcomes. Bootstrap intervals describe variation across simulated input seeds for this model. The optimized comparison sets do not support random-reference p-values or claims of biological replication. Decide further experiments only after this collection and review.

This note and the audit were prepared with Codex assistance. Scientific outcomes have not yet been supplied or analyzed.
