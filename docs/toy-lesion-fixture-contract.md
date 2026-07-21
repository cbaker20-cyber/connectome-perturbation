# Toy lesion fixture contract

## Purpose

This document defines the smallest deterministic synthetic graph needed to test lesion-ranking logic without making any biological or behavioral claim.

The fixture is not FlyWire data, is not a model of a real fly circuit, and must not be interpreted as neuroscience evidence. Its only role is to prove that scoring, ranking, provenance, and string-safe identifier handling behave as designed.

## Required graph roles

The synthetic graph must contain four explicit structural roles:

1. **Input node** — receives the fixed baseline signal.
2. **Critical relay node** — removing it must cause the largest functional output change among single-node lesions.
3. **Critical edge** — removing it must cause the largest functional output change among single-edge lesions.
4. **Misleading structural hub** — has higher degree or another stronger structural baseline than the critical relay, but its lesion must have a smaller functional effect.

At least one node identifier must be a decimal string representing an integer greater than `2^53`. All identifiers remain opaque strings through artifact generation, scoring, serialization, and tests.

## Deterministic signal contract

The baseline model must be dependency-light and deterministic:

- fixed graph, inputs, outputs, parameters, and seed produce byte-stable JSON artifacts;
- the baseline output vector is recorded before lesions;
- one node or one edge is removed at a time;
- the same propagation rule and parameters are used for baseline and every lesion;
- ties are broken deterministically by string identifier order;
- no stochastic claim is allowed unless the seed and sampling procedure are stored in the run record.

The first implementation should prefer a simple linear or bounded propagation rule over a biologically suggestive neuron model. The purpose is ranking correctness, not realism.

## Expected-answer fields

The generated toy artifact should include explicit expected answers:

```json
{
  "expected_critical_node": "critical_relay",
  "expected_critical_edge": ["input_node", "critical_relay"],
  "expected_misleading_hub": "structural_hub",
  "expected_node_ranking_prefix": ["critical_relay"],
  "expected_edge_ranking_prefix": [["input_node", "critical_relay"]]
}
```

Names may differ, but the roles and expected rankings must be encoded in the artifact rather than inferred from a test author's memory.

## Minimum score record

Each lesion result should include:

- `artifact_type`
- `schema_version`
- `claim_status`
- `target_type` (`node` or `edge`)
- `target_id` or `source_id`/`target_id`
- `baseline_output_vector`
- `lesioned_output_vector`
- `cosine_distance`
- `percent_output_change`
- `rank`
- `parameters`
- `seed`
- `input_artifact_sha256`

The record must state `claim_status: toy_validation_only` or an equally conservative value.

## Required assertions

Tests should prove all of the following:

1. The critical relay ranks above every other node lesion.
2. The critical edge ranks above every other edge lesion.
3. The misleading hub has a stronger structural score than the critical relay under at least one documented baseline metric, while producing a smaller functional lesion score.
4. The identifier above `2^53` survives round trips unchanged as text.
5. Repeated runs with fixed inputs produce identical ordered results and identical JSON bytes.
6. Absolute output paths and repository-escape paths are rejected.
7. The artifact and score records contain explicit non-claim language.

## Relationship to open issues

This contract sequences the existing work rather than creating a second framework:

- issue #10 owns the fixture and expected-answer encoding;
- issue #11 owns the baseline toy signal model;
- issue #12 owns node-lesion scoring;
- issue #13 owns edge-lesion scoring;
- issue #14 owns structural baseline metrics;
- issue #15 owns the vulnerability-matrix schema;
- issue #16 owns degree-matched random-control design.

Implementation should extend `tools/write_toy_graph_artifact.py` and its tests before introducing additional fixture generators.

## Non-claims

Passing this fixture demonstrates only that the toy scoring pipeline can recover answers intentionally built into a synthetic graph. It does not validate real connectome inputs, biological mechanisms, behavior, robustness on larger graphs, or scientific conclusions.