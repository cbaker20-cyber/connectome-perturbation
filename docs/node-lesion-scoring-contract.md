# Synthetic node-lesion scoring contract

Status: proposed contract for issue #12.

This document defines repository-local behavior for testing node-removal scoring on the deterministic synthetic lesion fixture. It is infrastructure for known-answer tests only. It does not describe a biological lesion, neural silencing, behavior, or a result from FlyWire or any other connectome dataset.

## Inputs

The scorer must receive:

- a non-empty ordered sequence of unique string node IDs;
- directed edges whose `source` and `target` both occur in the node sequence;
- finite numeric edge weights, defaulting to `1.0` only when the caller explicitly permits that default;
- a mapping of fixed input values keyed by node ID;
- an ordered sequence of output node IDs;
- deterministic propagation parameters accepted by `propagate_toy_signal`;
- a target-node sequence defining which nodes are tested one at a time.

IDs must remain strings throughout parsing, scoring, serialization, and validation. In particular, `9007199254740993` must never be coerced to a floating-point or integer representation.

## Baseline

Run the unmodified graph exactly once with the requested parameters and preserve:

- ordered `output_ids`;
- ordered baseline `output_vector`;
- input IDs and propagation parameters;
- the repository-local schema version and explicit limitations.

The baseline vector is bookkeeping output from the synthetic propagation model. It is not neural activity.

## One-node-at-a-time perturbation

For each requested target node:

1. reject targets absent from the graph;
2. reject duplicate targets;
3. construct a new graph with that node and every incident edge removed;
4. reject removal of a fixed input or requested output node unless the caller uses a separately documented policy;
5. run the same deterministic propagation parameters used for baseline;
6. preserve the original output ordering;
7. record the perturbed vector and comparison metrics.

The implementation must not mutate caller-owned node, edge, input, or output collections.

## Comparison metrics

For baseline vector `b` and perturbed vector `p`, record:

### Percent output change

Use the L1 magnitude definition:

```text
100 * sum(abs(p_i - b_i)) / sum(abs(b_i))
```

If `sum(abs(b_i)) == 0`, fail closed instead of emitting infinity, NaN, or an arbitrary sentinel.

### Cosine distance

Use:

```text
1 - dot(b, p) / (norm(b) * norm(p))
```

Both vectors must contain only finite numbers and have equal non-zero length. If either norm is zero, fail closed rather than choosing a convention silently.

These metrics are numerical comparisons of synthetic output vectors only.

## Deterministic ranking

Rank targets by:

1. descending percent output change;
2. descending cosine distance;
3. ascending target ID as a deterministic tie-breaker.

The known-answer fixture must show `critical_relay` ranking above `structural_hub`. This proves only that the scorer recovers the fixture's intentionally encoded answer.

## Result record

Each target row must include at least:

- `target_id` as an exact string;
- ordered `baseline_output_vector`;
- ordered `perturbed_output_vector`;
- `percent_output_change`;
- `cosine_distance`;
- propagation parameters;
- ordered input and output IDs;
- fixture or graph identifier;
- `claim_status: not_interpretable_as_neuroscience`;
- limitations stating that the graph and propagation values are synthetic.

A table-oriented result may use a new versioned schema rather than pretending that each row is an `atlas-run-record/v0` baseline run. Any new schema must be documented and validated before merge.

## Required validation and tests

Focused tests must cover:

- the known critical relay ranking above the misleading structural hub;
- exact preservation of `9007199254740993` as a string;
- stable ranking and byte-stable serialization;
- unknown and duplicate target rejection;
- input/output target-removal policy;
- dangling-edge rejection;
- non-finite edge, input, vector, and metric rejection;
- baseline-zero and perturbed-zero metric behavior;
- output-vector length and ordering checks;
- proof that caller-owned inputs are not mutated.

Acceptance evidence must come from a GitHub Actions run on the exact pull-request head. A local test result alone is not sufficient evidence for this repository workflow.

## Scientific limitations

Passing these tests would establish only that the repository's deterministic synthetic scoring implementation matches its declared mathematical and serialization contract. It would not validate neuron identity, synapse weights, neural dynamics, causal effects, behavioral effects, biological vulnerability, or any claim about a real fly connectome.
