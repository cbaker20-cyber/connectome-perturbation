import importlib.util
import json
from pathlib import Path


def load_tool():
    module_path = Path.cwd() / "tools/write_smoke_artifact.py"
    spec = importlib.util.spec_from_file_location(module_path.stem, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_smoke_artifact_payload_is_conservative_and_stable():
    tool = load_tool()

    payload = tool.smoke_artifact_payload()

    assert payload["schema_version"] == "0.1"
    assert payload["artifact_type"] == "metadata_only_reproducibility_smoke"
    assert payload["claim_status"] == "not_interpretable_as_neuroscience"
    assert "python tools/write_output_manifest.py" in payload["expected_next_command"]
    assert "--artifact results/reproducibility_smoke_artifact.json" in payload["expected_next_command"]
    assert "This artifact is not a simulation result." in payload["non_claims"]
    assert "This artifact is not evidence for a biological conclusion." in payload["non_claims"]


def test_write_smoke_artifact_creates_deterministic_json(tmp_path):
    tool = load_tool()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    output_path = tool.write_smoke_artifact(repo_root, "results/reproducibility_smoke_artifact.json")

    assert output_path == repo_root / "results" / "reproducibility_smoke_artifact.json"
    assert json.loads(output_path.read_text(encoding="utf-8")) == tool.smoke_artifact_payload()
    assert output_path.read_text(encoding="utf-8") == json.dumps(
        tool.smoke_artifact_payload(), indent=2, sort_keys=True
    ) + "\n"


def test_write_smoke_artifact_rejects_absolute_output_path(tmp_path):
    tool = load_tool()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    try:
        tool.write_smoke_artifact(repo_root, str(repo_root / "results" / "artifact.json"))
    except ValueError as exc:
        assert "--output must be repo-relative, not absolute:" in str(exc)
    else:
        raise AssertionError("absolute smoke artifact output path should be rejected")


def test_write_smoke_artifact_rejects_parent_directory_escape(tmp_path):
    tool = load_tool()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    try:
        tool.write_smoke_artifact(repo_root, "../artifact.json")
    except ValueError as exc:
        assert "--output must stay within the repository: ../artifact.json" in str(exc)
    else:
        raise AssertionError("escaping smoke artifact path should be rejected")
