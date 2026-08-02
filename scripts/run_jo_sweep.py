#!/usr/bin/env python3
"""Run the Johnston's Organ (JO) 30-trial ground-truth baseline and perturbation sweep.

Resolves all inputs through ``tools.path_resolver`` / ``data/input_manifest.json``.
Uses ``perturbation/perturb.py`` for silencing sweeps with JO neurons as ``neu_exc``.

This script records reproducibility metadata. It does not authorize neuroscience claims.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.path_resolver import resolve_input, repo_root_from  # noqa: E402


DEFAULT_CONFIG = "configs/jo_ground_truth_30trial.yaml"
SPIKE_PARQUET_COLUMNS = ("t", "trial", "flywire_id", "exp_name")


def load_config(path: Path) -> dict[str, Any]:
    """Load and minimally validate the JO sweep YAML config."""

    if not path.is_file():
        raise FileNotFoundError(f"Config not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Config must be a mapping: {path}")
    for key in ("run_name", "random_seed", "simulation", "paths", "sensory_input"):
        if key not in data:
            raise ValueError(f"Config missing required key {key!r}")
    sensory = data["sensory_input"]
    if "root_ids" not in sensory or not sensory["root_ids"]:
        raise ValueError("sensory_input.root_ids must be a non-empty list")
    if "expected_count" in sensory and len(sensory["root_ids"]) != int(sensory["expected_count"]):
        raise ValueError(
            f"sensory_input.root_ids length {len(sensory['root_ids'])} "
            f"!= expected_count {sensory['expected_count']}"
        )
    return data


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_commit(repo_root: Path) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return None


def load_annotations(annotations_path: Path) -> pd.DataFrame:
    return pd.read_csv(annotations_path, sep="\t", low_memory=False)


def load_sim_ids(completeness_path: Path) -> set[int]:
    df = pd.read_csv(completeness_path, index_col=0)
    return {int(x) for x in df.index.tolist()}


def _allowed_jo_cell_types(selection: dict[str, Any]) -> set[str]:
    groups = selection.get("cell_type_groups") or {}
    allowed: set[str] = set()
    for types in groups.values():
        allowed.update(str(t) for t in types)
    return allowed


def _normalize_root_id(value: Any) -> str:
    """Normalize FlyWire root IDs as strings to avoid int32 truncation on Windows."""

    return str(value).strip()


def select_jo_neurons(
    annotations: pd.DataFrame,
    sim_ids: set[int],
    sensory_input: dict[str, Any],
    *,
    require_curated: bool = True,
) -> list[int]:
    """Return curated JO root IDs after validating annotation/sim membership.

    Selection rules come from ``sensory_input.selection``. Curated ``root_ids`` are
    the authoritative stimulation set (methods: 146 JO neurons).
    """

    selection = sensory_input.get("selection") or {}
    curated = [_normalize_root_id(x) for x in sensory_input["root_ids"]]
    allowed_types = _allowed_jo_cell_types(selection)
    sim_ids_str = {_normalize_root_id(x) for x in sim_ids}

    ann = annotations.copy()
    ann["root_id"] = ann["root_id"].map(_normalize_root_id)
    mask = ann["root_id"].isin(sim_ids_str)
    if selection.get("super_class"):
        mask &= ann["super_class"] == selection["super_class"]
    if selection.get("cell_class"):
        mask &= ann["cell_class"] == selection["cell_class"]
    if selection.get("side"):
        mask &= ann["side"] == selection["side"]
    if allowed_types:
        mask &= ann["cell_type"].isin(allowed_types)

    labeled = set(ann.loc[mask, "root_id"].tolist())
    missing_sim = [i for i in curated if i not in sim_ids_str]
    if missing_sim:
        raise ValueError(
            f"{len(missing_sim)} curated JO root_ids are absent from the completeness table "
            f"(examples: {missing_sim[:5]})"
        )

    if require_curated:
        unlabeled = [i for i in curated if i not in labeled]
        # One historical root may lack a matching annotation row; allow at most one.
        if len(unlabeled) > 1:
            raise ValueError(
                f"{len(unlabeled)} curated JO root_ids fail annotation filters "
                f"(examples: {unlabeled[:5]})"
            )
        return [int(x) for x in curated]

    return sorted(int(x) for x in labeled)


def select_perturbation_groups(
    annotations: pd.DataFrame,
    sim_ids: set[int],
    group_specs: list[dict[str, Any]],
    *,
    exclude_ids: set[int] | None = None,
) -> dict[str, list[int]]:
    """Select silencing groups from FlyWire annotations intersected with sim neurons."""

    exclude_ids_str = {_normalize_root_id(x) for x in (exclude_ids or set())}
    sim_ids_str = {_normalize_root_id(x) for x in sim_ids}
    ann = annotations.copy()
    ann["root_id"] = ann["root_id"].map(_normalize_root_id)
    ann = ann[ann["root_id"].isin(sim_ids_str)]

    groups: dict[str, list[int]] = {}
    for spec in group_specs:
        name = str(spec["name"])
        by = str(spec["by"])
        value = spec["value"]
        if by not in ann.columns:
            raise ValueError(f"Unknown annotation column for group {name!r}: {by}")
        ids = [
            int(i)
            for i in ann.loc[ann[by] == value, "root_id"].tolist()
            if i not in exclude_ids_str
        ]
        if not ids:
            raise ValueError(f"Perturbation group {name!r} matched zero simulated neurons")
        groups[name] = ids
    return groups


def input_checksum_records(manifest_path: Path) -> list[dict[str, Any]]:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    records = []
    for item in payload.get("inputs", []):
        if not isinstance(item, dict):
            continue
        records.append(
            {
                "path": item.get("path"),
                "sha256": item.get("sha256"),
                "size_bytes": item.get("size_bytes"),
            }
        )
    return records


def build_output_manifest(
    config: dict[str, Any],
    config_path: str,
    *,
    repo_root: Path,
    command: list[str],
    jo_ids: list[int],
    groups: dict[str, list[int]],
    artifact_paths: list[str] | None = None,
) -> dict[str, Any]:
    """Bind output-manifest schema fields for the JO sweep."""

    paths = config["paths"]
    sim = config["simulation"]
    schema = config.get("output_manifest_schema") or {}
    spike = schema.get("spike_parquet") or {}
    input_manifest_rel = paths["input_manifest"]
    input_manifest_path = repo_root / input_manifest_rel
    config_abs = repo_root / config_path

    declared_outputs: list[dict[str, Any]] = []
    baseline_name = sim["baseline_exp_name"]
    spike_defs = [
        {
            "path": f"{paths['results_dir']}/{baseline_name}.parquet",
            "role": "baseline_spikes",
            "format": spike.get("format", "parquet"),
            "compression": spike.get("compression", "brotli"),
            "columns": list(spike.get("columns") or SPIKE_PARQUET_COLUMNS),
        }
    ]
    for group_name in groups:
        spike_defs.append(
            {
                "path": f"{paths['results_dir']}/perturb_{group_name}.parquet",
                "role": "perturbation_spikes",
                "group": group_name,
                "format": spike.get("format", "parquet"),
                "compression": spike.get("compression", "brotli"),
                "columns": list(spike.get("columns") or SPIKE_PARQUET_COLUMNS),
            }
        )

    for artifact in artifact_paths or []:
        abs_path = repo_root / artifact
        record: dict[str, Any] = {"path": artifact}
        if abs_path.is_file():
            record["sha256"] = sha256_file(abs_path)
            record["size_bytes"] = abs_path.stat().st_size
        declared_outputs.append(record)

    manifest = {
        "schema_version": schema.get("schema_version", "0.1"),
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "jo_ground_truth_sweep",
        "run_name": config["run_name"],
        "context": config.get("context", "grooming_jo"),
        "random_seed": config["random_seed"],
        "command": " ".join(command),
        "repo_commit": git_commit(repo_root),
        "config_path": config_path,
        "config_sha256": sha256_file(config_abs) if config_abs.is_file() else None,
        "input_manifest_path": input_manifest_rel,
        "input_manifest_present": input_manifest_path.is_file(),
        "input_checksums": input_checksum_records(input_manifest_path)
        if input_manifest_path.is_file()
        else [],
        "simulation": {
            "n_run": sim["n_run"],
            "t_run_ms": sim["t_run_ms"],
            "r_poi_hz": sim["r_poi_hz"],
            "baseline_exp_name": baseline_name,
            "n_jo_neurons": len(jo_ids),
            "perturbation_groups": {
                name: {"n_silenced": len(ids)} for name, ids in groups.items()
            },
        },
        "spike_parquet": spike_defs,
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "executable": sys.executable,
        },
        "outputs": declared_outputs,
        "notes": schema.get("notes")
        or [
            "JO sweep metadata for dual-context comparison; not interpretable as neuroscience alone."
        ],
        "claim_status": config.get("claim_status", "not_interpretable_as_neuroscience"),
    }

    required = schema.get("required_fields") or ["random_seed", "input_checksums", "outputs"]
    missing = [field for field in required if field not in manifest]
    if missing:
        raise ValueError(f"output manifest missing required fields: {missing}")
    return manifest


def prepare_jo_sweep(
    config: dict[str, Any],
    repo_root: Path | None = None,
) -> tuple[list[int], dict[str, list[int]], dict[str, Path]]:
    """Resolve paths and select JO / perturbation neuron groups."""

    root = repo_root_from(repo_root)
    paths_cfg = config["paths"]
    annotations_path = resolve_input(
        paths_cfg["annotations_id"],
        manifest_path=paths_cfg["input_manifest"],
        repo_root=root,
    )
    completeness_path = resolve_input(
        paths_cfg["completeness_id"],
        manifest_path=paths_cfg["input_manifest"],
        repo_root=root,
    )
    connectivity_path = resolve_input(
        paths_cfg["connectivity_id"],
        manifest_path=paths_cfg["input_manifest"],
        repo_root=root,
    )
    annotations = load_annotations(annotations_path)
    sim_ids = load_sim_ids(completeness_path)
    jo_ids = select_jo_neurons(annotations, sim_ids, config["sensory_input"])
    groups = select_perturbation_groups(
        annotations,
        sim_ids,
        config.get("perturbation_groups") or [],
        exclude_ids=set(jo_ids),
    )
    resolved = {
        "annotations": annotations_path,
        "completeness": completeness_path,
        "connectivity": connectivity_path,
        "results_dir": root / paths_cfg["results_dir"],
        "output_manifest": root / paths_cfg["output_manifest"],
        "input_manifest": root / paths_cfg["input_manifest"],
    }
    return jo_ids, groups, resolved


def run_jo_baseline(
    config: dict[str, Any],
    jo_ids: list[int],
    *,
    force: bool = False,
) -> None:
    """Run JO sensory baseline (no silencing) via perturbation/perturb.py."""

    from perturbation.perturb import run_single_perturbation

    paths = config["paths"]
    sim = config["simulation"]
    run_single_perturbation(
        neuron_ids=[],
        exp_name=sim["baseline_exp_name"],
        force=force or bool(sim.get("force_overwrite")),
        manifest_path=paths["input_manifest"],
        completeness_id=paths["completeness_id"],
        connectivity_id=paths["connectivity_id"],
        results_dir=paths["results_dir"],
        n_run=int(sim["n_run"]),
        neu_exc=jo_ids,
    )


def execute_sweep(
    config: dict[str, Any],
    jo_ids: list[int],
    groups: dict[str, list[int]],
    *,
    force: bool = False,
    skip_baseline: bool = False,
) -> pd.DataFrame:
    from perturbation import perturb as perturb_mod
    from perturbation.perturb import run_perturbation_sweep

    paths = config["paths"]
    sim = config["simulation"]
    Path(paths["results_dir"]).mkdir(parents=True, exist_ok=True)

    # Bind 30-trial / 150 Hz / 1000 ms from config into the shared PARAMS used by perturb.py.
    try:
        from brian2 import Hz, ms
        from model import default_params

        params = default_params.copy()
        params["n_run"] = int(sim["n_run"])
        params["t_run"] = float(sim["t_run_ms"]) * ms
        params["r_poi"] = float(sim["r_poi_hz"]) * Hz
        perturb_mod.PARAMS = params
    except Exception as exc:  # pragma: no cover - environment-dependent
        print(f"Warning: could not bind Brian2 params ({exc}); using perturb.PARAMS defaults")

    if not skip_baseline:
        print(f"=== JO baseline ({len(jo_ids)} sensory neurons, n_run={sim['n_run']}) ===")
        run_jo_baseline(config, jo_ids, force=force)

    print(f"=== JO perturbation sweep ({len(groups)} groups) ===")
    return run_perturbation_sweep(
        groups,
        force=force or bool(sim.get("force_overwrite")),
        manifest_path=paths["input_manifest"],
        completeness_id=paths["completeness_id"],
        connectivity_id=paths["connectivity_id"],
        results_dir=paths["results_dir"],
        n_run=int(sim["n_run"]),
        neu_exc=jo_ids,
        baseline_name=sim["baseline_exp_name"],
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=DEFAULT_CONFIG, help="Repo-relative JO sweep config YAML")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Resolve paths and select groups only; write output manifest without Brian2",
    )
    parser.add_argument("--skip-baseline", action="store_true", help="Skip baseline_jo when running the sweep")
    parser.add_argument("--force", action="store_true", help="Overwrite existing parquet outputs")
    parser.add_argument(
        "--n-trials",
        type=int,
        default=None,
        help="Override config simulation.n_run (trial count) for this execution",
    )
    args = parser.parse_args(argv)

    repo_root = repo_root_from()
    config_path = Path(args.config)
    if config_path.is_absolute():
        raise ValueError("--config must be repo-relative")
    config = load_config(repo_root / config_path)
    if args.n_trials is not None:
        if args.n_trials < 1:
            raise ValueError("--n-trials must be a positive integer")
        config["simulation"]["n_run"] = int(args.n_trials)
        print(f"Overriding simulation.n_run -> {args.n_trials}")

    jo_ids, groups, resolved = prepare_jo_sweep(config, repo_root=repo_root)
    print(f"Resolved annotations: {resolved['annotations']}")
    print(f"Resolved completeness: {resolved['completeness']}")
    print(f"Resolved connectivity: {resolved['connectivity']}")
    print(f"JO sensory neurons: {len(jo_ids)}")
    for name, ids in groups.items():
        print(f"  group {name}: {len(ids)} neurons")

    resolved["results_dir"].mkdir(parents=True, exist_ok=True)

    if not args.dry_run:
        execute_sweep(
            config,
            jo_ids,
            groups,
            force=args.force,
            skip_baseline=args.skip_baseline,
        )

    artifact_paths = []
    summary_path = resolved["results_dir"] / "perturbation_summary.csv"
    if summary_path.is_file():
        artifact_paths.append(str(summary_path.relative_to(repo_root)))

    manifest = build_output_manifest(
        config,
        args.config,
        repo_root=repo_root,
        command=["python", "scripts/run_jo_sweep.py", *(argv or sys.argv[1:])],
        jo_ids=jo_ids,
        groups=groups,
        artifact_paths=artifact_paths,
    )
    out_path = resolved["output_manifest"]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote output manifest: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
