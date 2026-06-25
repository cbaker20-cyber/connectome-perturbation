# Next Steps Execution Plan

Date: 2026-06-25

## Core Priority

Do not continue exploratory AN/BORA rescue attempts until the benchmark infrastructure is implemented. The next deliverable is the transition from conceptual framework to executable pipeline.

The first concrete target is:

```text
results/context_reachability/context_by_cell_type_exposure.csv
```

This table connects input contexts, perturbation targets, and null-calibrated exposure labels.

---

# Phase 1 — Freeze the Research Question

## Deliverable

```text
connectome_research_docs/13_FINAL_PROJECT_SCOPE.md
```

## Final research question

Can static graph topology predict the motor-output consequences of perturbing neuron groups in a nonlinear whole-brain connectome simulation, or are context-dependent dynamical features required?

## Final hypothesis

Simple graph metrics such as degree, strength, and centrality will only partially predict perturbation-induced motor-output changes. Context-conditioned routing and activity-weighted topology will improve prediction, especially under community-dropped validation.

---

# Phase 2 — Clean Repository State

Run locally:

```powershell
git status --short
```

Do not commit:

```text
.venv/
results/
Drosophila_brain_model/
large parquet files
temporary figures
```

If needed:

```powershell
Add-Content .git\info\exclude ".venv/"
Add-Content .git\info\exclude "results/"
Add-Content .git\info\exclude "Drosophila_brain_model/"
```

Then commit source files, docs, metadata, and tools only.

---

# Phase 3 — Simulator Audit

Before final claims, audit the simulator.

## Required checks

1. Reset rule audit
   - Current concern: `v = v_rst; w = 0; g = 0 * mV`
   - Cleaner target: `v = v_rst; g = 0 * mV`

2. Voltage sanity check
   - Monitor a sample of neurons.
   - Flag extreme hyperpolarization or runaway activity.

3. No-input spontaneous baseline
   - no input / intact
   - no input / lesioned

4. Seed control
   - save random seeds for final runs.
   - do not let Poisson timing differences masquerade as biological effects.

5. Trial count
   - development runs can use 5 trials.
   - final inference should use 30 trials when computationally feasible.

---

# Phase 4 — Context Source Panels

Build:

```text
metadata/source_contexts/
```

Minimum contexts:

```text
sugar
gustatory
mechanosensory
visual_projection
sensory_ascending
random_sensory_matched
no_input
```

Use two modes:

## Mode A — Biologically complete source sets

Use all available neurons from a meaningful annotated input group.

## Mode B — Total-current-normalized source sets

Normalize total external input across contexts so source-system size is not confounded with architecture.

---

# Phase 5 — Context Reachability Audit

Build:

```text
tools/context_reachability_audit.py
```

Output:

```text
results/context_reachability/context_by_cell_type_exposure.csv
```

Required columns:

```text
input_context
cell_type
cell_class
super_class
n_neurons
mean_source_exposure
fraction_exposed_neurons
total_source_exposure
null_median_exposure
fold_vs_null
p_exposure
q_exposure
exposure_label
reason
```

Exposure labels:

```text
Robustly Exposed
Weakly Exposed
Out-of-Context
Tonic Active
Ambiguous
```

---

# Phase 6 — Community-Dropped Validation Splits

Build:

```text
tools/build_cell_type_similarity_graph.py
```

Output:

```text
results/cell_type_similarity/cell_type_similarity_edges.csv
results/cell_type_similarity/cell_type_communities.csv
```

Similarity features:

```text
input cosine similarity
output cosine similarity
partner Jaccard overlap
degree/strength similarity
```

Then build:

```text
tools/community_dropped_cv_plan.py
```

Output:

```text
results/cv_splits/community_dropped_splits.csv
```

---

# Phase 7 — Pilot Run

Do not scale first. Run a pilot with:

```text
2 input contexts
20 perturbation targets
5-10 trials
raw motor metrics only
```

The pilot must answer:

```text
Do simulations finish reliably?
Are motor outputs nonzero?
Do no-input controls behave sanely?
Are exposure labels reasonable?
Do community splits have enough train/test targets?
```

---

# Phase 8 — Scale Perturbations

Preferred target count:

```text
N = 200-500 perturbation targets
```

Minimum target count:

```text
N >= 100
```

For each pair `(s,c)`, compute raw motor metrics:

```text
mean_abs_motor_delta
L2_motor_delta
top10_motor_shift
number_motor_neurons_affected
state_dependent_lesion_interaction
```

---

# Phase 9 — Structural Predictor Table

Build:

```text
results/benchmark_features/context_target_features.csv
```

Required columns:

```text
input_context
perturbation_target
n_neurons
removed_outgoing_weight
mean_degree
mean_strength
source_exposure
downstream_motor_reach
linear_diffusion_prediction
static_BORA
activity_weighted_BORA
community_id
```

---

# Phase 10 — Model Benchmark

Compare feature blocks:

```text
Model 0: lesion size + removed edge weight
Model 1: degree + strength
Model 2: centrality
Model 3: linear diffusion
Model 4: static routing / BORA
Model 5: activity-weighted routing
```

Validation:

```text
community-dropped cross-validation
```

Performance metrics:

```text
R2
MAE
Spearman correlation
permutation importance
Shapley/commonality attribution
```

Main analysis question:

```text
Does routing or activity-weighted topology improve prediction beyond size, degree, strength, and linear diffusion?
```

---

# Phase 11 — Motor Manifold Sensitivity

Only after raw metrics work:

```text
context-specific PCA
train-only PCA
K = 1-10 sensitivity
Isomap or Diffusion Maps sensitivity
```

PCA is not the primary target.

---

# Phase 12 — Final Figures

1. Project schematic
2. Context exposure audit heatmap
3. Random CV vs community-dropped CV comparison
4. Model benchmark bar plot
5. Shapley/commonality attribution figure

---

# Immediate 48-Hour Plan

## Day 1

1. Commit current documentation and metadata.
2. Audit `model.py` reset rule.
3. Add no-input baseline design.
4. Create source-context folder and initial context definition files.

## Day 2

1. Draft or build `context_reachability_audit.py`.
2. Generate first exposure table for sugar plus one other context.
3. Build cell-type similarity graph design.
4. Decide perturbation target eligibility rules.
5. Run a tiny pilot, not a full sweep.

---

# Do Not Do Next

Do not:

```text
keep trying to prove AN significance
claim feeding/grooming without independent labels
use the 78-neuron null as evidence
run massive simulations before simulator audit
trust random train/test splits
make PCA the central motor result
write final claims before benchmark tables exist
```
