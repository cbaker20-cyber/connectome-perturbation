# Degree-matched random control contract

This document defines a preregistration-style contract for comparing targeted perturbations with structurally similar random targets. It is an experiment-design artifact only. It does not report a completed analysis or support a neuroscience claim.

## Purpose

A target can appear important simply because it has unusually high degree or weighted degree. The control therefore asks whether a targeted perturbation produces a larger effect than random perturbations drawn from a prespecified population with similar structural covariates.

## Required inputs

Each run must record:

- repository commit and exact command;
- validated input-manifest path and checksums;
- graph/materialization identifier and preprocessing provenance;
- target identifier as an exact string;
- eligible control population and all exclusion rules;
- matching covariates and binning or distance rule;
- number of requested controls and random seed;
- primary effect metric defined before result inspection.

Neuron identifiers must remain strings. Matching must not coerce identifiers to floating-point values.

## Eligible population

Define the eligible population before sampling. At minimum, exclude:

- the target itself;
- nodes absent from the validated graph;
- nodes failing the same inclusion criteria used for the target;
- nodes with missing matching covariates;
- any node excluded by a documented anatomical, annotation, or quality rule.

Do not silently broaden the pool when too few matches exist. Record the failure and stop, or use a preregistered fallback rule.

## Matching rule

Prefer exact matching on discrete covariates where feasible. Otherwise use a deterministic nearest-neighbor rule over preregistered transformed covariates.

Minimum structural covariates:

- in-degree;
- out-degree;
- weighted in-degree;
- weighted out-degree.

Optional covariates may include component membership, layer, neuropil, or annotation class only when their provenance and missing-value handling are documented.

For binned matching:

1. define bin edges before inspecting perturbation effects;
2. use the same edges for targets and controls;
3. record the target bin and candidate-pool size;
4. sample without replacement when enough candidates exist;
5. record whether replacement was required by a preregistered rule.

For distance matching:

1. define scaling or transformation for each covariate;
2. define the distance function;
3. define tie-breaking deterministically by exact string identifier;
4. record the distance for every selected control.

## Sampling and reproducibility

For each target:

- use a named seed recorded in the output;
- produce the same control set for identical inputs, configuration, and seed;
- sort emitted records deterministically;
- preserve the full candidate-pool size and selected-control list;
- write repository-relative outputs only;
- include output byte size and SHA-256 in the output manifest.

A second seed may be used only as a separately identified run, not as an undocumented retry.

## Effect-size reporting

Let `E_target` be the preregistered perturbation effect for the target and `E_control_i` the same effect for each matched control.

Report at minimum:

- target effect;
- number of valid controls;
- control median and mean;
- control standard deviation and interquartile range when defined;
- target-minus-control-median difference;
- empirical percentile of the target within the control distribution;
- two-sided empirical tail proportion using a documented finite-sample correction;
- all individual control effects, not only aggregate values.

Do not label the empirical tail proportion as a confirmatory p-value unless the sampling design, exchangeability assumptions, multiplicity handling, and analysis plan justify that interpretation.

## Minimum output fields

Each target summary record must contain:

- `run_id`
- `target_id`
- `target_effect`
- `primary_metric`
- `matching_covariates`
- `matching_rule`
- `eligible_pool_size`
- `requested_control_count`
- `valid_control_count`
- `seed`
- `control_mean`
- `control_median`
- `control_standard_deviation`
- `control_interquartile_range`
- `target_minus_control_median`
- `target_empirical_percentile`
- `empirical_two_sided_tail_proportion`
- `input_manifest`
- `config_sha256`
- `repository_commit`
- `claim_status`

Each control-level record must contain:

- `run_id`
- `target_id`
- `control_id`
- `control_effect`
- matching-covariate values for target and control;
- match distance or exact-bin identifier;
- selection rank;
- replacement flag.

## Failure conditions

The run must be marked non-interpretable when:

- the validated input manifest fails;
- the eligible pool is empty;
- fewer controls are available than the preregistered minimum;
- matching covariates are missing or computed inconsistently;
- target and controls use different perturbation or scoring code paths;
- identifiers are coerced or lose precision;
- deterministic reruns disagree for fixed inputs and seed;
- provenance required by the smoke-to-experiment gate is incomplete.

## Interpretation limits

Degree matching reduces one class of structural confounding; it does not prove causal biological importance. Results may still depend on graph incompleteness, materialization choice, edge-weight definition, annotation quality, matching quality, perturbation-model assumptions, metric choice, and multiple comparisons.

The default `claim_status` must remain `not_interpretable_as_neuroscience` until real inputs, controls, provenance, repeated runs, and claim-ledger review satisfy the repository promotion gate.
