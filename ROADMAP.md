# FLY Reactor Roadmap

## North Star

Build a counterfactual connectome atlas: a reproducible system that turns static wiring into evidence-linked vulnerability maps.

The core research question:

> Can virtual perturbations reveal context-specific vulnerability signatures in a whole-brain connectome that are not predicted by structural graph metrics alone?

## Phase 0 — Stop the Bleeding

Goal: make the repo safe for agents and honest research.

- Add agent rules.
- Add claim rules.
- Add atlas folders.
- Add schema validation.
- Add issue templates.
- Add CI.
- Refuse unsupported biological claims.

## Phase 1 — Trust the Inputs

Goal: prove the data can be loaded without corruption.

Required outputs:

- input manifest;
- SHA-256 checksums;
- schema validation;
- 64-bit-safe neuron ID tests;
- materialization/version decision log.

Kill criteria:

- if IDs round, the result is invalid;
- if source/version cannot be documented, the run is exploratory only.

## Phase 2 — Toy Truth Before Big Data

Goal: create a tiny connectome where the correct answer is known.

Required outputs:

- toy graph fixture;
- known critical neuron;
- known critical edge;
- known useless hub;
- tests proving lesion scoring finds the correct targets.

No full-brain claim is allowed until the toy graph works.

## Phase 3 — Baseline Simulation Spine

Goal: produce deterministic model output from a defined sensory context.

Required outputs:

- context config format;
- input neuron group;
- output neuron group;
- model parameters;
- random seed;
- saved output vector;
- run manifest.

## Phase 4 — Node and Edge Perturbation

Goal: score how much each lesion changes output.

Required outputs:

- node vulnerability scores;
- edge vulnerability scores;
- cosine-distance metric;
- percent-output-change metric;
- saved before/after vectors;
- tests and toy validation.

## Phase 5 — Structural Baselines

Goal: prove whether vulnerability is or is not reducible to graph centrality.

Required baselines:

- in-degree;
- out-degree;
- weighted degree;
- PageRank;
- betweenness when tractable;
- distance from input;
- distance to output;
- hub/rich-club indicator if available.

Required comparisons:

- Spearman correlation;
- top-k overlap;
- random degree-matched controls;
- effect-size table.

## Phase 6 — Vulnerability Signatures

Goal: build the central atlas matrix.

```text
rows = contexts
columns = neurons or synapses
values = vulnerability score
```

Minimum contexts:

- sugar/taste;
- odor;
- touch/mechanosensory;
- vision/motion.

## Phase 7 — Behavior Geometry

Goal: compare contexts by shared vulnerability.

Required outputs:

- context similarity matrix;
- clustered heatmap;
- list of context-specific bottlenecks;
- list of shared bottlenecks;
- interpretation file that avoids overclaiming.

## Phase 8 — Stability and Controls

Goal: attack the method.

Required checks:

- shuffled inputs;
- shuffled neurotransmitter labels;
- random lesions;
- degree-matched random lesions;
- seed sensitivity;
- threshold sensitivity;
- synaptic-weight scaling sensitivity.

## Phase 9 — Competition Output

Goal: convert the validated system into a serious project story.

Required figures:

1. pipeline diagram;
2. ID validation and provenance diagram;
3. toy graph proof;
4. vulnerability ranking;
5. structural-vs-functional comparison;
6. vulnerability signature matrix;
7. context similarity map;
8. claim-evidence map.

## Rule

A cool result without controls is garbage. A modest result with ruthless validation is usable. The win condition is not size; it is defensible novelty.
