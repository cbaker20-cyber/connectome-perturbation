# Synthetic connection-lesion scoring contract

Status: proposed contract for issue #13.

This document defines repository-local behavior for testing one-connection-at-a-time scoring on the deterministic synthetic lesion fixture. It is infrastructure for known-answer tests only. It does not describe a biological lesion, synaptic silencing, neural activity, behavior, or a result from FlyWire or any other connectome dataset.

## Inputs

The scorer must receive:

- a non-empty ordered sequence of unique string node IDs;
- an ordered sequence of directed edge records;
- every edge with string `source` and `target` IDs present in the node sequence;
- a finite numeric edge weight, defaulting to `1.0` only when the caller explicitly permits that default;
- a mapping of fixed input values keyed by node ID;
- an ordered sequence of output node IDs;
- deterministic propagation parameters accepted by `propagate_toy_signal`;
- an ordered target-edge sequence defining which connections are tested one at a time.

Node IDs must remain strings throughout parsing, scoring, serialization, and validation. In particular, `9007199254740993` must never be coerced to a floating-point or integer representation.

## Edge identity

A target connection is identified by an exact ordered pair:

```text
(source_id, target_id)
```

Direction is part of the identity. `(a, b)` and `(b, a)` are different targets.

The initial implementation must reject parallel edges with the same ordered pair rather than silently removing all matches or selecting one by list position. Supporting multigraph edge IDs requires a separate documented schema revision.

Self-loops may be accepted only when the underlying propagation function accepts them and the target is represented unambiguously. Unknown, duplicate, malformed, or non-string target pairs must fail closed.

## Baseline

Run the unmodified graph exactly once with the requested parameters and preserve:

- ordered `output_ids`;
- ordered baseline `output_vector`;
- input IDs and propagation parameters;
- fixture or graph identifier;
- repository-local schema version and explicit limitations.

The baseline vector is bookkeeping output from the synthetic propagation model. It is not neural activity.

## One-connection-at-a-time perturbation

For each requested target connection:

1. verify that exactly one edge matches the ordered source-target pair;
2. construct a new edge sequence with only that edge removed;
3. retain the complete node sequence, fixed inputs, output IDs, and propagation parameters;
4. run the same deterministic propagation parameters used for baseline;
5. preserve the original output ordering;
6. record the perturbed vector and comparison metrics.

The implementation must not mutate caller-owned node, edge, input, output, or target collections.

Removing an edge must not remove either endpoint. Any resulting disconnected node remains in the graph unless a separately documented preprocessing step says otherwise.

## Comparison metrics

For baseline vector `b` and perturbed vector `p`, reuse `compare_output_vectors` and record:

### Percent output change

```text
100 * sum(abs(p_i - b_i)) / sum(abs(b_i))
```

If `sum(abs(b_i)) == 0`, fail closed instead of emitting infinity, NaN, or an arbitrary sentinel.

### Cosine distance

```text
1 - dot(b, p) / (norm(b) * norm(p))
```

Both vectors must contain only finite numbers and have equal non-zero length. If either norm is zero, fail closed rather than choosing a convention silently.

These metrics are numerical comparisons of synthetic output vectors only.

## Deterministic ranking

Rank connections by:

1. descending percent output change;
2. descending cosine distance;
3. ascending source ID;
4. ascending target ID.

The known-answer fixture must show `critical_relay -> toy_output` ranking above noncritical connections. This proves only that the scorer recovers the fixture's intentionally encoded answer.

## Result record

The table-level record must include at least:

- `schema_version` for a repository-local connection-lesion table schema;
- `artifact_type: synthetic_connection_lesion_scores`;
- `claim_status: not_interpretable_as_neuroscience`;
- fixture or graph identifier;
- ordered input and output IDs;
- propagation parameters;
- ordered baseline output vector;
- explicit limitations;
- ranked result rows.

Each result row must include at least:

- `source_id` and `target_id` as exact strings;
- ordered `baseline_output_vector`;
- ordered `perturbed_output_vector`;
- `percent_output_change`;
- `cosine_distance`.

The schema must be documented and validated before merge. It must not be presented as an external Atlas standard.

## Required validation and tests

Focused tests must cover:

- the known critical connection ranking above noncritical connections;
- direction-sensitive edge identity;
- exact preservation of `9007199254740993` as a string;
- stable ranking and byte-stable serialization;
- unknown and duplicate target rejection;
- rejection of ambiguous parallel edges;
- malformed edge and target-pair rejection;
- dangling-edge rejection;
- non-finite edge, input, vector, and metric rejection;
- baseline-zero and perturbed-zero metric behavior;
- output-vector length and ordering checks;
- proof that caller-owned inputs are not mutated.

Acceptance evidence must come from a GitHub Actions run on the exact pull-request head. A local test result alone is not sufficient evidence for this repository workflow.

## Scientific limitations

Passing these tests would establish only that the repository's deterministic synthetic connection-scoring implementation matches its declared mathematical and serialization contract. It would not validate neuron identity, synapse identity or weight, neural dynamics, causal effects, behavioral effects, biological vulnerability, or any claim about a real fly connectome.
