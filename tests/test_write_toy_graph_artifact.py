from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


def load_tool():
    path = Path(__file__).resolve().parents[1] / "tools" / "write_toy_graph_artifact.py"
    spec = importlib.util.spec_from_file_location("write_toy_graph_artifact", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_toy_graph_payload_has_known_expected_outcomes():
    tool = load_tool()

    payload = tool.toy_graph_payload()

    assert payload["claim_status"] == "not_interpretable_as_neuroscience"
    assert "This is not FlyWire data." in payload["non_claims"]
    assert "biological connectome" in " ".join(payload["non_claims"])

    metrics = payload["expected_metrics"]
    assert metrics["node_count"] == 4
    assert metrics["edge_count"] == 3
    assert metrics["reachable_from_sensory_a"] == [
        "interneuron_b",
        "motor_c",
        "sensory_a",
    ]
    assert metrics["weak_component_count"] == 2
    assert metrics["out_degree"] == {
        "sensory_a": 2,
        "interneuron_b": 1,
        "motor_c": 0,
        "isolated_d": 0,
    }
    assert metrics["in_degree"] == {
        "sensory_a": 0,
        "interneuron_b": 1,
        "motor_c": 2,
        "isolated_d": 0,
    }


def test_lesion_fixture_preserves_exact_string_ids_and_expected_roles():
    tool = load_tool()
    fixture = tool.toy_graph_payload()["lesion_fixture"]

    assert fixture["source"] == "9007199254740993"
    assert isinstance(fixture["source"], str)
    assert all(isinstance(node, str) for node in fixture["nodes"])
    assert fixture["expected_critical_node"] == "critical_relay"
    assert fixture["expected_critical_edge"] == ["critical_relay", "toy_output"]
    assert fixture["expected_misleading_hub"] == "structural_hub"


def test_known_critical_node_outranks_misleading_structural_hub():
    tool = load_tool()
    scores = tool.toy_lesion_scores()

    assert scores["baseline_target_reachable"] is True
    assert scores["out_degree"]["structural_hub"] > scores["out_degree"]["critical_relay"]
    assert scores["node_scores"]["critical_relay"] > scores["node_scores"]["structural_hub"]


def test_known_critical_edge_outranks_noncritical_edges():
    tool = load_tool()
    edge_scores = tool.toy_lesion_scores()["edge_scores"]

    critical_key = "critical_relay->toy_output"
    assert edge_scores[critical_key] == 1
    assert edge_scores[critical_key] > edge_scores["9007199254740993->structural_hub"]
    assert edge_scores[critical_key] > edge_scores["structural_hub->dead_end_a"]


def test_write_toy_graph_artifact_is_deterministic(tmp_path, monkeypatch):
    tool = load_tool()
    fake_repo = tmp_path / "repo"
    fake_repo.mkdir()
    monkeypatch.setattr(tool, "repo_root", lambda: fake_repo)

    first = tool.write_toy_graph_artifact("results/toy_graph_artifact.json")
    first_bytes = first.read_bytes()
    second = tool.write_toy_graph_artifact("results/toy_graph_artifact.json")

    assert second.read_bytes() == first_bytes
    assert first.read_text(encoding="utf-8") == json.dumps(
        tool.toy_graph_payload(), indent=2, sort_keys=True
    ) + "\n"


def test_write_toy_graph_artifact_rejects_absolute_output(tmp_path, monkeypatch):
    tool = load_tool()
    monkeypatch.setattr(tool, "repo_root", lambda: tmp_path)

    with pytest.raises(ValueError, match="repo-relative"):
        tool.write_toy_graph_artifact(str(tmp_path / "artifact.json"))


def test_write_toy_graph_artifact_rejects_parent_directory_escape(tmp_path, monkeypatch):
    tool = load_tool()
    repo = tmp_path / "repo"
    repo.mkdir()
    monkeypatch.setattr(tool, "repo_root", lambda: repo)

    with pytest.raises(ValueError, match="escapes repository"):
        tool.write_toy_graph_artifact("../artifact.json")
