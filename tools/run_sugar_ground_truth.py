#!/usr/bin/env python3
"""CEO-007: run the 30-trial sugar ground-truth panel and bind manifests.

Pipeline:
1. Resolve connectome inputs via ``tools.path_resolver``.
2. Drive the 21 right sugar gustatory neurons for ``n_run`` Poisson trials.
3. Run sugar-self + size-matched control silences under the same drive.
4. Export Welch + Benjamini-Hochberg FDR statistics (raw ``p_value`` + ``p_value_fdr``).
5. Write ``output_manifest.json`` bound to config, seed, input checksums, and Parquets.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import pandas as pd
import yaml

_BOOTSTRAP_ROOT = Path(__file__).resolve().parents[1]
if str(_BOOTSTRAP_ROOT) not in sys.path:
    sys.path.insert(0, str(_BOOTSTRAP_ROOT))

from tools.path_resolver import ensure_repo_on_path, resolve_input, repo_root_from
from tools.write_output_manifest import (
    git_commit,
    input_manifest_checksums,
    read_json,
    sha256_file,
)

_REPO_ROOT = ensure_repo_on_path(Path(__file__))


def load_config(path: str | Path) -> dict:
    """Load a repo-relative YAML run config."""
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = _REPO_ROOT / candidate
    if not candidate.exists():
        raise FileNotFoundError(f"Config not found: {path}")
    data = yaml.safe_load(candidate.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Config must be a mapping: {path}")
    return data


def resolve_motor_ids(manifest_path: str, completeness_id: str) -> list[int]:
    """Load motor FlyWire IDs using manifest-resolved annotation + completeness tables."""
    ann_path = resolve_input("flywire_annotations.tsv", manifest_path=manifest_path, repo_root=_REPO_ROOT)
    comp_path = resolve_input(completeness_id, manifest_path=manifest_path, repo_root=_REPO_ROOT)
    ann = pd.read_csv(ann_path, sep="\t", low_memory=False)
    sim = pd.read_csv(comp_path, index_col=0)
    sim_ids = set(sim.index.astype("int64").tolist())
    # Keep IDs as Python ints without float coercion of the join key.
    ann = ann[ann["root_id"].isin(sim_ids)]
    motor = ann.loc[ann["super_class"] == "motor", "root_id"]
    return [int(x) for x in motor.tolist()]


def configure_brian2(codegen_target: str) -> None:
    os.environ.setdefault("BRIAN2_CODEGEN", codegen_target)
    from brian2 import prefs

    prefs.codegen.target = codegen_target


def write_bound_output_manifest(
    *,
    config_path: Path,
    config: dict,
    input_manifest_path: str,
    output_manifest_path: str,
    artifact_paths: list[str],
    status: str,
) -> Path:
    input_manifest = read_json(_REPO_ROOT / input_manifest_path)
    outputs = []
    for rel in artifact_paths:
        abs_path = _REPO_ROOT / rel
        if not abs_path.is_file():
            raise FileNotFoundError(f"Missing artifact for output manifest: {rel}")
        outputs.append(
            {
                "path": rel,
                "sha256": sha256_file(abs_path),
                "size_bytes": abs_path.stat().st_size,
            }
        )

    manifest = {
        "schema_version": "0.1",
        "status": status,
        "run_name": config.get("run_name"),
        "experiment_id": config.get("experiment_id"),
        "command": " ".join(sys.argv),
        "repo_commit": git_commit(_REPO_ROOT),
        "config_path": str(config_path.relative_to(_REPO_ROOT)),
        "config_sha256": sha256_file(config_path),
        "run_config": {
            "random_seed": config.get("random_seed"),
            "n_run": config.get("n_run"),
            "t_run_ms": config.get("t_run_ms"),
            "selected_materialization": config.get("selected_materialization"),
            "completeness_id": config.get("completeness_id"),
            "connectivity_id": config.get("connectivity_id"),
            "poisson_rate_hz": config.get("poisson_rate_hz"),
            "n_proc": config.get("n_proc"),
            "codegen_target": config.get("codegen_target"),
        },
        "input_manifest_path": input_manifest_path,
        "input_manifest_present": input_manifest is not None,
        "input_checksums": input_manifest_checksums(input_manifest),
        "outputs": outputs,
        "notes": config.get("notes") or [],
        "claim_status": config.get(
            "claim_status", "simulation_bound_pending_independent_validation"
        ),
    }
    out_path = _REPO_ROOT / output_manifest_path
    out_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default="configs/sugar_ground_truth_30trial.yaml",
        help="Repo-relative YAML config",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite existing Parquets")
    parser.add_argument(
        "--skip-perturbations",
        action="store_true",
        help="Only run baseline sugar (no FDR multi-condition panel)",
    )
    parser.add_argument(
        "--skip-statistics",
        action="store_true",
        help="Skip statistics export",
    )
    args = parser.parse_args(argv)

    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = _REPO_ROOT / config_path
    config = load_config(config_path)
    print(f"Loaded config: {config_path}", flush=True)

    configure_brian2(str(config.get("codegen_target", "numpy")))
    print("Brian2 codegen configured", flush=True)

    from perturbation.baseline import NEU_SUGAR, run_baseline
    from perturbation.perturb import (
        build_sugar_ground_truth_groups,
        run_perturbation_sweep,
    )
    from perturbation import statistics as statistics_mod

    print("Imported perturbation modules", flush=True)
    manifest_path = config.get("input_manifest", "data/input_manifest.json")
    completeness_id = config["completeness_id"]
    connectivity_id = config["connectivity_id"]
    results_dir = config.get("results_dir", "results/sugar_ground_truth")
    n_run = int(config.get("n_run", 30))
    t_run_ms = float(config.get("t_run_ms", 1000))
    seed = int(config.get("random_seed", 47))
    n_proc = int(config.get("n_proc", 1))
    baseline_name = config.get("baseline_exp_name", "baseline_sugar")

    # Confirm sugar IDs resolve against completeness via path_resolver.
    path_comp = resolve_input(completeness_id, manifest_path=manifest_path, repo_root=_REPO_ROOT)
    path_con = resolve_input(connectivity_id, manifest_path=manifest_path, repo_root=_REPO_ROOT)
    print(f"Resolved completeness: {path_comp}")
    print(f"Resolved connectivity: {path_con}")
    print(f"Sugar neurons: {len(NEU_SUGAR)}")

    print("=== CEO-007 baseline sugar ground truth ===")
    run_baseline(
        force=args.force,
        completeness_id=completeness_id,
        connectivity_id=connectivity_id,
        manifest_path=manifest_path,
        results_dir=results_dir,
        n_run=n_run,
        t_run_ms=t_run_ms,
        random_seed=seed,
        exp_name=baseline_name,
        n_proc=n_proc,
    )

    artifact_paths = [f"{results_dir}/{baseline_name}.parquet"]

    if not args.skip_perturbations:
        print("=== CEO-007 sugar-context perturbation panel ===")
        groups = build_sugar_ground_truth_groups(
            manifest_path=manifest_path,
            completeness_id=completeness_id,
            connectivity_id=connectivity_id,
            seed=int(config.get("control_seed", seed)),
            group_size=int(config.get("perturbation_group_size", len(NEU_SUGAR))),
        )
        # Persist silenced ID lists for provenance.
        results_root = _REPO_ROOT / results_dir
        results_root.mkdir(parents=True, exist_ok=True)
        groups_path = results_root / "perturbation_groups.json"
        groups_path.write_text(
            json.dumps({k: [str(i) for i in v] for k, v in groups.items()}, indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
        )
        artifact_paths.append(f"{results_dir}/perturbation_groups.json")

        run_perturbation_sweep(
            groups,
            force=args.force,
            manifest_path=manifest_path,
            completeness_id=completeness_id,
            connectivity_id=connectivity_id,
            results_dir=results_dir,
            n_run=n_run,
            t_run_ms=t_run_ms,
            random_seed=seed,
            n_proc=n_proc,
        )
        for name in groups:
            artifact_paths.append(f"{results_dir}/perturb_{name}.parquet")
        summary_rel = f"{results_dir}/perturbation_summary.csv"
        if (_REPO_ROOT / summary_rel).exists():
            artifact_paths.append(summary_rel)

    if not args.skip_statistics and not args.skip_perturbations:
        print("=== CEO-007 statistics (Welch + BH-FDR) ===")
        motor_ids = resolve_motor_ids(manifest_path, completeness_id)
        print(f"Motor neurons in join: {len(motor_ids)}")
        targets = [
            ("perturb_sugar_self", "sugar_self"),
            ("perturb_control_A", "control_A"),
            ("perturb_control_B", "control_B"),
        ]
        stats_name = config.get("statistics_output", "statistics.csv")
        statistics_mod.run_statistics(
            targets=targets,
            baseline_name=baseline_name,
            path_res=results_dir,
            output_name=stats_name,
            motor_ids=motor_ids,
            t_run=t_run_ms / 1000.0,
        )
        artifact_paths.append(f"{results_dir}/{stats_name}")

    out_manifest = write_bound_output_manifest(
        config_path=config_path,
        config=config,
        input_manifest_path=manifest_path,
        output_manifest_path=config.get("output_manifest", "output_manifest.json"),
        artifact_paths=artifact_paths,
        status="sugar_ground_truth_complete",
    )
    print(f"Wrote bound output manifest: {out_manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
