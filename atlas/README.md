# FLY Grand Atlas

The Atlas is the evidence spine of the project.

It should answer four questions for every result:

1. What was run?
2. What data and parameters were used?
3. What changed after perturbation?
4. Which claim, if any, does the result support?

## Directories

```text
atlas/
  perturbations/   run records, schemas, vulnerability outputs
  signatures/      context-by-neuron or context-by-edge matrices
  claims/          claim/evidence map
  failures/        failed runs, broken assumptions, bugs
  literature/      paper matrix and research gaps
  figures/         figure registry and captions
  reports/         daily/weekly summaries
```

## Rules

- No run is interpretable without a manifest.
- No claim is allowed without linked evidence.
- Failed experiments must be logged.
- Toy graph validation must precede full-data claims.
- 64-bit neuron IDs must be preserved exactly.
