"""Tests for Johnston's Organ 30-trial sweep config loading and group selection."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "configs" / "jo_ground_truth_30trial.yaml"


def load_run_jo_sweep():
    module_path = REPO_ROOT / "scripts" / "run_jo_sweep.py"
    spec = importlib.util.spec_from_file_location("run_jo_sweep", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def jo_sweep():
    return load_run_jo_sweep()


@pytest.fixture(scope="module")
def config(jo_sweep):
    return jo_sweep.load_config(CONFIG_PATH)


def test_config_loads_30trial_poisson_protocol(config):
    assert config["run_name"] == "jo_ground_truth_30trial"
    assert config["random_seed"] == 42
    assert config["simulation"]["n_run"] == 30
    assert config["simulation"]["t_run_ms"] == 1000
    assert config["simulation"]["r_poi_hz"] == 150
    assert config["paths"]["results_dir"] == "results/jo_ground_truth"
    assert config["sensory_input"]["expected_count"] == 146
    assert len(config["sensory_input"]["root_ids"]) == 146


def test_config_binds_output_manifest_schema(config):
    schema = config["output_manifest_schema"]
    assert "random_seed" in schema["required_fields"]
    assert "input_checksums" in schema["required_fields"]
    assert schema["spike_parquet"]["columns"] == ["t", "trial", "flywire_id", "exp_name"]
    assert schema["spike_parquet"]["compression"] == "brotli"


def test_config_rejects_root_id_count_mismatch(tmp_path, jo_sweep):
    payload = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    payload["sensory_input"]["root_ids"] = payload["sensory_input"]["root_ids"][:10]
    bad = tmp_path / "bad.yaml"
    bad.write_text(yaml.safe_dump(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="expected_count"):
        jo_sweep.load_config(bad)


def test_select_jo_neurons_from_annotations(jo_sweep, config):
    annotations = jo_sweep.load_annotations(REPO_ROOT / "flywire_annotations.tsv")
    sim_ids = jo_sweep.load_sim_ids(REPO_ROOT / "2023_03_23_completeness_630_final.csv")
    jo_ids = jo_sweep.select_jo_neurons(annotations, sim_ids, config["sensory_input"])

    assert len(jo_ids) == 146
    assert jo_ids == [int(x) for x in config["sensory_input"]["root_ids"]]
    assert set(jo_ids).issubset(sim_ids)

    # Curated IDs must predominantly match JO mechanosensory annotation filters.
    ann = annotations.copy()
    ann["root_id"] = ann["root_id"].astype("int64")
    labeled = ann[ann["root_id"].isin(jo_ids)]
    assert (labeled["super_class"] == "sensory").mean() >= 0.95
    assert (labeled["cell_class"] == "mechanosensory").mean() >= 0.95
    assert labeled["cell_type"].astype(str).str.startswith("JO-").mean() >= 0.95


def test_select_perturbation_groups(jo_sweep, config):
    annotations = jo_sweep.load_annotations(REPO_ROOT / "flywire_annotations.tsv")
    sim_ids = jo_sweep.load_sim_ids(REPO_ROOT / "2023_03_23_completeness_630_final.csv")
    jo_ids = jo_sweep.select_jo_neurons(annotations, sim_ids, config["sensory_input"])
    groups = jo_sweep.select_perturbation_groups(
        annotations,
        sim_ids,
        config["perturbation_groups"],
        exclude_ids=set(jo_ids),
    )

    assert set(groups) == {"AN", "descending", "LO", "Kenyon_Cell", "motor"}
    for name, ids in groups.items():
        assert len(ids) > 0
        assert set(ids).isdisjoint(jo_ids)
        assert set(ids).issubset(sim_ids)


def test_prepare_jo_sweep_uses_path_resolver(jo_sweep, config):
    jo_ids, groups, resolved = jo_sweep.prepare_jo_sweep(config, repo_root=REPO_ROOT)
    assert len(jo_ids) == 146
    assert resolved["annotations"].name == "flywire_annotations.tsv"
    assert resolved["completeness"].name == "2023_03_23_completeness_630_final.csv"
    assert resolved["connectivity"].name == "2023_03_23_connectivity_630_final.parquet"
    assert resolved["results_dir"].as_posix().endswith("results/jo_ground_truth")
    assert "AN" in groups


def test_build_output_manifest_includes_seed_checksums_and_spike_schema(jo_sweep, config):
    jo_ids = [int(x) for x in config["sensory_input"]["root_ids"]]
    groups = {"AN": [1, 2, 3]}
    manifest = jo_sweep.build_output_manifest(
        config,
        "configs/jo_ground_truth_30trial.yaml",
        repo_root=REPO_ROOT,
        command=["python", "scripts/run_jo_sweep.py", "--dry-run"],
        jo_ids=jo_ids,
        groups=groups,
    )
    assert manifest["random_seed"] == 42
    assert isinstance(manifest["input_checksums"], list)
    assert len(manifest["input_checksums"]) >= 1
    assert all("sha256" in row for row in manifest["input_checksums"])
    assert manifest["claim_status"] == "not_interpretable_as_neuroscience"
    spike_paths = {row["path"] for row in manifest["spike_parquet"]}
    assert "results/jo_ground_truth/baseline_jo.parquet" in spike_paths
    assert "results/jo_ground_truth/perturb_AN.parquet" in spike_paths
    assert manifest["spike_parquet"][0]["columns"] == ["t", "trial", "flywire_id", "exp_name"]


def test_dry_run_writes_manifest(jo_sweep):
    import json

    payload = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    payload["paths"]["results_dir"] = "results/jo_ground_truth_test_tmp"
    payload["paths"]["output_manifest"] = "results/jo_ground_truth_test_tmp/output_manifest.json"
    cfg_path = REPO_ROOT / "configs" / "_test_jo_tmp.yaml"
    out_dir = REPO_ROOT / "results/jo_ground_truth_test_tmp"
    try:
        cfg_path.write_text(yaml.safe_dump(payload), encoding="utf-8")
        rc = jo_sweep.main(["--config", "configs/_test_jo_tmp.yaml", "--dry-run"])
        assert rc == 0
        out = out_dir / "output_manifest.json"
        assert out.is_file()
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data["random_seed"] == 42
        assert data["simulation"]["n_jo_neurons"] == 146
        assert data["input_checksums"]
    finally:
        if cfg_path.exists():
            cfg_path.unlink()
        if out_dir.exists():
            for child in out_dir.iterdir():
                child.unlink()
            out_dir.rmdir()
