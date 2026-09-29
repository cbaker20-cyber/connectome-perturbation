# Detailed preparation for the meeting with James and Dr. Muldoon

Current through 29 September 2026. This is a personal explanation guide, with possible questions rather than questions attributed to either adviser. The [short guide](EXPLAINING_THE_STUDY.md) is the starting point; the [experiment overview](RESEARCH_OVERVIEW.md) gives the full sequence. No new simulation was performed to write this guide.

## The result to lead with

The study found one exploratory structural candidate whose simulated lesion response reproduces across fresh input seeds. In the separate 30-seed replication, the selected 51-cell set had an average absolute mean-rate change of 22.544 Hz per member and contained 23.12% of the whole-network absolute mean response. Both measurements exceeded the five fixed comparison sets. However, the comparisons differ in relevant properties and overlap substantially, so this does not yet establish an additional effect of eigenmode membership. Most of the response remains outside the set.

This is a useful preliminary result because the response is reproducible and the main obstacles are now specific: comparison design, dependence on the support definition, and numerical sensitivity under an altered parameter setting. It is not a completed confirmation. The separate [replication report](SEED_REPLICATION_RESULTS_20260922.md) contains every set's estimate and conditional uncertainty interval.

## What exactly is the hypothesis?

The scientific question is whether a small set identified from a connectivity eigenvector predicts the spatial distribution of a simulated lesion response better than connectivity summaries and baseline participation alone. Here, spatial means membership in neuron sets; the primary measurements do not measure physical distance in the brain.

The original P/D/C/R labels organize explanations. P is additional predictive information from eigenmode membership; D is degree and synaptic strength; C is concentrated strong connections; R is participation under the stimulus. These explanations can coexist. A mode may recruit strongly because of its connectivity, and those same features may explain its lesion response. A positive contrast against imperfect comparisons does not identify which explanation is responsible. [Original question and definitions](PLAN.md#question).

The narrower claim currently supported is about a fixed set, model and input: this set produces a reproducible response that is more concentrated on its own members than the particular comparisons tested. The broader claim about eigenmode-specific organization remains open.

## What is an eigenmode here?

The signed connectivity matrix uses W[post, pre]: column j describes outgoing connections from neuron j, and row i describes incoming connections to neuron i. Entries are signed synapse counts. The structural calculation solves Wv = lambda v for right eigenvectors. A right eigenvector is a pattern whose image under this linear map retains the same direction, up to its eigenvalue.

Our W is directed and signed. It is not assumed symmetric, and its eigenvectors need not be orthogonal. An individual loading is a mathematical coefficient, not the cell's firing rate or transmitter label. The four eligible candidates have complex eigenvalues. Because W is real, conjugate eigenpairs represent a paired real subspace; they are not counted as two separate candidates. Squared magnitude preserves the real and imaginary contributions when assigning membership. Raw eigenvalues of a signed-count matrix are not frequencies in Hz.

The important gap is between structural linear algebra and the simulator. Thresholds, resets, delays, refractory behavior and external drive make the spiking dynamics different from repeated multiplication by W. Removing columns of W is also not the same intervention as stimulating a pattern proportional to v. The spectral calculation proposes a set to test; it does not prove what its lesion will do. [Structural implementation](../../eigencircuits/build_modes.py), [exploratory implementation](../../scripts/pcdr_modes_exploratory80.py).

## What comes from the papers, and what is specific to this project?

Pospisil et al. motivate selecting sparse structural modes for dynamical investigation and use 75% of loading power to define supports. Our outgoing-lesion experiment tests a different intervention; it does not estimate their experimental effectome. Their 75% loading-power convention is also distinct from their example reporting 75% of synapses in one neuropil. The preceding overview did not clearly acknowledge the loading-power precedent; that omission has been corrected. [Pospisil et al., Fig. 3f–g and Methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC11446844/).

Shiu et al. provide the connectome-based integrate-and-fire model and experimentally test selected sensorimotor predictions. Those validations motivate using the model, but do not independently validate our selected support, altered weights or response-localization hypothesis. [Shiu et al.](https://doi.org/10.1038/s41586-024-07763-9).

Our contribution so far is this particular structural selection, lesion comparison and verification sequence. Novelty across the literature has not been established by a comprehensive search. Do not describe either published approach as having been disproved by our results.

## What is a support, and why 75%?

For each cell, calculate p_i = |v_i| squared divided by the sum of all squared magnitudes. Sort cells by descending p_i and retain the shortest prefix whose sum reaches 0.75. Stable sorting resolves exact ties. Because membership is discrete, retained power can slightly exceed 75%; the selected set contains approximately 75.22%.

This is a literature-supported convention for describing a concentrated vector, not a demonstrated biological boundary. A cell just outside the cutoff may still matter. It also does not predict that 75% of the lesion response will remain inside. Loading power describes the eigenvector; F describes a simulated response. [Support code](../../eigencircuits/build_modes.py), [candidate review](RESEARCH_OVERVIEW.md#8-candidate-review-for-the-meeting-29-september).

## How was the candidate chosen, and was that exploratory?

The original search returned 22 stable complete modes from 40 eigenpairs. None of the first 20 had baseline-spiking cells in its 75% support. The original eligibility procedure therefore returned no candidate. This is a result under the sugar-input protocol, not evidence that these structural modes never function.

A separately recorded exploratory amendment expanded the calculation to 80 eigenpairs and considered the first 40 stable complete modes. Eligibility required at least ten support cells with at least five pooled spikes across the five selection trials, and no directly stimulated sugar cell in the support. The rule did not remove inconvenient sensory members to make a mode qualify. Among eligible modes, selection favored the greatest whole-vector loading power on any baseline-active cells, then eigenvalue magnitude and rank.

This selected rank 33, using zero-based indexing. Selection depended on original baseline activity but preceded its lesion outcomes. Thus it was not chosen because its lesion result was largest. Nevertheless, the deeper search was undertaken after the original screen failed, so it remains exploratory. The [original amendment](../../results/pcdr/exploratory80_20260921/amendment.json) records that distinction.

## What are the four candidates?

| Zero-based rank | Support size | At least one pooled spike | At least five pooled spikes | Active in all five selection trials | Whole-vector recruited power |
| --- | ---: | ---: | ---: | ---: | ---: |
| 32 | 819 | 17 | 17 | 13 | 1.117% |
| 33, selected | 51 | 29 | 29 | 28 | 53.794% |
| 35 | 813 | 28 | 27 | 22 | 3.324% |
| 39 | 724 | 16 | 15 | 13 | 3.032% |

Whole-vector recruited power sums loadings over every baseline-active cell, including cells outside the support. It is not the proportion of support members that fired. The selected candidate's unusually high recruited power explains why the rule selected it; it is not independent confirmation of the hypothesis being tested.

The selected support has 26 model-excitatory and 25 model-inhibitory cells, 13 annotated motor cells and nine missing superclass labels. Missing annotations remain missing, rather than becoming an inferred biological category. It shares no support cells with ranks 32 or 39 and three with rank 35. In contrast, ranks 32 and 35 share 506 cells. Four eligible modes are not four independent neuron groups.

The other three candidates have not undergone this candidate-lesion comparison series. No claim is available about their comparative A/F or biological roles. Their larger sizes and lower recruitment also mean that simply lesioning them would not make them appropriately matched controls. [All candidate measurements](evidence/2026-09-29/candidate_review/candidates.csv), [overlap table](evidence/2026-09-29/candidate_review/overlap.csv).

## How sensitive is this choice?

The latest retrospective review examined all forty screened modes under nine combinations: 50%, 75% or 90% support, with one, five or ten pooled spikes as the qualifying threshold. It retained the ten-cell requirement and sensory exclusion. At 75%, the same four candidates qualify for every tested spike threshold. At 90%, more qualify, but rank 33 remains selected.

At 50%, none qualifies. Rank 33 then contains fifteen cells, with nine meeting the original five-spike criterion, below the required ten. Its 90% support contains 140 cells, with 63 meeting that criterion. The result supports robustness to these recruitment-threshold changes at 75%, but not independence from the support convention. There are no lesion outcomes for the fifteen- or 140-cell versions. [All 360 rows](evidence/2026-09-29/candidate_review/sensitivity.csv).

Numerical checks are another issue. The original solver used different seeded starting vectors, residual checks, phase-invariant vector comparison, exact support agreement and a near-degeneracy check. The latest review independently multiplied the saved four candidate vectors by the hash-matched matrix and found residuals around 1e-15 to 1e-14. Small residuals verify approximate eigenpairs of that matrix. They do not establish robustness to anatomical errors, neurotransmitter uncertainty or changing the network. No new solver-start or noisy-connectome study was performed in this review. [Review protocol and limits](evidence/2026-09-29/candidate_review/protocol.json).

## What does a simulation actually do?

The materialization-630 model contains 127400 modeled neurons. Twenty-one sugar-input neurons receive stimulation at a nominal 150 Hz for a one-second trial. The original time step is 0.1 ms. These parameters specify the experiment; they do not represent every sensory condition or physiological state.

The implemented subthreshold equations are dv/dt = (v_0 - v + g)/20 ms and dg/dt = -g/5 ms, both with refractory gating. Rest/reset voltage is -52 mV, threshold is strictly above -45 mV, refractory duration is 2.2 ms, and recurrent delay is 1.8 ms. A recurrent presynaptic spike adds its signed weight to the target's g. The base weight is 0.275 mV per signed synapse-count unit. Despite its name, g has voltage units here; it is not a measured conductance or a current in amperes. [Actual parameters and equations](../../model.py), [trial implementation](../../eigencircuits/trials.py).

The lesion sets selected outgoing weights to zero. It does not delete the selected neurons, prevent them from receiving input or clamp their firing. This matters especially for MN9: including it in a lesion does not mechanically set its rate to zero. Its response can still change through altered recurrent activity.

## Why were paired input events necessary?

Using the same random seed originally failed to produce identical input events in baseline and lesion. Conditional simulation behavior affected random-number consumption. The corrected procedure generates the external schedule before simulation and uses that same schedule in both conditions. The original stepwise distribution uses probability 150 × 0.0001 = 0.015 per input per clock tick. This is a fixed discrete-time approximation, not a claim of reproducing every old random stream.

Actual delivered voltage jumps are recorded separately because delivery can depend on state. An identical schedule is the pairing requirement; equal delivered records are additionally checked where relevant. The correction was followed by new selection baselines, and the earlier mismatched pairs were retained as failed evidence rather than analyzed as valid paired effects. [Correction history](PLAN.md#amendment-recorded-19-september-2026-paired-external-input), [notebook](LAB_NOTEBOOK.md).

For time-step follow-ups, the same physical input schedule is preserved. This isolates a numerical comparison conditional on that schedule. It is not a separate convergence study of every possible input-generation discretization.

## What exactly do A and F measure?

For neuron i and paired seed s, let d_is be lesion firing rate minus baseline firing rate. Calculate dbar_i by averaging these signed differences across seeds. If S is the selected set, define I = sum over i in S of |dbar_i|, and T = sum over all modeled neurons of |dbar_i|. Then A = I/|S| and F = I/T. If T is zero, F is undefined. [Implementation](../../eigencircuits/readouts.py).

A is measured in Hz per set member. It is not the fraction of neurons affected, and an A of 22.544 does not mean every member changes by that amount. F is a response fraction, not a probability or accuracy score. The complement 1-F is the off-support fraction. A and F share I, so they are related summaries rather than independent confirmations.

The order of operations matters. As an illustrative example, a neuron changing by +10 Hz in one seed and -10 Hz in another contributes zero to |dbar|, although its average absolute single-seed change is 10 Hz. The declared endpoint measures the average signed effect's footprint; it is not the typical magnitude of every single-trial disturbance. Changing that endpoint now would require a separate analysis.

Each comparison set is scored on its own support. Component-lesion comparisons also report common-support scores when comparing full51 with active29; otherwise a denominator change could make A look different for purely arithmetic reasons. The current measures include directly lesioned cells. They do not alone establish a selective effect on unlesioned downstream cells.

## How large is the result, and what is the uncertainty?

| Separate study | Mode A, Hz | Mode F | Purpose |
| --- | ---: | ---: | --- |
| Five-seed optimized pilot | 22.576 | 0.2294 | Initial descriptive comparison |
| Thirty fresh-seed replication | 22.544 | 0.2312 | Reproduce the fixed-set response under new input realizations |
| Default CCR setting, 0.1 ms | 22.50327 | 0.230290 | Broader parameter/component study |
| Default finer-step study, 0.05 ms | 22.28235 | 0.230280 | Numerical sensitivity |
| Default finer-step study, 0.025 ms | 22.30915 | 0.230822 | Numerical sensitivity |

Do not pool these rows as five independent experiments: some follow-ups deliberately reuse inputs and memberships. The replication's bootstrap 95% intervals are 22.233–22.816 Hz for A and 0.2293–0.2327 for F, conditional on these sets and the model. Whole paired seeds are resampled. These intervals do not include uncertainty in anatomy, model parameters, candidate selection or comparison quality. [Replication](SEED_REPLICATION_RESULTS_20260922.md), [finer-step results](CCR_RESULTS_20260927.md#completed-530-trial-time-step-comparison).

F around 0.23 indicates concentration relative to these comparisons, not circuit independence. Comparing 51/127400 with 0.23 would make a striking descriptive ratio, but uniform response across all modeled neurons is not the relevant null: many cells are silent and connectivity is highly uneven. Such a ratio would not replace matched comparisons.

## Why isn't the result already a confirmation?

The original matching sampler found no accepted sets after 50000 proposals. A later optimization found sets meeting the declared mean-balance rules. That established feasibility under those rules, not a justified random reference distribution. The five optimized pilot sets share 31–37 cells with one another. Their motor counts are 5, 4, 3, 3 and 4 versus 13 in the mode, and all exclude MN9 while the mode contains it. [Matching audit](MATCHING_AUDIT_20260921.md), [pilot limitations](OPTIMIZED_PILOT_RESULTS_20260921.md).

The motor-composition follow-up used nine sets with matching motor counts and other specified strata. They share 47 cells across all nine, and only three distinct observed response patterns resulted. Incoming-degree spread remained very different despite small standardized mean differences. The largest log1p incoming-degree variance ratio in that audit was 19.117. A small mean difference does not imply the distributions coincide. [Distribution audit](MOTOR_SET_AUDIT_20260922.md).

Austin's methodological paper supports examining distributions beyond their means, but does not provide a fly-specific threshold or make this comparison causal. [Austin 2009](https://pubmed.ncbi.nlm.nih.gov/19757444/).

The eligible pool creates a concrete design constraint: all eight eligible active excitatory motor alternatives are required by the current strata. Three active inhibitory motor alternatives must come from a pool of four. Hence only four active motor memberships are available under those constraints, before imposing the remaining matching requirements. Generating thousands more nominally matched sets cannot remove that constraint. [Pool review](CCR_RESULTS_20260927.md#local-event-and-comparator-review).

Fresh seeds address variability in stochastic input; they do not fix comparison bias. The planned 199-reference confirmation has not been performed, and no calibrated random-reference p-value is claimed for the optimized comparisons. Five valid random references would in any case give a minimum plus-one empirical p-value of 1/6; having optimized references presents a separate validity problem beyond that resolution limit.

## What happened to James's correlation and single-cell sequence?

The study followed correlation matrices, reordered displays, provisional clustering and individual excitatory/inhibitory lesions before the mode comparison. Correlations used binned activity, with bin-width, shuffle and split-trial checks. Clusters depended on bin width and were not treated as established anatomical circuits. The four eligible eigenmodes refer to support/recruitment criteria, not four matches to those clusters. [Original sequence](PLAN.md#fixed-local-procedure).

The 720 individual-cell trials included baseline and 23 lesion conditions across thirty seeds. One of forty adjusted secondary tests passed the recorded BH threshold: a selected excitatory cell's total motor response. No MN9 test passed correction. That finding is separate from the later mode hypothesis, and nonsignificance does not establish exactly zero effects. [Original single-cell findings](../../results/pcdr/ccr_singles_20260919/FINDINGS.md).

## What did the larger CCR runs add?

The 3390-trial study examined nine combinations of overall and inhibitory weight multipliers, component lesions and individual members. It checked whether the selected response depended on parameters or particular subsets. The following 101- and 530-trial studies addressed replay, time steps and the active subset. Their counts are computational trials, not animals or independent candidate circuits. [Frozen expanded design](CCR_EXPANDED_DESIGN.json), [results](CCR_RESULTS_20260927.md).

At default, lesioning the 29 baseline-active members produces a response close to, but not identical to, full51. At 0.1 ms, the absolute difference between their mean response vectors is 79 summed Hz, 1.5852% of the full-mode response, with signed cosine 0.999896. This suggests the active subset explains much of this fixed-condition response. It is not a general equivalence claim: no equivalence margin was fixed, memberships are outcome/context dependent, and silent cells can become active after a joint lesion.

All 660 single-cell lesions of the 22 default-baseline-silent members exactly reproduced their paired baseline spike events. In an outgoing-weight lesion, a cell that sends no spikes contributes no outgoing spike-triggered events along that trajectory. This explains the conditional result without proving those cells lack a role under another input or joint lesion. Eight fired in at least one full-mode lesion trial. [Component analysis](CCR_RESULTS_20260927.md).

## Does the numerical problem invalidate everything?

No blanket conclusion is supported. Default full-mode aggregate A/F remain close across 0.1, 0.05 and 0.025 ms, and their ordering exceeds the three fixed CCR comparators at both finer steps. That supports aggregate stability over those tested steps. It does not establish identical single-neuron responses, all-condition stability or convergence to a continuous-time limit. No numerical equivalence tolerance was specified before those results.

At overall weight 1.2 and inhibitory multiplier 0.8, some trajectories vary dramatically and non-monotonically with step size. For mode-without-MN9, seed 631405, the lesion emits 629557 spikes at 0.0125 ms and 17959 at 0.00625 ms. The large response occurs at an intermediate tested step, so smaller steps do not simply make every response decrease. It is not justified to select the smallest result as correct or declare a physiological transition. [Time-step evidence](CCR_RESULTS_20260927.md#completed-530-trial-time-step-comparison).

The linear subthreshold update does not remove the discrete scheduling of threshold detection, resets, refractory recovery and synaptic delivery. These event timings matter in a recurrent thresholded system. A specific cause of the divergence has not yet been isolated.

## What do replay and reconstruction establish?

Exact replay shows that the same setup reproduces its saved events. Non-perturbing recording checks that adding observation does not change those events. Four full-network recorded replays passed, including both the large and small trajectories. Neither test chooses which time step best approximates the intended dynamics. [Recorded-replay record](OBSERVED_REPLAY.md).

The ten monitored cells produced 646 spikes in the large-response lesion and 669 in the finer-step lesion, even though the whole-network difference was +611598. Their selection captured early differences but missed the later increase. Full spike files identified 11530 cells firing only in the large-response run, with 577 first firing before 180 ms. These groups depend on known outcomes and are descriptive.

Reconstructing delayed incoming increments matched 4.8 million recorded cell/tick comparisons within the declared 1e-9 mV tolerance and reproduced refractory flags exactly. Extending to the 577 cells showed larger positive and negative incoming magnitudes overall. Independent per-edge arrival counting reproduced 2308 target/run comparisons. Approximately 90.14% of positive arrivals in selected pre-first-spike windows came from early large-only cells. Ten targets, including the earliest eight, had no such positive arrivals. This describes sources during propagation; it does not identify an initiating cell or prove loss of inhibition. [Detailed reconstruction and source results](CCR_RESULTS_20260927.md).

## What would distinguish the explanations more convincingly?

This is the most useful design discussion to have with James and Dr. Muldoon. One option is to narrow the claim to conditional lesion sensitivity for this candidate and these explicitly imperfect alternatives. Another is a new multi-mode design with selection, feasible comparisons and evaluation inputs fixed before new lesion outcomes. A nonmotor-only question could reduce a particular confound, but it changes the target and should not be presented as the same experiment.

A defensible new comparison needs a stated reference population, a reproducible set-generation procedure, distribution checks, support/recruitment accounting, explicit treatment of motor identity, and a plan for unavoidable overlap. Tightening every rule without examining the available pool may make matching impossible. Relaxing rules because a desired result disappears would introduce a different problem. The next design should state what it can isolate before spending more compute.

If the question becomes the earliest cause of the high-weight numerical divergence, first validate full state reconstruction for the early targets and trace their incoming timing. Any intervention should then have a prediction fixed before its outcome, include suitable alternative interventions and retain all selected cases. This is a separate mechanistic/numerical question, not a replacement confirmation of the original mode hypothesis.

## What should I say when evidence is missing?

It is appropriate to say: that has not been tested; the result is conditional on these inputs; the comparison does not isolate that property; or the current files establish reproduction but not convergence. Do not infer a brain region from missing annotations, name a causal trigger from the earliest spike, equate seed replication with animal replication, or claim all four candidate circuits work.

The records do not justify every choice as uniquely optimal. The 75% support has a published precedent, whereas the minimum recruitment count, stimulus restriction, duration and particular matching tolerances remain operational choices whose adequacy depends on the question. Their recorded use and limitations are stronger evidence of a systematic process than a retrospective claim that every choice was inevitable.

## Where is the evidence if they ask to see it?

| Question | Record to open |
| --- | --- |
| What was decided and when? | [Lab notebook](LAB_NOTEBOOK.md) and [dated plan](PLAN.md) |
| Why did rank 33 win? | [Candidate review](RESEARCH_OVERVIEW.md#8-candidate-review-for-the-meeting-29-september) and [verification record](evidence/2026-09-29/candidate_review/record.json) |
| Did new seeds reproduce the result? | [Thirty-seed replication](SEED_REPLICATION_RESULTS_20260922.md) |
| What remains unmatched? | [Distribution audit](MOTOR_SET_AUDIT_20260922.md) and [later pool review](CCR_RESULTS_20260927.md#local-event-and-comparator-review) |
| What changed with time step? | [530-trial results](CCR_RESULTS_20260927.md#completed-530-trial-time-step-comparison) |
| What does the code do? | [Separate code guide](CODE_GUIDE.md) |
| How was the work checked? | [Verification overview](RESEARCH_OVERVIEW.md#6-verification-and-stopping-point), manifests and linked evidence |

Latest software suite: 330 passed, three unsupported-symlink skips, 106 warnings. Those are software results, not biological evidence. Large raw trial files remain in the local results archive; not every raw file is included in Git. No new test-suite run was needed for this explanatory document.
