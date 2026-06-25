# Scientific Justification & Literature Defense Portfolio

Date: 2026-06-25

## Framework Title

Context-conditional, community-validated benchmarking of static connectome topology, linear diffusion, activity-weighted routing, and nonlinear spiking simulation for predicting motor-output vulnerability in the Drosophila whole-brain connectome.

## Executive Thesis

The central scientific problem is not whether one neuron class appears important under one stimulus. The deeper problem is that a whole-brain connectome is a static wiring diagram, while the functional consequence of perturbing that wiring depends on input context, recurrent dynamics, thresholds, delays, and motor-output geometry.

The final framework asks:

```text
When do static graph metrics predict nonlinear simulated motor-output consequences of perturbation, and when are context-dependent dynamical features required?
```

The benchmark target is:

```text
Y(s,c) = motor-output response under input context s after output-lesioning perturbation target c
```

where `s` is an input context and `c` is a cell type, cell class, or structurally defined perturbation target.

---

# Module 1 — Out-of-Sample Generalization Defense

## Problem: topological autocorrelation

A random train/test split across cell types is invalid because connectome-derived observations are not independent. Cell types that share input partners, output partners, circuit modules, or anatomical neighborhoods may have similar structural feature vectors and similar simulated perturbation effects.

If cell type A is placed in training and a nearly identical neighboring cell type B is placed in testing, high performance does not prove general network learning. It may only prove local interpolation.

## Formal defense

Let each perturbation target have structural features:

```text
x_c = [cell_count, degree, strength, centrality, exposure, motor_reach, diffusion, routing, ...]
```

If two targets have high input/output similarity:

```text
sim(c_i, c_j) ≈ 1
```

then:

```text
x_ci ≈ x_cj
Y(s,ci) ≈ Y(s,cj)
```

Random splits therefore leak topological information.

## Required fix: community-dropped cross-validation

Build a cell-type similarity graph. Each node is a perturbation target. Edge weights combine:

```text
input cosine similarity
output cosine similarity
partner Jaccard overlap
degree/strength similarity
```

Then partition this similarity graph into structural communities using Louvain, Leiden, Infomap, or an equivalent graph clustering method.

For fold `m`:

```text
Train = all communities except community m
Test  = community m
```

This tests out-of-community generalization rather than interpolation between locally similar cell types.

## Critique silencer

A reviewer may say:

```text
Your model memorized local wiring neighborhoods.
```

The response is:

```text
Prediction was evaluated on structurally held-out cell-type communities, not random cell types. Test targets were withheld by input/output wiring similarity, so performance reflects out-of-community generalization.
```

---

# Module 2 — Disentangling Graph Metric Collinearity

## Problem: graph predictors are collinear

Cell count, removed outgoing edge weight, out-degree, strength, diffusion, motor reach, centrality, and routing metrics are not independent. A large cell type often has high removed edge weight. A high-strength group often has high motor reach. A routing score may share variance with source exposure and downstream connectivity.

Ordinary least squares coefficients are unstable under this structure.

## VIF logic

For predictor `X_j`, the variance inflation factor is:

```text
VIF_j = 1 / (1 - R_j^2)
```

where `R_j^2` comes from regressing `X_j` on all other predictors. If `R_j^2` is high, the coefficient for `X_j` is not interpretable because the model cannot uniquely allocate shared variance.

## Required fix: blocked model comparison plus Shapley/commonality

Use predictor blocks:

```text
Block 0: lesion size + removed edge weight
Block 1: degree + strength
Block 2: centrality
Block 3: linear diffusion
Block 4: static routing / BORA
Block 5: activity-weighted routing
```

For any subset of blocks `S`, define:

```text
v(S) = held-out predictive performance using blocks in S
```

For block `i`, the Shapley value is:

```text
phi_i = sum over S not containing i of weight(S) * [v(S union {i}) - v(S)]
```

This averages a block's marginal contribution over all possible insertion orders.

## Critique silencer

A reviewer may say:

```text
BORA only looks useful because it shares variance with degree and strength.
```

or:

```text
BORA only looks useless because size and strength entered first.
```

The response is:

```text
I report order-independent Shapley/commonality attribution and reverse-order sensitivity, not only one sequential regression. Shared variance is quantified explicitly.
```

This prevents the benchmark from collapsing into the trivial claim that large lesions cause large effects.

---

# Module 3 — State-Dependent Factorial Interaction Framework

## Problem: baseline subtraction is not enough

In a nonlinear spiking network, spontaneous activity cannot be removed by simple linear subtraction. A perturbation can have little effect at rest but a large effect when sensory drive moves membrane potentials toward threshold.

A linear system satisfies:

```text
f(A + B) = f(A) + f(B)
```

A recurrent spiking system with thresholds, refractory periods, delays, and feedback generally does not.

## Required fix: 2 x 2 factorial design

Use the design:

```text
Network state: spontaneous vs driven
Perturbation state: intact vs lesioned
```

The state-dependent lesion interaction is:

```text
I(s,c) = [M_lesion(s,c) - M_intact(s)] - [M_lesion(no_input,c) - M_intact(no_input)]
```

This should be interpreted as an interaction term, not simple background subtraction.

## Critique silencer

A reviewer may say:

```text
You cannot linearly subtract spontaneous activity from a nonlinear spiking network.
```

The response is:

```text
Correct. The double difference is not interpreted as linear background removal. It is the formal interaction term testing whether lesion impact depends on network state.
```

This turns a vulnerability into a core dynamical-systems question.

---

# Module 4 — Continuous, Null-Calibrated Exposure vs Structural Dust

## Problem: dense connectomes make binary reachability meaningless

In a large dense directed connectome, many neurons may be technically reachable through long, weak, low-weight paths. Binary path existence therefore creates false exposure labels.

## Required exposure metric

For input vector `x_s` and row-normalized effective connectivity matrix `P`, define attenuated downstream exposure:

```text
exposure_s = sum_{k=1 to L} gamma^(k-1) * x_s * P^k
```

where:

```text
L = maximum propagation depth
gamma = attenuation factor between 0 and 1
```

For target group `c`, compute:

```text
mean_source_exposure(s,c)
fraction_exposed_neurons(s,c)
total_source_exposure(s,c)
```

Use mean exposure as primary because total exposure is confounded by cell count.

## Matched random-source null

For each context, compare observed exposure to random source ensembles matched on:

```text
source count or total injected current
source modality/super_class when possible
source degree
source strength
```

Then compute empirical p-values and BH-FDR q-values:

```text
q_exposure(s,c) < 0.05
```

A robust exposure call also requires fold enrichment over null and a group-level fraction criterion.

## Five-tier exposure taxonomy

Use:

```text
Robustly Exposed
Weakly Exposed
Out-of-Context
Tonic Active
Ambiguous
```

This prevents low effect under one input context from being mislabeled as biological unimportance.

## Critique silencer

A reviewer may say:

```text
Everything is reachable in a dense graph.
```

The response is:

```text
I do not use binary reachability. Exposure is attenuated, continuous, null-calibrated, FDR-corrected, and interpreted through a five-tier taxonomy.
```

---

# Module 5 — Target-Space Representation Geometry

## Problem: PCA may impose false geometry

Motor output is initially a vector across annotated motor neurons:

```text
delta_m(s,c) = motor_lesion(s,c) - motor_intact(s)
```

PCA assumes that meaningful motor variation lies in a linear subspace. A recurrent spiking system with thresholds and delays may generate curved nonlinear manifolds. Therefore PCA should not be the primary target definition.

## Primary raw motor metrics

Use assumption-light primary metrics:

```text
mean_abs_motor_delta
L2_motor_delta
top_k_motor_shift
number_motor_neurons_affected
```

## Secondary manifold analyses

Use context-specific PCA only as a sensitivity analysis:

```text
For each context s:
    fit PCA on training perturbation targets only
    project held-out targets into that fixed basis
    choose K using training-only rules
```

Also test nonlinear embeddings such as Isomap or Diffusion Maps as sensitivity analyses.

## Poisson-seed robustness

Split-half trial reliability should not be called biological reproducibility. In this simulator, much of the stochasticity comes from Poisson input spike timing. Therefore, the correct term is:

```text
Poisson-seed robustness
```

It filters components that are unstable to stochastic input jitter.

## Critique silencer

A reviewer may say:

```text
PCA is blind to nonlinear motor geometry.
```

The response is:

```text
PCA is not primary. Raw motor metrics are primary, PCA is secondary, and nonlinear embeddings are sensitivity analyses. Conclusions must survive across target-space representations.
```

---

# Integrated Final Defense

The final framework controls the major false-discovery risks:

```text
Random-split leakage -> community-dropped CV
Big lesions cause big effects -> lesion size/removed edge baselines
Graph metric collinearity -> Shapley/commonality attribution
Linear baseline subtraction -> factorial interaction
Structural dust -> null-calibrated attenuated exposure
Sugar-only overinterpretation -> context-conditional tensor Y(s,c)
PCA geometry bias -> raw primary metrics + manifold sensitivity
```

## Final Defensible Claim

This project develops a context-conditional, community-validated benchmark for testing when static connectome topology is sufficient to predict nonlinear motor-output vulnerability and when full dynamical simulation or activity-weighted topology adds predictive information. The design explicitly controls for lesion size, degree/strength confounding, topological autocorrelation, structural reachability dust, nonlinear state dependence, and target-space geometry.

## Claims Not Supported Without Further Validation

The framework does not yet prove:

```text
AN neurons are biological feeding/grooming switch neurons.
Simulation motor outputs equal real behavior.
Provisional hq_AN motor-response targets are validated behavior labels.
```

Those remain exploratory or future validation directions.
