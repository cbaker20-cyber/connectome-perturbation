import math

import pytest

from connectome_analysis.toy_signal import (
    build_toy_signal_run_record,
    propagate_toy_signal,
)


NODES = ["9007199254740993", "relay", "toy_output"]
EDGES = [
    {"source": "9007199254740993", "target": "relay", "weight": 2.0},
    {"source": "relay", "target": "toy_output", "weight": 0.5},
]


def test_known_answer_and_exact_string_id_preservation():
    output = propagate_toy_signal(
        NODES,
        EDGES,
        {"9007199254740993": 1.0},
        ["toy_output"],
        steps=2,
        decay=1.0,
        seed=7,
    )

    assert output == [1.0]
    record = build_toy_signal_run_record(
        input_ids=["9007199254740993"],
        output_ids=["toy_output"],
        output_vector=output,
        steps=2,
        decay=1.0,
        seed=7,
    )
    assert record["schema_version"] == "atlas-run-record/v0"
    assert record["input_ids"] == ["9007199254740993"]
    assert record["claim_status"] == "not_interpretable_as_neuroscience"
    assert "repository-local" in record["limitations"][2]


def test_output_order_is_stable():
    output = propagate_toy_signal(
        ["input", "a", "b"],
        [
            {"source": "input", "target": "a", "weight": 2.0},
            {"source": "input", "target": "b", "weight": 3.0},
        ],
        {"input": 1.0},
        ["b", "a"],
        steps=1,
        seed=0,
    )
    assert output == [3.0, 2.0]


@pytest.mark.parametrize(
    ("edges", "inputs", "outputs", "steps", "decay", "seed", "message"),
    [
        ([{"source": "missing", "target": "relay"}], {}, ["toy_output"], 1, 1.0, 0, "source is not in nodes"),
        (EDGES, {"missing": 1.0}, ["toy_output"], 1, 1.0, 0, "input node is not in nodes"),
        (EDGES, {}, ["missing"], 1, 1.0, 0, "output node is not in nodes"),
        (EDGES, {}, ["toy_output"], -1, 1.0, 0, "steps must be"),
        (EDGES, {}, ["toy_output"], 1, math.inf, 0, "decay must be"),
        (EDGES, {}, ["toy_output"], 1, 1.0, True, "seed must be"),
    ],
)
def test_rejects_invalid_inputs(edges, inputs, outputs, steps, decay, seed, message):
    with pytest.raises(ValueError, match=message):
        propagate_toy_signal(
            NODES,
            edges,
            inputs,
            outputs,
            steps=steps,
            decay=decay,
            seed=seed,
        )


def test_run_record_requires_aligned_outputs():
    with pytest.raises(ValueError, match="same length"):
        build_toy_signal_run_record(
            input_ids=["input"],
            output_ids=["a", "b"],
            output_vector=[1.0],
            steps=1,
            decay=1.0,
            seed=0,
        )
