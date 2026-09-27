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

## Follow-up analysis of the existing summaries

Added 27 September after inspecting the first CCR results. These are secondary, post-result calculations, not newly preregistered endpoints. No simulation, mode membership, primary statistic or exclusion rule changed. The added CSVs are mn9_paired_contrasts.csv, paired_seed_orderings.csv and seed_influence.csv in the existing evidence directory.

For each network setting, paired the same 30 seeds and calculated the extra MN9 response from adding MN9 itself to the other-50-cell lesion. At default this is -0.0667 Hz, with a percentile seed-bootstrap interval of -0.3000 to +0.1333 Hz. Across the grid the point estimates range from -0.367 to +0.700 Hz. This supports a small observed incremental effect on this readout, not formal equivalence: no equivalence margin was specified. The saved per-seed MN9 readout is signed and linear, so this contrast can be calculated exactly without the full neuron-level vectors.

Also calculated two additive contrasts. Let D(S) be the signed MN9 rate change for lesion set S versus the shared baseline. The two-part interaction is D(all 51) - D(other 50) - D(MN9). Its default estimate is -1.533 Hz, with interval -3.300 to +0.100 Hz. The all-single-cell contrast is D(all 51) - sum_i D(cell i), with each of the 51 cells included exactly once. The sum of single-cell mean changes is -33.200 Hz, compared with -82.467 Hz for the joint lesion. Their difference is -49.267 Hz, with interval -89.733 to -9.295 Hz. This is exploratory evidence against a simple additive prediction of MN9 from these individual perturbations. It does not identify a particular interacting cell pair, prove biological synergy, establish spatial confinement, or imply that the single-cell effects should be added to predict behavior. The two-part and 51-part contrasts ask different questions, so their differing intervals are not contradictory.

All new intervals use 10,000 multinomial resamples of complete seed rows, random seed 630727, and the 2.5th/97.5th percentiles. Conditions are kept paired within a seed; neurons and conditions are not treated as independent replicates. These are marginal descriptive intervals, with no multiple-comparison correction, p-values or biological-replication claim. The estimates were first inspected interactively; the procedure was then saved and rerun reproducibly. This ordering is recorded rather than presented as prospective.

At default, the mode exceeds each comparator in both per-seed A and per-seed F in all 30 pairs. These counts are descriptive and reuse the same mode trials; they are not 90 independent experiments. At weight 1.2/inhibition 0.8, mode A exceeds comparison 004 and 005 in 29/30 seeds, whereas its aggregate primary A exceeds both. Mode per-seed F exceeds comparison 003 in 27/30 seeds even though the primary F ordering is reversed. This is a concrete reason to preserve the declared averaging order rather than voting across seeds.

The largest seed contributes 93.8 percent of the sum of per-seed total changes for MN9-only at weight 1.2/inhibition 0.8. The corresponding shares are 70.1 percent for mode-without-MN9, 81.3 percent for comparison 004, 73.6 percent for comparison 005, 23.7 percent for the full mode and 3.6 percent for comparison 003. These are influence diagnostics on the sum of seed-level absolute changes, not decompositions of the primary mean-vector footprint. No seed was removed and no new threshold was used to classify a run as invalid. The unusually large responses are spread across different seeds and conditions, so the summary does not support blaming one common input seed for every case.

Within the default mode support, the signed mean-vector changes contain 302.30 summed Hz of increases and 845.37 summed Hz of decreases. Those follow from (absolute sum ± signed sum)/2, with the signed sum equal to 51 times the recorded signed mean. The lesion response is therefore not just uniform suppression within the set. This decomposition applies after seed averaging and says nothing about the number of neurons increasing or decreasing.

One clarification to the initial interpretation: 76.97 percent outside the mode is not a standalone rejection of localization. The selected support is small and no absolute cutoff for F was defined. The relevant primary comparison is A and F against suitable reference sets. Conversely, a higher F than the available comparators does not prove independence. The unresolved comparator imbalance prevents claiming the eigenvector structure has an effect beyond degree, strength, strong synapses and recruitment.

## Paper review and implications for this procedure

Read Pospisil et al., The fly connectome reveals a path to the effectome (2024), especially Fig. 3 and Methods, Simulations to analyse eigencircuits. They use eigenvector loading concentration to propose small populations for study and examine selected circuits dynamically. Their linear eigenmode argument concerns patterns of activity, including the plane spanned by real and imaginary components for complex modes. Our deletion of all outgoing weights from a membership set changes the network operator; it is not stimulation along that eigenvector. Therefore our lesion result is a test inspired by their proposal, not a direct replication or refutation of the eigenmode argument. The 75 percent loading criterion defines a candidate support; it is not a prediction that 75 percent of a lesion response must remain inside it. [Published paper, author repository](https://api.repository.cam.ac.uk/server/api/core/bitstreams/1b44c48c-2482-4148-b4e1-36c36c2c42a4/content), DOI 10.1038/s41586-024-07982-0.

Their supplementary Experimental setting section proposes prioritizing high-loading neurons for perturbation and voltage recording. This supports using the structural mode to choose what to examine next, while keeping the empirical dynamical claim separate from that selection. It does not justify interpreting our lesion footprint as an estimated effectome. [Supplementary information](https://api.repository.cam.ac.uk/server/api/core/bitstreams/decbca11-944c-40a0-9918-e4457570a2fa/content).

Read Shiu et al., A Drosophila computational brain model reveals sensorimotor processing (2024), model construction and Discussion. The model uses connectome-based spiking dynamics with zero basal activity. The authors discuss limits involving transmitter predictions, neuromodulation, morphology and other omitted physiology. This explains why a zero effect under one sugar drive cannot establish general neuronal irrelevance. Their modeled firing readout also should not be described as observed feeding behavior. The parameter-grid exception motivates inspecting baseline and lesion activity before interpreting it as a circuit mechanism; that recommendation is our inference, not a diagnostic supplied by their paper. [Paper](https://www.nature.com/articles/s41586-024-07763-9), DOI 10.1038/s41586-024-07763-9.

Revisited Austin, Balance diagnostics for comparing the distribution of baseline covariates between treatment groups in propensity-score matched samples (2009). It describes checking variance, higher-order distribution features and graphical balance as well as means. The application here is limited: this is a reason to retain our distribution checks, not authority for a fly-specific matching threshold or a causal claim from three optimized comparison sets. More input seeds reduce uncertainty about these sets without repairing their mismatch. [Paper record](https://pubmed.ncbi.nlm.nih.gov/19757444/), DOI 10.1002/sim.3697.

The P/D/C/R question remains open. P has descriptive support from the selected set's responses, but an extra eigenstructure-specific effect is not identified. D and C have not been ruled out because the comparisons do not isolate degree/strength or strong connections. R remains plausible because selection and testing use sugar-evoked participation; the 22 zero-rate-effect cells do not by themselves determine why their lesions are ineffective. These explanations can coexist. There is no reason yet to replace this question with a claim of a confirmed eigencircuit or to call the large-response condition a bifurcation, critical point or numerical failure.

No further simulations are proposed as an immediate action in this update. The existing raw traces and neuron-level rate differences should resolve the next descriptive questions first. If more tests are later chosen, their seed selection, endpoints and decision rules should be recorded separately before execution.

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
