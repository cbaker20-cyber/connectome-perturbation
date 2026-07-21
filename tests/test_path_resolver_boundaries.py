import importlib.util
import json
from pathlib import Path

import pytest


def load_resolver():
    module_path = Path.cwd() / "tools/path_resolver.py"
    spec = importlib.util.spec_from_file_location(module_path.stem, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def make_repo(tmp_path: Path) -> Path:
    """Create an explicit repository-root fixture for repo_root_from()."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "README.md").write_text("fixture repository\n", encoding="utf-8")
    return repo_root


def write_manifest(repo_root: Path, record_path: str) -> Path:
    manifest_path = repo_root / "data/input_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(
            {
                "inputs": [
                    {
                        "path": record_path,
                        "filename": Path(record_path).name,
                        "guessed_role": "connectome_edges",
                        "guessed_materialization": "toy",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    return manifest_path


def test_resolve_input_rejects_manifest_record_outside_repo(tmp_path):
    resolver = load_resolver()
    repo_root = make_repo(tmp_path)
    outside = tmp_path / "outside.csv"
    outside.write_text("source,target\n1,2\n", encoding="utf-8")
    write_manifest(repo_root, "../outside.csv")

    with pytest.raises(ValueError, match="must stay within the repository"):
        resolver.resolve_input("outside.csv", repo_root=repo_root)


def test_resolve_input_rejects_fallback_outside_repo(tmp_path):
    resolver = load_resolver()
    repo_root = make_repo(tmp_path)
    outside = tmp_path / "outside.csv"
    outside.write_text("source,target\n1,2\n", encoding="utf-8")
    write_manifest(repo_root, "data/missing.csv")

    with pytest.raises(ValueError, match="must stay within the repository"):
        resolver.resolve_input("../outside.csv", repo_root=repo_root)


def test_resolve_input_accepts_repo_relative_manifest_record(tmp_path):
    resolver = load_resolver()
    repo_root = make_repo(tmp_path)
    data_file = repo_root / "data/edges.csv"
    data_file.parent.mkdir(parents=True)
    data_file.write_text("source,target\n1,2\n", encoding="utf-8")
    write_manifest(repo_root, "data/edges.csv")

    assert resolver.resolve_input("edges.csv", repo_root=repo_root) == data_file.resolve()
