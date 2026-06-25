# Final Project Scope

Date: 2026-06-25

## Final Project Direction

This project is no longer framed as a narrow descriptive claim that ascending neurons (ANs) or any single neuron group are definitively responsible for feeding, grooming, or a specific biological behavior. The refined project is a computational neuroscience benchmark:

> A context-conditional benchmark testing when static connectome topology, linear diffusion, activity-weighted routing, and nonlinear spiking simulations can predict motor-output vulnerability in the Drosophila whole-brain connectome.

The project uses FlyWire-derived connectivity and a simplified spiking simulator to compare structural graph summaries against nonlinear simulated motor-output consequences of perturbation.

## Final Research Question

Can static graph topology predict the motor-output consequences of perturbing neuron groups in a nonlinear whole-brain connectome simulation, or are context-dependent dynamical features required?

## Final Hypothesis

Simple graph metrics such as degree, strength, and centrality will only partially predict perturbation-induced motor-output changes. Context-conditioned routing and activity-weighted topology are expected to improve prediction, especially under structurally held-out community-dropped validation.

## Unit of Analysis

The unit of analysis is not a neuron group alone. It is:

```text
(input_context, perturbation_target) -> motor-output response
```

Formally:

```text
Y(s, c) = simulated motor-output response under input context s after output-lesioning perturbation target c
```

where:

- `s` is an input context such as sugar, gustatory, mechanosensory, visual projection, sensory ascending, or no-input control.
- `c` is a perturbed cell type, cell class, or structurally defined group.
- `Y(s,c)` is measured from simulated motor-neuron firing-rate changes, not direct behavior.

## Claim Boundaries

The project may claim:

- The simulator implements a connectome-based dynamical benchmark.
- Motor output is measured as changes in simulated annotated motor-neuron firing rates.
- Perturbations are synaptic output lesions, not literal optogenetic silencing.
- Context matters: a neuron group may be important under one source context and irrelevant under another.
- Static topology, linear diffusion, routing, and activity-weighted topology can be benchmarked against nonlinear simulation outputs.
- Community-dropped validation is required to avoid topological autocorrelation leakage.

The project must not claim without independent validation:

- AN neurons are definitively feeding/grooming switch neurons.
- hq_AN-derived motor targets are validated feeding/grooming motor labels.
- Sugar-only perturbation results imply global neuron importance.
- Simulation output is the same as measured biological behavior.
- Random train/test splits prove generalizable network principles.

## Core Methodological Commitments

1. Use context-conditional analyses rather than sugar-only global interpretation.
2. Treat source exposure as continuous and null-calibrated, not binary reachability.
3. Include no-input controls and state-dependent lesion interaction terms.
4. Use raw motor metrics as primary targets; PCA and nonlinear embeddings are sensitivity analyses.
5. Use community-dropped cross-validation rather than random cell-type splits.
6. Include lesion size and removed edge weight as baseline predictors to avoid the trivial claim that large lesions cause large effects.
7. Attribute predictive variance using blocked model comparison plus Shapley/commonality analysis.
8. Treat BORA and routing metrics as predictors in a benchmark, not as standalone proof of biological enrichment.

## Final One-Sentence Thesis

A rigorous context-conditional benchmark can determine when static connectome topology is sufficient to predict simulated motor-output vulnerability and when nonlinear dynamics or activity-weighted routing add predictive information beyond size, degree, strength, and linear diffusion.
