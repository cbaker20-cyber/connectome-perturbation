import copy

import pytest

from connectome_analysis.targeted_validation_manifest import (
    CLAIM_STATUS,
    SCHEMA_VERSION,
    validate_targeted_validation_manifest,
)


def valid_manifest():
    digest = "a" * 64
    return {
        "schema_version": SCHEMA_VERSION,
        "claim_status": CLAIM_STATUS,
        "run_id": "synthetic-preflight-example",
        "git_commit": "1" * 40,
        "command": "planned-command-not-executed",
        "backend": {"name": "declared-backend", "version": "0"},
        "parameters": {"n_run": 30, "t_run_ms": 1000, "seed_policy": "fixed per cell"},
        "sources": [
            {"label": "sugar", "id_count": 21},
            {"label": "gustatory", "id_count": 7},
        ],
        "targets": ["AN", "brain_motor_neuron"],
        "cells": [
            {"source": "sugar", "target": "AN"},
            {"source": "sugar", "target": "brain_motor_neuron"},
            {"source": "gustatory", "target": "AN"},
            {"source": "gustatory", "target": "brain_motor_neuron"},
        ],
        "inputs": [{"path": "inputs/source_ids.csv", "size_bytes": 1, "sha256": digest}],
        "outputs": [
            {"path": "sweep_summary.csv", "size_bytes": 1, "sha256": digest},
            {"path": "sweep_run_info.csv", "size_bytes": 1, "sha256": digest},
            {"path": "ranked_targeted_validation.csv", "size_bytes": 1, "sha256": digest},
            {"path": "targeted_validation_readable_summary.txt", "size_bytes": 1, "sha256": digest},
            {"path": "logs/run.log", "size_bytes": 1, "sha256": digest},
        ],
        "limitations": [
            "Repository-local simulation evidence is not a biological or causal conclusion."
        ],
    }


def test_accepts_complete_four_cell_manifest():
    validate_targeted_validation_manifest(valid_manifest())


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda item: item.pop("claim_status"), "missing required fields"),
        (lambda item: item.__setitem__("extra", True), "unknown fields"),
        (lambda item: item.__setitem__("schema_version", "external/v1"), "unsupported schema_version"),
        (lambda item: item.__setitem__("claim_status", "validated"), "claim_status must be"),
        (lambda item: item.__setitem__("git_commit", "short"), "full 40-character"),
        (lambda item: item["parameters"].__setitem__("n_run", True), "positive integer"),
        (lambda item: item["sources"][0].__setitem__("id_count", 20), "must equal 21"),
        (lambda item: item["sources"].append({"label": "sugar", "id_count": 21}), "duplicate source"),
        (lambda item: item["targets"].append("AN"), "must not contain duplicates"),
        (lambda item: item["cells"].pop(), "cover exactly the four"),
        (lambda item: item["cells"].append(copy.deepcopy(item["cells"][0])), "must not contain duplicates"),
        (lambda item: item["inputs"][0].__setitem__("size_bytes", 0), "positive integer"),
        (lambda item: item["inputs"][0].__setitem__("sha256", "BAD"), "64 lowercase"),
        (lambda item: item["outputs"].pop(0), "missing required paths"),
        (lambda item: item["outputs"].__setitem__(-1, {"path": "outside.log", "size_bytes": 1, "sha256": "a" * 64}), "under logs/"),
        (lambda item: item.__setitem__("limitations", []), "non-empty array"),
    ],
)
def test_rejects_incomplete_or_corrupt_manifests(mutate, message):
    manifest = valid_manifest()
    mutate(manifest)

    with pytest.raises(ValueError, match=message):
        validate_targeted_validation_manifest(manifest)
