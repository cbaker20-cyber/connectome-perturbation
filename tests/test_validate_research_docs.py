import csv
import importlib.util
from pathlib import Path


def load_module():
    module_path = Path.cwd() / "tools/validate_research_docs.py"
    spec = importlib.util.spec_from_file_location("validate_research_docs", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def write_minimal_pack(docs_root: Path) -> None:
    docs_root.mkdir(parents=True, exist_ok=True)
    for name in load_module().REQUIRED_FILES:
        path = docs_root / name
        if name.endswith(".csv"):
            continue
        path.write_text(f"# {name}\n", encoding="utf-8")

    docs_root.joinpath("docs_config.yaml").write_text(
        "status_labels:\n  - exploratory\n  - validated\n  - completed\n",
        encoding="utf-8",
    )

    with (docs_root / "03_EXPERIMENT_REGISTRY.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "experiment_id",
                "date",
                "short_name",
                "type",
                "stimulus",
                "perturbation_target",
                "n_trials",
                "duration_s",
                "script_or_file",
                "primary_output",
                "status",
                "key_outcome",
                "claim_ids",
                "notes",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "experiment_id": "E001",
                "date": "2026-03-20",
                "short_name": "test",
                "type": "setup",
                "stimulus": "sugar",
                "perturbation_target": "none",
                "n_trials": "1",
                "duration_s": "1.0",
                "script_or_file": "test_run.py",
                "primary_output": "results/statistics.csv",
                "status": "validated",
                "key_outcome": "ok",
                "claim_ids": "C001",
                "notes": "",
            }
        )

    with (docs_root / "11_CLAIMS_REGISTER.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["claim_id", "claim", "evidence_files", "status", "caveat", "next_action", "safe_wording"],
        )
        writer.writeheader()
        writer.writerow(
            {
                "claim_id": "C001",
                "claim": "Engine works",
                "evidence_files": "test_run.py",
                "status": "validated-in-code",
                "caveat": "",
                "next_action": "",
                "safe_wording": "",
            }
        )

    with (docs_root / "04_RESULTS_LEDGER.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "result_id",
                "experiment_id",
                "date",
                "analysis_level",
                "condition_or_group",
                "metric",
                "value",
                "raw_p",
                "fdr_q",
                "status",
                "interpretation",
                "caveat",
                "paper_location",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "result_id": "R001",
                "experiment_id": "E001",
                "date": "2026-03-20",
                "analysis_level": "setup",
                "condition_or_group": "test",
                "metric": "ok",
                "value": "1",
                "raw_p": "",
                "fdr_q": "",
                "status": "completed",
                "interpretation": "ok",
                "caveat": "",
                "paper_location": "",
            }
        )


def test_validate_research_docs_passes_for_repo_pack():
    module = load_module()
    repo_root = Path.cwd()

    errors = module.validate_research_docs(
        repo_root,
        repo_root,
        check_evidence_files=True,
        check_validated_outputs=False,
    )

    assert errors == []


def test_validate_research_docs_rejects_unknown_claim_reference(tmp_path):
    module = load_module()
    repo_root = tmp_path / "repo"
    docs_root = repo_root / "docs"
    write_minimal_pack(docs_root)
    (repo_root / "test_run.py").write_text("print('ok')\n", encoding="utf-8")
    (repo_root / "results").mkdir()
    (repo_root / "results/statistics.csv").write_text("group,delta\n", encoding="utf-8")

    experiments = module.read_csv(docs_root / "03_EXPERIMENT_REGISTRY.csv")
    experiments[0]["claim_ids"] = "C999"
    with (docs_root / "03_EXPERIMENT_REGISTRY.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=experiments[0].keys())
        writer.writeheader()
        writer.writerows(experiments)

    errors = module.validate_research_docs(repo_root, docs_root, check_validated_outputs=False)

    assert any("references unknown claim_id: C999" in error for error in errors)


def test_validate_research_docs_rejects_missing_evidence_file(tmp_path):
    module = load_module()
    repo_root = tmp_path / "repo"
    docs_root = repo_root / "docs"
    write_minimal_pack(docs_root)
    (repo_root / "results").mkdir()
    (repo_root / "results/statistics.csv").write_text("group,delta\n", encoding="utf-8")

    claims = module.read_csv(docs_root / "11_CLAIMS_REGISTER.csv")
    claims[0]["evidence_files"] = "missing_script.py"
    with (docs_root / "11_CLAIMS_REGISTER.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=claims[0].keys())
        writer.writeheader()
        writer.writerows(claims)

    errors = module.validate_research_docs(repo_root, docs_root, check_validated_outputs=False)

    assert any("evidence file not found on disk: missing_script.py" in error for error in errors)


def test_validate_research_docs_rejects_duplicate_experiment_id(tmp_path):
    module = load_module()
    repo_root = tmp_path / "repo"
    docs_root = repo_root / "docs"
    write_minimal_pack(docs_root)
    (repo_root / "test_run.py").write_text("print('ok')\n", encoding="utf-8")
    (repo_root / "results").mkdir()
    (repo_root / "results/statistics.csv").write_text("group,delta\n", encoding="utf-8")

    experiments = module.read_csv(docs_root / "03_EXPERIMENT_REGISTRY.csv")
    duplicate = dict(experiments[0])
    with (docs_root / "03_EXPERIMENT_REGISTRY.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=experiments[0].keys())
        writer.writeheader()
        writer.writerows([experiments[0], duplicate])

    errors = module.validate_research_docs(repo_root, docs_root, check_validated_outputs=False)

    assert any("duplicate experiment_id: E001" in error for error in errors)


def test_validate_research_docs_skips_wildcard_evidence(tmp_path):
    module = load_module()
    repo_root = tmp_path / "repo"
    docs_root = repo_root / "docs"
    write_minimal_pack(docs_root)
    (repo_root / "results").mkdir()
    (repo_root / "results/statistics.csv").write_text("group,delta\n", encoding="utf-8")

    claims = module.read_csv(docs_root / "11_CLAIMS_REGISTER.csv")
    claims[0]["evidence_files"] = "notebook/scripts hq_*"
    with (docs_root / "11_CLAIMS_REGISTER.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=claims[0].keys())
        writer.writeheader()
        writer.writerows(claims)

    errors = module.validate_research_docs(repo_root, docs_root, check_validated_outputs=False)

    assert errors == []
