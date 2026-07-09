import importlib.util
import json
from pathlib import Path


SCHEMA_VERSION = "0.1"
AWARE_TIMESTAMP = "2026-07-09T00:00:00+00:00"


def load_module(repo_root: Path, relative_path: str):
    module_path = repo_root / relative_path
    spec = importlib.util.spec_from_file_location(module_path.stem, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def write_smoke_config(repo_root: Path, tool) -> dict:
    config_dir = repo_root / "configs"
    config_dir.mkdir(exist_ok=True)
    config_path = config_dir / "smoke_run.yaml"
    config_path.write_text("run_name: smoke\nrandom_seed: 42\nmode: metadata_only\n", encoding="utf-8")
    return {
        "config_path": "configs/smoke_run.yaml",
        "config_sha256": tool.sha256_file(config_path),
    }


def base_output_manifest(repo_root: Path, tool) -> dict:
    config = write_smoke_config(repo_root, tool)
    return {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": AWARE_TIMESTAMP,
        "status": "metadata_only_smoke",
        "command": "python tools/write_output_manifest.py",
        "repo_commit": None,
        "config_path": config["config_path"],
        "config_sha256": config["config_sha256"],
        "input_manifest_path": "data/input_manifest.json",
        "input_manifest_present": False,
        "input_checksums": [],
        "claim_status": "not_interpretable_as_neuroscience",
        "outputs": [],
    }


def test_validate_output_manifest_accepts_declared_output_with_matching_digest(tmp_path):
    tool = load_module(Path.cwd(), "tools/validate_reproducibility.py")
    repo_root = tmp_path
    output_file = repo_root / "results" / "summary.json"
    output_file.parent.mkdir()
    output_file.write_text('{"ok": true}\n', encoding="utf-8")
    manifest = base_output_manifest(repo_root, tool)
    manifest["outputs"] = [
        {
            "path": "results/summary.json",
            "sha256": tool.sha256_file(output_file),
            "size_bytes": output_file.stat().st_size,
        }
    ]
    manifest_path = repo_root / "output_manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    errors = []
    tool.validate_output_manifest(repo_root, manifest_path, errors)

    assert errors == []


def test_validate_output_manifest_rejects_output_path_escape(tmp_path):
    tool = load_module(Path.cwd(), "tools/validate_reproducibility.py")
    repo_root = tmp_path
    manifest = base_output_manifest(repo_root, tool)
    manifest["outputs"] = [{"path": "../outside.csv", "sha256": "0" * 64}]
    manifest_path = repo_root / "output_manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    errors = []
    tool.validate_output_manifest(repo_root, manifest_path, errors)

    assert "output 0 path must stay within the repository: ../outside.csv" in errors


def test_validate_output_manifest_rejects_stale_output_digest(tmp_path):
    tool = load_module(Path.cwd(), "tools/validate_reproducibility.py")
    repo_root = tmp_path
    output_file = repo_root / "results" / "summary.json"
    output_file.parent.mkdir()
    output_file.write_text('{"ok": true}\n', encoding="utf-8")
    manifest = base_output_manifest(repo_root, tool)
    manifest["outputs"] = [
        {
            "path": "results/summary.json",
            "sha256": "0" * 64,
            "size_bytes": output_file.stat().st_size,
        }
    ]
    manifest_path = repo_root / "output_manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    errors = []
    tool.validate_output_manifest(repo_root, manifest_path, errors)

    assert "output sha256 mismatch: results/summary.json" in errors
