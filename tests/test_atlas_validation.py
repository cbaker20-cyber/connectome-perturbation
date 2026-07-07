from __future__ import annotations

import pytest

from tools.validate_atlas import validate_run_record


def valid_record():
    return {
        "run_id": "toy-example-001",
        "created_at": "2026-07-06T00:00:00-04:00",
        "code_version": {"commit": "example-only", "branch": "agent/fly-reactor-setup"},
        "context": {
            "name": "toy_sugar_like",
            "input_neurons": ["100000000000000001"],
            "output_neurons": ["100000000000000009"],
        },
        "model": {"name": "toy_linear_propagation", "parameters": {"steps": 3}, "random_seed": 0},
        "input_data": {"manifest": "example", "id_validation": "example", "checksums": {}},
        "perturbation": {"target_type": "node", "targets": ["100000000000000005"], "method": "remove_node"},
        "metrics": {"primary": "cosine_distance", "values": {"cosine_distance": 0.91}},
        "outputs": {"files": ["results/toy/example.csv"], "figure_ids": []},
        "validation_status": "exploratory",
    }


def test_valid_record_passes():
    validate_run_record(valid_record())


def test_rejects_non_string_input_neuron_ids():
    record = valid_record()
    record["context"]["input_neurons"] = [100000000000000000.0]
    with pytest.raises(ValueError, match="input neuron IDs must be strings"):
        validate_run_record(record)


def test_rejects_non_string_perturbation_targets():
    record = valid_record()
    record["perturbation"]["targets"] = [100000000000000000.0]
    with pytest.raises(ValueError, match="perturbation targets must be strings"):
        validate_run_record(record)


def test_rejects_missing_required_field():
    record = valid_record()
    record.pop("metrics")
    with pytest.raises(ValueError, match="missing top-level fields"):
        validate_run_record(record)
