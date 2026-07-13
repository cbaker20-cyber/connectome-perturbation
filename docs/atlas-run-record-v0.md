# Atlas run-record contract v0 (repository-local proposal)

Status: **proposed, synthetic-only, not an external Atlas standard**.

This document resolves the currently undefined “Atlas-compatible” requirement in issue #11 with the smallest repository-local contract that can be reviewed and validated. The name does not imply compatibility with any external Atlas project or neuroscience data standard.

## Required top-level fields

A run record is a UTF-8 JSON object with exactly these required fields:

- `schema_version`: string, fixed to `atlas-run-record/v0`.
- `artifact_type`: string, fixed to `toy_signal_run_record`.
- `claim_status`: string, fixed to `not_interpretable_as_neuroscience`.
- `model`: non-empty string identifying the deterministic synthetic model.
- `parameters`: object containing `steps` (non-negative integer), `decay` (finite number), and `seed` (integer).
- `input_ids`: array of unique, non-empty strings.
- `output_ids`: array of unique, non-empty strings.
- `output_vector`: array of finite numbers with the same length as `output_ids`.
- `limitations`: non-empty array of non-empty strings.

Identifiers must remain strings end-to-end. In particular, values such as `9007199254740993` must never be parsed as numbers.

## Deterministic serialization

Writers should use UTF-8 JSON with sorted object keys, two-space indentation, and a trailing newline. Array order is meaningful and must not be sorted implicitly. `output_vector[i]` corresponds to `output_ids[i]`.

## Validation behavior

A future `tools/validate_atlas.py` should:

1. fail closed on missing, unknown, or mistyped required fields;
2. reject booleans where integers or numbers are required;
3. reject NaN and infinities;
4. reject duplicate or empty identifiers;
5. enforce output-vector length equality;
6. preserve identifier text exactly;
7. return a non-zero exit code with a concise field-specific error on invalid input.

The validator should validate only representation, deterministic artifact structure, and declared limitations. It must not validate neuron identity, biological connectivity, neural dynamics, perturbation effects, behavior, or any neuroscience conclusion.

## Versioning

`v0` is intentionally narrow and may change before any stable release. Any incompatible change requires a new schema-version string and focused regression tests. Until this proposal is accepted and a validator is merged, PR #26 must not claim Atlas compatibility.
