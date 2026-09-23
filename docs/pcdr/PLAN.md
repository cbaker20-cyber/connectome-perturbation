# P/D/C/R study

Latest outcome, 22 September 2026: the separately declared motor-composition pilot completed and verified 55 trials using all nine feasible sets and five fresh seeds. The eigen-set exceeded every comparator on both A and F, conditional on those fixed sets. A post-result full-output audit found only three distinct five-seed response patterns among the nine memberships, with silent-cell substitutions within each group. Distributional imbalance, overlap and unmatched MN9 identity remain. See MOTOR_COMPOSITION_RESULTS_20260922.md; this does not complete the historical random-reference confirmation.

Current-status addendum, 22 September 2026: the original six-feature pooled-SMD criterion with added exact annotated motor/sign/recruitment counts is now feasible for the selected exploratory mode. Nine binary sets passed independent verification after two bounded LP diagnostics and exhaustive completion of seven fractional entries. This is a baseline-only design result, not new lesion evidence or a calibrated reference ensemble. See FULLPOOL_FEASIBILITY_20260922.md for the recorded follow-up method, limitations and proposed composition sensitivity. The dated protocol below remains historical; its original random-reference confirmation has not been completed.

Recorded 18 September 2026. This is a working research protocol and source record, not an STS research report.

## Question

Do concentrated eigenvector supports of the materialization-630 Shiu matrix predict localized firing-rate responses to output lesions, beyond connectivity, strong connections, and recruitment?

- P: eigen-defined sets have an additional localized response.
- D: degree and synaptic strength account for the response.
- C: concentrated strong connections account for the response.
- R: participation under the sensory drive accounts for the response.
- These explanations can overlap. Failure to reject a comparison does not prove an alternative explanation.
- The response is simulated firing. It is not feeding, grooming, an in-vivo effectome, or direct evidence about behavior.

## Where the procedure came from

The user reports that James and Dr. Muldoon suggested a slower sequence: pairwise spike correlations, a sorted matrix, clustering, and individual E/I lesions. The implementation keeps that sequence. The exact bin widths, clustering cut, sampling algorithm, seed lists, statistical definitions, and numerical checks below are choices made during this review; they are not attributed to the meeting.

### Notes on Pospisil et al. 2024

- [The fly connectome reveals a path to the effectome](https://pmc.ncbi.nlm.nih.gov/articles/PMC11446844/), Nature 634:201–209. DOI: 10.1038/s41586-024-07982-0.
- Their sparse eigenvector supports motivate the perturbation sets.
- They did simulate dynamical models. The question is not whether anyone has ever simulated these ideas.
- Their proposed circuits are hypotheses about dynamics, not measured effectome eigenvectors.
- Their paper uses v783, including a stated less-than-five-synapse cutoff and a different transmitter-sign convention. Their public preprocessing script does not visibly apply that cutoff; its input file could already have been processed. That is an unresolved paper/code provenance difference, not proof the authors made an error.
- [Author preprocessing code](https://github.com/dp4846/conn2eff/blob/master/data/connectome_data.py).
- Here, compute modes from the exact signed count matrix used by the 630 LIF. Multiplying the whole matrix by 0.275 mV changes eigenvalues, not its eigenvectors. These are not the Jacobian eigenvectors of the spiking simulator.

### Notes on Shiu et al. 2024

- [A Drosophila computational brain model reveals sensorimotor processing](https://pmc.ncbi.nlm.nih.gov/articles/PMC11446845/), Nature 634:210–219. DOI: 10.1038/s41586-024-07763-9.
- Supplies the LIF model and sensorimotor setting.
- Zero basal firing motivates checking recruitment. The undriven condition is a sanity check on an assumption, not a new biological finding.
- Sensory drive can recruit inhibitory cells. Zero basal firing does not prohibit all disinhibition in a driven network.
- Preserve the local model equations, thresholds, delays, refractory periods, and outgoing-only silence operation.
- The original reset statement includes a local `w = 0`. A small runtime check did not find that it erased synaptic weights. Do not rewrite the model just because a static audit flags that string.

### Notes on degree and strong connections

- [Tu et al. 2018](https://doi.org/10.1016/j.neuroimage.2018.04.010), NeuroImage 176:83–91, motivates matched connectivity controls. It concerns brain controllability; it does not establish that fly eigencircuits are hubs.
- [Currier & Clandinin 2025](https://pubmed.ncbi.nlm.nih.gov/40460825/), Cell 188:4366–4381.e14, motivates examining strong inputs using evidence from visual physiology. DOI: 10.1016/j.cell.2025.05.007.
- The exact 5% threshold was supplied in the proposed protocol. This review verified the paper's broader strong-input finding, but did not verify the threshold against accessible full text. It is recorded here as a protocol-defined cutoff, not a universal biological boundary or a direct quotation of their methods.
- Strong means absolute connection weight divided by the sum of absolute incoming weights of the postsynaptic cell in this model. Keep the original sign. This denominator is the modeled graph, not an independently measured total physiological input.
- Jaccard overlap with hubs or another support is descriptive. No 0.7 or 0.4 overlap cutoff decides among P/D/C/R.

### Notes on functional clustering

- [Feldt et al. 2009](https://pmc.ncbi.nlm.nih.gov/articles/PMC2814878/), Functional clustering algorithm for the analysis of dynamic network data, motivates treating temporal similarity and surrogate comparisons explicitly.
- [Feldt Muldoon et al. 2013](https://pubmed.ncbi.nlm.nih.gov/23401510/), PNAS 110:3567–3572, DOI: 10.1073/pnas.1216958110, applies functional clustering in epileptic mouse hippocampal networks.
- Our Pearson/average-linkage analysis is not an exact implementation of that published algorithm. The simulated fly groups are called functional clusters under sugar, not cortical subcircuits.
- A correlation block may reflect common drive, rate differences, or timing. It does not establish an anatomical or causal circuit.

## Fixed local procedure

- Materialization 630; 127,400 modeled neurons. W[post, pre] is the signed synapse-count matrix.
- Root IDs remain strings in stored tables. Integer matrix indices are separate.
- Input: the existing 21 sugar IDs, Poisson rate 150 Hz. Duration 1 s; dt 0.1 ms.
- Selection seeds: 630101–630105. Replay and no-input checks use 630101.
- One worker; a shared two-hour deadline across development and final validation pilots. Preserve completed trials and all superseded outputs.
- Count every declared trial, including a trial with no events. All modeled neurons stay in rate tables even without an annotation.
- Record actual delivered input events using voltage measurements immediately before and after Brian2's synapses scheduling slot. Recurrent synapses change g; the Poisson inputs change v. Check integer multiples of the fixed input jump.
- Correlation: 10 ms counts, excluding directly stimulated cells and constant rows. Preserve trial boundaries in a neuron × trial × bin array. Concatenate bins only for the zero-lag Pearson calculation; never form lagged pairs across trial boundaries.
- Average linkage on 1-r; provisional cut 0.7. Save original and reordered matrices, ordering, linkage, groups, and dendrograms. Singletons count as groups.
- Sensitivities: 5 and 20 ms; minimum five pooled spikes. These are descriptive comparisons, not tuning steps that choose the most favorable picture.
- Surrogates: 99 independent within-trial circular shifts and 99 per-neuron trial shuffles, seed 630400. Recluster each surrogate and save within-group correlation. Repeated stimulus timing survives the trial shuffle. Neither surrogate proves anatomical independence.
- Split the five trials into two and three; compare labels only for cells with variable counts in both halves using adjusted Rand index. Do not call unstable groupings established circuits.
- Select ten E and ten I cells before examining their lesion responses, seed 630500. Both transmitter label maps and the actual model sign must agree; prefer ACh/GABA. Require activity in at least three of five trials. Randomized round-robin over cluster/rate-tertile strata distributes selections. Tertiles are computed among eligible cells of each polarity, not among all 127,400 neurons.
- Add up to two recruited cells outside selected groups and one baseline-silent inhibitory cell. If outside-group candidates are unavailable, record that instead of substituting a different definition.
- Locally test the first selected E and I with seed 630101. One pair verifies the path; no p-value or interval is reported for that pair.

## CCR stages

### Individual lesions

- Thirty new seeds, 630201–630230, separate from selection.
- Full baseline plus every frozen individual lesion, with common input seeds and matching input-event digests.
- Analyze all twenty E/I cells before the mode-lesion study. Two-sided paired sign-flip tests describe MN9 and total motor responses; BH adjusts the complete 40-test E/I family. The auxiliary comparison cells stay diagnostic.
- A seed is a stochastic simulation replicate. Neurons, bins, and shared seeds are not independent biological samples.

### Mode selection

- Start with 40 eigenpairs, increasing to 80 only if needed for 20 complete distinct real/conjugate modes.
- ARPACK: largest magnitude, tolerance 1e-9, maxiter 10,000, recorded seeded start vectors 630300 and 630301. Require relative residual below 1e-6.
- Sort squared complex magnitudes and keep the smallest prefix carrying 75% of power. Keep complex components. Stable ordering breaks exact loading ties.
- Match the two solutions by eigenvalue. Numerical acceptance requires the same support and phase-invariant vector overlap >0.999; eigenvalue separation <1e-6 relative flags a near-degenerate mode. These are numerical checks, not biological effect thresholds.
- Consider the first 20 stable complete modes in spectral order, after excluding incomplete pairs and unstable bases. Exclude supports with fewer than ten cells having at least five baseline spikes, and supports containing a directly stimulated sugar neuron. Do not remove inputs from an eigen-support to make it eligible.
- The input-containing exclusion is an implementation clarification: the trial runner excludes direct sensory lesions, and comparing them against controls that exclude sensory neurons would be unfair.
- Pick greatest loading power on any baseline-recruited neuron; break ties by eigenvalue magnitude, then recorded rank. If none qualifies, report no eligible mode under this protocol.

### Matched controls

- Five degree/strength sets for a descriptive pilot. For confirmation, 199 distinct sets matched additionally for sign, recruitment, baseline rate, and strong outgoing mass.
- Continuous variables: log1p incoming/outgoing degree and strength; add baseline Hz and strong outgoing mass for full matching.
- Exact counts of sign/recruitment strata and exact set size. No repeated neuron within a set. Exclude the focal set and the 21 inputs.
- Randomized nearest-64 proposals within strata, with probabilities proportional to exp(-distance). Accept only standardized mean differences <=0.1 on every continuous variable. Limit 50,000 attempts and report failure if too few sets qualify.
- The reference distribution depends on this proposal/matching model. It is not uniform sampling of all possible sets, nor a randomized biological experiment.
- Save every accepted set, its balance, and overlap between sets.

### Outcomes

- For each neuron, first average its paired lesion-minus-baseline rate over seeds. Then take absolute values.
- A = mean absolute change within the set.
- F = absolute change within the set / absolute change across the whole model.
- Score each control on its own support. Zero total response gives undefined F and cannot support P.
- Primary test requires superiority on both A and F. Compute upper-tail reference comparisons using (1 + number of controls at least as large)/(1 + number of controls). Use the larger p-value for the conjunction.
- [Phipson & Smyth 2010](https://pubmed.ncbi.nlm.nih.gov/21044043/) motivates retaining the Monte Carlo correction. Five controls have minimum p=1/6; 199 have minimum p=1/200. Neither n=30 nor this p-value resolution guarantees power.
- Paired-seed bootstrap: 2,000 resamples, seed 630700. Resample whole trial pairs, not neurons. Report undefined-concentration replicates.
- MN9 and total/per-neuron motor firing are secondary. These mean-rate endpoints can miss effects on timing or oscillation phase.

### Sensitivity and compute

- Benchmark NumPy against Cython on CCR before enabling a compiled backend. Check replay, no-input silence, common input, and output distributions; save both runtimes.
- Benchmark seeds 630801–630830. Numerical acceptance uses a 90% confidence interval for the backend mean difference within predefined margins: MN9 and lesion MN9 delta, max(5 Hz, 10% of NumPy mean magnitude); total motor, max(10 Hz, 10%); input event count, 5%. These are numerical tolerances, not scientific equivalence claims.
- Keep NumPy if compilation or validation fails. Do not change biological parameters to improve a benchmark.
- Each array index is one condition/seed. No nested workers. Jobs have separate directories, locks, source/data hashes, and atomic completion manifests. Missing jobs prevent confirmation analysis.
- Default primary mode study: 6,030 trials including its shared baseline. Prepare timing estimates before dispatch. Account, partition, available concurrency and node limits are cluster settings to supply on CCR, not guessed local values.
- After confirmation, examine fixed supports at I:E 0.5/1/1.5, recurrent global weight 0.7/1/1.3, and the 5% strong-only graph. Each graph gets its own baseline. External input jump/rate remain fixed. This implemented sensitivity stage is descriptive and does not reuse the primary matched-reference p-value.
- Global suppression after pruning is not specific evidence for C. JO is a later extension.

## Recordkeeping

- New code, corrections, commands, output paths and limitations go into LAB_NOTEBOOK.md. CODE_GUIDE.md explains the program separately from the source.
- Every completed trial contains the relevant code archive, environment, seed, hashes, spikes, scheduled and delivered inputs, and all-neuron counts/rates.
- Actual code assistance is recorded. Do not invent reading dates, meeting quotations, or a first-person discovery history.
- These are research support materials. The student's STS report remains their own writing. [STS requirements](https://www.societyforscience.org/regeneron-sts/application-requirements/) and [2027 report guidelines](https://sspcdn.blob.core.windows.net/files/Documents/SEP/STS/2027/Application/Research-Report-Guidelines.pdf).
# Amendment recorded 19 September 2026: paired external input

- The original NumPy PoissonInput draws random numbers only for voltage writes allowed by the refractory mask. Inspected the generated Brian2 2.9.0 code: the binomial function receives indices filtered by `not_refractory`.
- A feedback-dependent change in a sugar neuron's firing can therefore shift the later random sequence. Equal seeds alone did not give equal stimulation in the first whole-brain lesion check. That comparison is excluded from paired interpretation.
- New protocol `fixed_binomial_tape_v1`: generate all independent N=1 Bernoulli draws before simulation, with probability 150 Hz × 0.0001 s = 0.015 per input per step. Save the schedule and use it for both members of each seed pair. This has the original stepwise input distribution but a different mapping from seeds to events.
- Retain voltage refractory gating, zero refractory-period parameter for sugar targets, jump amplitude, scheduling slot, recurrent equations, connectivity and output-only silencing. Save delivered voltage jumps separately. Identical scheduled events are required; state-dependent delivered jumps need not be identical.
- Regenerate selection baselines and freeze a new selection before viewing corrected lesion effects. Historical selections and the failed comparison remain available.
- This is a common-input coupling amendment, not evidence for P, D, C or R. It does not claim bitwise reproduction of the original PoissonInput trajectories. [Brian2 PoissonInput documentation](https://brian2.readthedocs.io/en/stable/reference/brian2.input.poissoninput.PoissonInput.html) describes independent per-step inputs generated during the run; the installed 2.9.0 generated code supplies the specific masking evidence.
- The original two-hour window expired. The user explicitly authorized up to 30 additional minutes on 19 September for the corrected pilot. A separate manifest records that deadline; it does not reset the old run's deadline.

## Local extension authorized 20 September 2026

- CCR is unavailable. The user authorized approximately thirty hours of small serial local batches through Monday night. Run the frozen 720-job single-cell study locally, with one simulation process and its unchanged thirty-seed design.
- After singles, attempt one resource-bounded mode pilot: five strict fully matched controls, five fresh seeds 630901–630905, 35 trials including baseline. This is exploratory; it neither replaces nor satisfies the 199-control/30-seed confirmation.
- Keep the mode selection, matching balance and exclusion criteria. Stop a stage on numerical failure, no eligible mode, insufficient matches, or time/resource limits; record the reason instead of relaxing it.
- On 20 September the user delegated the endpoint choice after requesting a comparison. Retain localization (A and F jointly) as primary because the question concerns prediction of lesion footprints. MN9 and total/per-neuron motor ΔHz remain secondary. This decision precedes all mode-lesion results and does not change the frozen single-cell execution.
- Independent Python controllers execute and write findings without model calls. An hourly Codex follow-up adds supervision. The full decision record is [PROCESS_DETAILS.md](PROCESS_DETAILS.md).
