# Research Claims Ledger

This file controls what the project is allowed to say.

## Central Claim Under Construction

> Counterfactual perturbation can generate model-predicted vulnerability signatures for defined sensory-output contexts in a connectome model.

Status: **not yet proven in this repo**.

Evidence needed:

- 64-bit-safe input validation;
- toy graph with known lesion answer;
- deterministic baseline simulation;
- node and edge perturbation scores;
- graph metric baselines;
- random and degree-matched controls;
- context-specific vulnerability matrix;
- stability checks.

## Strong Claim We Want Eventually

> Functional vulnerability is context-specific and not fully predicted by structural graph centrality.

Status: **future target**.

Evidence needed:

- at least three contexts;
- top-k overlap between vulnerability and graph metrics;
- correlation statistics;
- control comparisons;
- sensitivity analysis.

## Ambitious Claim We May Explore

> Contexts can be organized into a behavior-similarity space using shared vulnerability signatures.

Status: **speculative**.

Evidence needed:

- vulnerability signature matrix;
- context-context similarity metric;
- clustering stability;
- comparison to known circuit organization if available.

## Forbidden Claims For Now

Do not claim:

- that the system proves real fly behavior;
- that simulated outputs are actual behavior;
- that identified neurons are true biological causes;
- that a top lesion target is experimentally validated;
- that the project has built an AlphaFold equivalent;
- that the full connectome has been functionally solved.

## Approved Framing

Use:

- model-predicted;
- under this simulation;
- candidate;
- vulnerability signature;
- virtual perturbation;
- counterfactual analysis;
- testable prediction.

## Evidence Map Template

| Claim | Status | Evidence files | Figures | Weakness |
|---|---|---|---|---|
| Functional vulnerability differs from graph centrality | unsupported | TBD | TBD | no baselines yet |
| ID validation prevents silent neuron corruption | in progress | TBD | TBD | validator not merged yet |
| Toy graph lesion scoring works | unsupported | TBD | TBD | no toy fixture yet |
