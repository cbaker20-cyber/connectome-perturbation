import json
import pytest
from scripts import pcdr_check_resolution as checker


def test_changed_plan_and_incomplete_run_are_rejected(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    (root / "docs/pcdr").mkdir(parents=True)
    plan = {"jobs": [{"id": "one"}]}
    (root / "docs/pcdr/CCR_RESOLUTION_PLAN.json").write_text(json.dumps(plan))
    run = tmp_path / "run"
    run.mkdir()
    monkeypatch.setattr(checker, "ROOT", root)
    (run / "plan.json").write_text(json.dumps({"jobs": []}))
    with pytest.raises(ValueError, match="Changed follow-up plan"):
        checker.check(tmp_path / "old", run, tmp_path / "out")
    (run / "plan.json").write_text(json.dumps(plan))
    (run / "progress.json").write_text(json.dumps({"status": "complete", "completed": 0}))
    with pytest.raises(ValueError, match="Incomplete run"):
        checker.check(tmp_path / "old", run, tmp_path / "out")
    assert not (tmp_path / "out").exists()


def test_changed_source_is_rejected(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    (root / "docs/pcdr").mkdir(parents=True)
    plan = {"jobs": [], "sources": {"scripts/worker.py": "wrong"}}
    (root / "docs/pcdr/CCR_RESOLUTION_PLAN.json").write_text(json.dumps(plan))
    run = tmp_path / "run"
    (run / "source").mkdir(parents=True)
    (run / "source/worker.py").write_text("changed")
    (run / "plan.json").write_text(json.dumps(plan))
    (run / "progress.json").write_text(json.dumps({"status": "complete", "completed": 0}))
    monkeypatch.setattr(checker, "ROOT", root)
    with pytest.raises(ValueError, match="Changed source"):
        checker.check(tmp_path / "old", run, tmp_path / "out")
    assert not (tmp_path / "out").exists()
