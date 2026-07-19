import importlib.util
import textwrap
from pathlib import Path

import yaml


def load_module():
    module_path = Path.cwd() / "tools/validate_research_docs.py"
    spec = importlib.util.spec_from_file_location("validate_research_docs", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def write_docs_config(repo_root: Path, minimum_claim_standard: dict | None = None) -> None:
    config = {
        "status_labels": ["planned", "exploratory", "validated", "revised", "negative", "deprecated"],
        "minimum_claim_standard": minimum_claim_standard
        or {
            "require_matched_trial_counts": True,
            "require_zero_spike_trial_retention": True,
            "require_fdr_correction": True,
            "exploratory_trial_count_label": "5-trial screen",
            "preferred_validation_trials": 30,
        },
    }
    (repo_root / "docs_config.yaml").write_text(yaml.safe_dump(config), encoding="utf-8")


def write_required_docs(repo_root: Path) -> None:
    for name in [
        "README.md",
        "00_PROJECT_STATE.md",
        "01_LIVING_RESEARCH_LOG.md",
        "02_METHODS_MASTER.md",
        "05_CODE_CHANGELOG.md",
        "06_DECISION_LOG.md",
        "07_ISSUES_AND_CAVEATS.md",
        "08_DATA_PROVENANCE.md",
        "09_REPRODUCIBILITY_CHECKLIST.md",
        "10_PUBLICATION_NARRATIVE_TRACKER.md",
        "12_LITERATURE_AND_SOURCE_NOTES.md",
    ]:
        path = repo_root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# {name}\n", encoding="utf-8")


def write_registry(
    repo_root: Path,
    experiments_csv: str,
    claims_csv: str = "claim_id,claim,evidence_files,status,caveat,next_action,safe_wording\n",
    results_csv: str = "result_id,experiment_id,date,analysis_level,condition_or_group,metric,value,raw_p,fdr_q,status,interpretation,caveat,paper_location\n",
) -> None:
    write_required_docs(repo_root)
    write_docs_config(repo_root)
    (repo_root / "03_EXPERIMENT_REGISTRY.csv").write_text(experiments_csv, encoding="utf-8")
    (repo_root / "11_CLAIMS_REGISTER.csv").write_text(claims_csv, encoding="utf-8")
    (repo_root / "04_RESULTS_LEDGER.csv").write_text(results_csv, encoding="utf-8")


def test_committed_registry_passes_minimum_claim_standard():
    module = load_module()
    errors = module.validate_research_docs(Path.cwd())
    assert errors == [], errors


def test_rejects_validated_experiment_with_five_trials(tmp_path):
    module = load_module()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    write_registry(
        repo_root,
        textwrap.dedent(
            """\
            experiment_id,date,short_name,type,stimulus,perturbation_target,n_trials,duration_s,script_or_file,primary_output,status,key_outcome,claim_ids,notes
            E099,2026-04-02,bad_validation,perturbation,sugar,sensory,5,1.0,perturb.py,results/bad.csv,validated,claimed validated,C004,Missing exploratory caveat
            """
        ),
        claims_csv=textwrap.dedent(
            """\
            claim_id,claim,evidence_files,status,caveat,next_action,safe_wording
            C004,Significant motor effect,statistics.py,validated pending exact q-values,,,
            """
        ),
    )
    errors = module.validate_research_docs(repo_root)
    assert any("records 5 trials" in error for error in errors)


def test_rejects_exploratory_experiment_with_thirty_trials(tmp_path):
    module = load_module()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    write_registry(
        repo_root,
        textwrap.dedent(
            """\
            experiment_id,date,short_name,type,stimulus,perturbation_target,n_trials,duration_s,script_or_file,primary_output,status,key_outcome,claim_ids,notes
            E099,2026-04-02,mislabeled,perturbation screen,sugar,sensory,30,1.0,perturb.py,results/screen.csv,exploratory,screen result,,5-trial screen label only in notes
            """
        ),
    )
    errors = module.validate_research_docs(repo_root)
    assert any("is exploratory but records 30 trials" in error for error in errors)


def test_rejects_unmatched_validated_trial_counts(tmp_path):
    module = load_module()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    write_registry(
        repo_root,
        textwrap.dedent(
            """\
            experiment_id,date,short_name,type,stimulus,perturbation_target,n_trials,duration_s,script_or_file,primary_output,status,key_outcome,claim_ids,notes
            E099,2026-04-02,unmatched,statistical validation,sugar,sensory,30 baseline; 5 perturbation,1.0,statistics.py,results/statistics.csv,validated,stats,,Use FDR q-values
            """
        ),
    )
    errors = module.validate_research_docs(repo_root)
    assert any("trial counts are not matched" in error for error in errors)


def test_rejects_exploratory_reference_to_validated_claim_without_caveat(tmp_path):
    module = load_module()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    write_registry(
        repo_root,
        textwrap.dedent(
            """\
            experiment_id,date,short_name,type,stimulus,perturbation_target,n_trials,duration_s,script_or_file,primary_output,status,key_outcome,claim_ids,notes
            E099,2026-04-02,screen,perturbation screen,sugar,sensory,5,1.0,perturb.py,results/screen.csv,exploratory,net positive effect,C004,No caveat recorded
            """
        ),
        claims_csv=textwrap.dedent(
            """\
            claim_id,claim,evidence_files,status,caveat,next_action,safe_wording
            C004,Significant motor effect,statistics.py,validated pending exact q-values,,,
            """
        ),
    )
    errors = module.validate_research_docs(repo_root)
    assert any("without an exploratory caveat" in error for error in errors)


def test_rejects_validated_statistical_experiment_without_fdr_documentation(tmp_path):
    module = load_module()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    write_registry(
        repo_root,
        textwrap.dedent(
            """\
            experiment_id,date,short_name,type,stimulus,perturbation_target,n_trials,duration_s,script_or_file,primary_output,status,key_outcome,claim_ids,notes
            E099,2026-04-02,stats,statistical validation,sugar,sensory,30,1.0,statistics.py,results/statistics.csv,validated,stats,,No multiple-testing correction note
            """
        ),
    )
    errors = module.validate_research_docs(repo_root)
    assert any("does not document FDR correction" in error for error in errors)


def test_rejects_validated_result_with_raw_p_but_no_fdr(tmp_path):
    module = load_module()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    write_registry(
        repo_root,
        textwrap.dedent(
            """\
            experiment_id,date,short_name,type,stimulus,perturbation_target,n_trials,duration_s,script_or_file,primary_output,status,key_outcome,claim_ids,notes
            E099,2026-04-02,stats,statistical validation,sugar,sensory,30,1.0,statistics.py,results/statistics.csv,validated,stats,,No multiple-testing correction note
            """
        ),
        results_csv=textwrap.dedent(
            """\
            result_id,experiment_id,date,analysis_level,condition_or_group,metric,value,raw_p,fdr_q,status,interpretation,caveat,paper_location
            R099,E099,2026-04-02,statistics,sensory,motor_delta_hz,-10.0,0.01,,validated in notebook,significant,,
            """
        ),
    )
    errors = module.validate_research_docs(repo_root)
    assert any("reports raw p-values without FDR q-values" in error for error in errors)


def test_optional_benchmark_tier_mismatch_is_reported(tmp_path):
    module = load_module()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    write_registry(
        repo_root,
        textwrap.dedent(
            """\
            experiment_id,date,short_name,type,stimulus,perturbation_target,n_trials,duration_s,script_or_file,primary_output,status,key_outcome,claim_ids,notes
            E099,2026-04-02,sweep,perturbation screen,sugar,sensory,5,1.0,perturb.py,results/screen.csv,exploratory,screen result,,Exploratory 5-trial screen
            """
        ),
    )
    benchmark_path = repo_root / "data/benchmark_registry.yaml"
    benchmark_path.parent.mkdir(parents=True, exist_ok=True)
    benchmark_path.write_text(
        yaml.safe_dump(
            {
                "benchmarks": {
                    "BM099": {
                        "experiment_id": "E099",
                        "claim_tier": "infrastructure",
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    errors = module.validate_research_docs(repo_root)
    assert any("does not match benchmark tier infrastructure" in error for error in errors)


def test_skip_minimum_claim_standard_preserves_backwards_compatibility(tmp_path):
    module = load_module()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    write_registry(
        repo_root,
        textwrap.dedent(
            """\
            experiment_id,date,short_name,type,stimulus,perturbation_target,n_trials,duration_s,script_or_file,primary_output,status,key_outcome,claim_ids,notes
            E099,2026-04-02,bad_validation,perturbation,sugar,sensory,5,1.0,perturb.py,results/bad.csv,validated,claimed validated,C004,Missing exploratory caveat
            """
        ),
        claims_csv=textwrap.dedent(
            """\
            claim_id,claim,evidence_files,status,caveat,next_action,safe_wording
            C004,Significant motor effect,statistics.py,validated pending exact q-values,,,
            """
        ),
    )
    errors = module.validate_research_docs(repo_root, require_minimum_claim_standard=False)
    assert errors == []
