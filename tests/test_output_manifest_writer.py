import importlib.util
from pathlib import Path


def load_writer():
    module_path = Path.cwd() / "tools/write_output_manifest.py"
    spec = importlib.util.spec_from_file_location(module_path.stem, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_output_manifest_writer_rejects_absolute_cli_paths(tmp_path):
    writer = load_writer()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    try:
        writer.repo_relative_path(repo_root, str(repo_root / "output_manifest.json"), "--output")
    except ValueError as exc:
        assert "--output must be repo-relative, not absolute:" in str(exc)
    else:
        raise AssertionError("absolute output path should be rejected")


def test_output_manifest_writer_rejects_parent_directory_escape(tmp_path):
    writer = load_writer()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    try:
        writer.repo_relative_path(repo_root, "../outside_manifest.json", "--output")
    except ValueError as exc:
        assert "--output must stay within the repository: ../outside_manifest.json" in str(exc)
    else:
        raise AssertionError("parent-directory output escape should be rejected")


def test_output_manifest_writer_ignores_malformed_inputs_list():
    writer = load_writer()

    manifest = {"input_count": 2, "inputs": "not-a-list"}

    assert writer.input_manifest_checksums(manifest) == []
    assert writer.input_manifest_count(manifest) == 2


def test_output_manifest_writer_skips_non_object_input_records():
    writer = load_writer()

    manifest = {
        "input_count": 3,
        "inputs": [
            {"path": "data/a.csv", "sha256": "abc", "size_bytes": 12},
            "not-an-object",
            {"path": "data/b.csv", "sha256": "def", "size_bytes": 34},
        ],
    }

    assert writer.input_manifest_checksums(manifest) == [
        {"path": "data/a.csv", "sha256": "abc", "size_bytes": 12},
        {"path": "data/b.csv", "sha256": "def", "size_bytes": 34},
    ]


def test_output_manifest_writer_ignores_non_integer_input_count():
    writer = load_writer()

    assert writer.input_manifest_count({"input_count": "3", "inputs": []}) is None
