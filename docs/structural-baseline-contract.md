# Synthetic structural baseline contract

This document defines a repository-local contract for issue #14. It applies only
to deterministic synthetic graph fixtures. The resulting values are graph
statistics, not measurements of neural function, biological importance,
behavior, vulnerability, mechanism, or causality.

## Scope

Given an explicit ordered node list and a directed weighted edge list, produce
one row per node with deterministic structural statistics that can be compared
with repository-local synthetic lesion scores.

The first implementation should remain dependency-free unless a new dependency
is separately justified and reviewed. PageRank is therefore optional; degree
metrics are required.

## Input contract

- `nodes` is a non-empty sequence of unique, non-empty strings.
- Numeric-looking identifiers remain strings and are never coerced.
- `edges` is an ordered sequence of records with exactly `source`, `target`, and
  `weight` fields.
- Every endpoint must occur in `nodes`.
- `weight` must be finite and non-negative.
- Self-loops are allowed but must be counted consistently as both incoming and
  outgoing.
- Parallel directed edges are allowed for structural aggregation and are summed;
  they must not be silently deduplicated.
- Caller-owned inputs must not be mutated.

Malformed or ambiguous inputs must fail closed with a descriptive error.

## Required metrics

For each node, compute:

- `in_degree`: number of incoming edge records.
- `out_degree`: number of outgoing edge records.
- `weighted_in_degree`: sum of incoming edge weights.
- `weighted_out_degree`: sum of outgoing edge weights.
- `weighted_degree`: `weighted_in_degree + weighted_out_degree`.

All values must be finite and non-negative. Integer degree counts remain
integers; weighted values are serialized as JSON numbers.

If PageRank is later added, its algorithm, damping factor, convergence tolerance,
maximum iterations, dangling-node behavior, dependency/version, and
normalization checks must be explicit. PageRank must not be introduced merely to
satisfy the issue wording if those choices are not reproducible.

## Output contract

Use repository-local schema `atlas-structural-baseline-table/v0` with these
top-level fields:

- `schema_version`
- `artifact_type`
- `claim_status`
- `node_ids`
- `metrics`
- `rows`
- `limitations`

Required fixed values:

- `schema_version`: `atlas-structural-baseline-table/v0`
- `artifact_type`: `synthetic_structural_baseline_table`
- `claim_status`: `not_interpretable_as_neuroscience`
- `metrics`: `["in_degree", "out_degree", "weighted_in_degree",
  "weighted_out_degree", "weighted_degree"]`

`node_ids` preserves the exact input order. `rows` contains exactly one record
per node in that same order. Each row contains exactly `node_id` plus the five
required metric fields. Duplicate or missing rows are invalid.

Serialization must be deterministic under the repository's canonical JSON
convention. Repeated construction from equivalent inputs must produce equal
objects and byte-stable canonical JSON.

## Comparison with lesion scores

A future test may compare structural and synthetic functional rankings only when
both artifacts use the exact same node axis. The test should demonstrate the
specific toy-fixture property requested by issue #14: a deliberately misleading
hub can rank highly on a declared structural metric while ranking lower on an
existing synthetic lesion metric.

That known-answer result is evidence about the fixture and implementation only.
It must not be generalized to real connectomes or described as a neuroscience
finding.

## Required validation and tests

The implementation PR should include:

1. a hand-computed known-answer graph covering incoming, outgoing, weighted,
   self-loop, and parallel-edge accounting;
2. exact string-ID and node-order preservation;
3. deterministic serialization and non-mutation checks;
4. fail-closed tests for duplicate nodes, unknown endpoints, malformed edges,
   booleans, negative weights, and non-finite weights;
5. top-level artifact validation for exact fields, dimensions, row ordering,
   metric types/ranges, fixed claim status, and non-empty limitations;
6. a focused comparison against the existing synthetic node-lesion scorer using
   an explicit shared fixture, without biological interpretation.

Passing GitHub Actions on the exact PR head is required before merge. No local
or unverified execution is acceptable as evidence.

## Limitations

- Degree statistics describe only the supplied synthetic edge table.
- High degree is not equivalent to functional importance or biological
  vulnerability.
- Synthetic lesion scores are bookkeeping outputs of the repository's toy
  propagation model, not simulated neural activity or behavior.
- This contract does not validate FlyWire identifiers, synapses, cell types,
  connectome completeness, neural dynamics, perturbation effects, behavior,
  mechanism, or causality.
