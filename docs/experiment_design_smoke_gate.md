# Smoke-to-experiment promotion gate

This note defines the minimum evidence required before a metadata-only smoke run can be promoted into a perturbation experiment. It is a design contract, not evidence that any biological result is valid.

## Stage 0: immutable inputs

Promotion is blocked unless:

- `data/input_manifest.json` validates with no path, size, or SHA-256 mismatch;
- every input path is repository-relative and resolves inside the repository root;
- the output manifest copies the validated input path, byte size, and checksum records exactly;
- the smoke configuration checksum matches the configuration file used by the run;
- source release/materialization, access date, citation, terms, schema, row count, and preprocessing provenance are populated before claim-ready analysis.

A changed byte, changed config, or unresolved provenance field creates a new experimental input state and requires a new run identifier.

## Stage 1: deterministic smoke run

The smoke run should use `configs/smoke_run.yaml` and remain small enough for CI. A successful run must record:

- repository commit;
- exact command;
- random seed;
- configuration path and SHA-256;
- validated input-manifest reference and copied input checksums;
- every declared output path, byte size, and SHA-256;
- conservative `claim_status: not_interpretable_as_neuroscience`.

Repeat the same smoke run twice from the same commit and inputs. Promotion is blocked if deterministic artifacts differ, except for explicitly documented volatile metadata such as creation timestamps.

## Stage 2: negative controls

Before a biological perturbation is interpreted, run controls that should not produce a meaningful network effect:

1. **Identity control:** no nodes or edges changed.
2. **Seed-repeat control:** identical seed and parameters reproduce the same selected perturbation and metrics.
3. **Label-shuffle control:** preserve graph structure while breaking the proposed biological labeling relationship.
4. **Degree-matched random control:** compare targeted nodes with randomly selected nodes matched on degree or another preregistered structural covariate.

The output manifest must distinguish control type from perturbation type and preserve the same provenance chain.

## Stage 3: preregistered perturbation comparison

For each perturbation family, define before running:

- selection rule and eligible node population;
- perturbation magnitude or fraction;
- number of independent seeds;
- primary metric and its direction of interest;
- secondary metrics;
- baseline and negative-control comparison;
- exclusion and failure rules;
- aggregation method and uncertainty summary.

Do not select the primary metric after inspecting results. Exploratory metrics must be labeled exploratory.

## Stage 4: promotion decision

A run may be promoted from plumbing validation to scientific review only when all of the following are true:

- CI proves the reproducibility tests pass for the exact PR head;
- input and output manifests validate against files on disk;
- repeated deterministic smoke artifacts agree under the documented comparison rule;
- controls execute and are represented in manifests;
- provenance is complete enough for `--require-provenance` validation;
- the claim ledger names the exact run identifiers supporting each statement;
- limitations include graph incompleteness, materialization dependence, perturbation-model assumptions, and multiple-comparison risk where applicable.

Passing this gate permits review of results. It does not itself establish a neuroscience conclusion.
