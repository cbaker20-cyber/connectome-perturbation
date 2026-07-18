"""Run the baseline sugar stimulation experiment.

This entry point now resolves input data through ``data/input_manifest.json`` by
filename by default. That keeps the legacy experiment runnable while forcing the
next validation step to depend on a manifest/checksum record instead of hidden
hard-coded data assumptions.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from brian2 import ms

from model import default_params, run_exp
from tools.path_resolver import ensure_repo_on_path, resolve_input

ensure_repo_on_path(Path(__file__))

PARAMS = default_params.copy()
PARAMS["n_run"] = 5
PARAMS["t_run"] = 1000 * ms

DEFAULT_COMPLETENESS_ID = "2023_03_23_completeness_630_final.csv"
DEFAULT_CONNECTIVITY_ID = "2023_03_23_connectivity_630_final.parquet"
DEFAULT_RESULTS_DIR = "results"

NEU_SUGAR = [
    720575940624963786,
    720575940630233916,
    720575940637568838,
    720575940638202345,
    720575940617000768,
    720575940630797113,
    720575940632889389,
    720575940621754367,
    720575940621502051,
    720575940640649691,
    720575940639332736,
    720575940616885538,
    720575940639198653,
    720575940620900446,
    720575940617937543,
    720575940632425919,
    720575940633143833,
    720575940612670570,
    720575940628853239,
    720575940629176663,
    720575940611875570,
]


def resolve_baseline_inputs(
    completeness_id: str = DEFAULT_COMPLETENESS_ID,
    connectivity_id: str = DEFAULT_CONNECTIVITY_ID,
    manifest_path: str = "data/input_manifest.json",
    repo_root: Path | None = None,
) -> tuple[Path, Path]:
    """Resolve baseline input files from the manifest.

    The defaults intentionally use exact filenames rather than vague roles,
    because the manifest can contain multiple connectivity/completeness tables
    and the resolver refuses ambiguous identifiers.
    """

    path_comp = resolve_input(completeness_id, manifest_path=manifest_path, repo_root=repo_root)
    path_con = resolve_input(connectivity_id, manifest_path=manifest_path, repo_root=repo_root)
    return path_comp, path_con


def run_baseline(
    force: bool = False,
    completeness_id: str = DEFAULT_COMPLETENESS_ID,
    connectivity_id: str = DEFAULT_CONNECTIVITY_ID,
    manifest_path: str = "data/input_manifest.json",
    results_dir: str = DEFAULT_RESULTS_DIR,
) -> None:
    path_comp, path_con = resolve_baseline_inputs(
        completeness_id=completeness_id,
        connectivity_id=connectivity_id,
        manifest_path=manifest_path,
    )
    Path(results_dir).mkdir(exist_ok=True)
    print("Running baseline simulation with manifest-resolved inputs...")
    print(f"Completeness: {path_comp}")
    print(f"Connectivity: {path_con}")
    run_exp(
        exp_name="baseline_sugar",
        neu_exc=NEU_SUGAR,
        path_res=results_dir,
        path_comp=str(path_comp),
        path_con=str(path_con),
        params=PARAMS,
        n_proc=1,
        force_overwrite=force,
    )
    print("Baseline done.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="Overwrite existing baseline outputs")
    parser.add_argument("--manifest", default="data/input_manifest.json", help="Input manifest path")
    parser.add_argument("--completeness-id", default=DEFAULT_COMPLETENESS_ID, help="Manifest identifier for completeness table")
    parser.add_argument("--connectivity-id", default=DEFAULT_CONNECTIVITY_ID, help="Manifest identifier for connectivity table")
    parser.add_argument("--results-dir", default=DEFAULT_RESULTS_DIR, help="Directory for run outputs")
    args = parser.parse_args(argv)
    run_baseline(
        force=args.force,
        completeness_id=args.completeness_id,
        connectivity_id=args.connectivity_id,
        manifest_path=args.manifest,
        results_dir=args.results_dir,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
