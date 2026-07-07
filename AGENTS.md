# FLY Agent Rules

## Mission

This repository is being turned into a counterfactual connectome vulnerability-mapping project for the adult Drosophila connectome.

The target contribution is not “a fly simulator.” The target contribution is a reproducible framework that asks: which neurons and synapses does a model-predicted sensory computation depend on, and how does that dependency change across contexts?

## Prime Directive

Never claim success without evidence.

Every completed task must report:

- files changed;
- commands run;
- tests or checks performed;
- exact observed output;
- remaining uncertainty;
- next recommended step.

If any of those are missing, the task is not complete.

## Scientific Claim Rules

Allowed language:

- model-predicted vulnerability;
- context-specific perturbation effect;
- candidate circuit element;
- functional importance under this simulation;
- experimentally testable prediction;
- structural-vs-functional comparison.

Forbidden language unless future wet-lab evidence exists:

- proved behavior;
- discovered the real circuit;
- causal in the real fly;
- definitive biological control point;
- brain understands;
- AlphaFold for connectomes.

## Data Integrity Rules

Neuron IDs must never be parsed as floats.

FlyWire/root IDs must be preserved as either:

- strings, or
- true 64-bit integers.

Every data-loading task must check:

- no scientific-notation corruption;
- no rounded IDs;
- no duplicate IDs unless expected and documented;
- edge endpoints exist;
- neurotransmitter labels align to the correct neurons;
- row counts and schemas are logged.

## Coding Rules

Only work on the assigned GitHub issue.

Never commit directly to `main`.

Use branches named:

```text
agent/<issue-number>-short-title
```

Prefer simple code. Do not add dependencies unless necessary. Add tests for every behavior change. If tests do not exist, add the smallest useful test or validation script.

## Required Validation

Every scientific module needs:

- toy graph test with known answer;
- random baseline where applicable;
- saved config;
- saved seed;
- saved output path;
- reproducible command.

## Required PR Summary

Each PR must include:

### Summary
What changed.

### Evidence
Commands run and exact results.

### Files Changed
Important files.

### Scientific Risk
What could be wrong.

### Remaining Uncertainty
What is not proven yet.

### Next Step
Recommended next issue.
