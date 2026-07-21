"""Run the baseline sugar stimulation experiment.

This entry point resolves input data through ``data/input_manifest.json`` by
filename via ``tools.path_resolver.resolve_input``. Scripts remain runnable
from any working directory.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Bootstrap: make the repository root importable before loading the resolver.
_BOOTSTRAP_ROOT = Path(__file__).resolve().parents[1]
if str(_BOOTSTRAP_ROOT) not in sys.path:
    sys.path.insert(0, str(_BOOTSTRAP_ROOT))

from tools.path_resolver import ensure_repo_on_path, resolve_input

_REPO_ROOT = ensure_repo_on_path(Path(__file__))

from brian2 import ms  # noqa: E402

from model import default_params, run_exp  # noqa: E402

PARAMS = default_params.copy()
PARAMS["n_run"] = 5
PARAMS["t_run"] = 1000 * ms

DEFAULT_COMPLETENESS_ID = "2023_03_23_completeness_630_final.csv"
DEFAULT_CONNECTIVITY_ID = "2023_03_23_connectivity_630_final.parquet"
DEFAULT_RESULTS_DIR = "results"
DEFAULT_MANIFEST_PATH = "data/input_manifest.json"
DEFAULT_EXP_NAME = "baseline_sugar"

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
    manifest_path: str = DEFAULT_MANIFEST_PATH,
    repo_root: Path | None = None,
) -> tuple[Path, Path]:
    """Resolve baseline input files from the manifest.

    The defaults intentionally use exact filenames rather than vague roles,
    because the manifest can contain multiple connectivity/completeness tables
    and the resolver refuses ambiguous identifiers.

    ``repo_root`` defaults to this file's repository so resolution does not
    depend on the caller's current working directory.
    """
    root = repo_root if repo_root is not None else Path(__file__)
    path_comp = resolve_input(
        completeness_id, manifest_path=manifest_path, repo_root=root
    )
    path_con = resolve_input(
        connectivity_id, manifest_path=manifest_path, repo_root=root
    )
    return path_comp, path_con


def resolve_results_dir(results_dir: str | Path, repo_root: Path | None = None) -> Path:
    """Resolve a results directory through the repository root when relative."""
    root = repo_root if repo_root is not None else _REPO_ROOT
    path = Path(results_dir)
    if path.is_absolute():
        return path
    return (root / path).resolve()


def build_run_params(
    n_run: int | None = None,
    t_run_ms: float | None = None,
    random_seed: int | None = None,
) -> dict:
    """Return Brian2 params for a sugar baseline/perturbation run."""
    params = PARAMS.copy()
    if n_run is not None:
        params["n_run"] = int(n_run)
    if t_run_ms is not None:
        params["t_run"] = float(t_run_ms) * ms
    if random_seed is not None:
        params["random_seed"] = int(random_seed)
    return params


def run_baseline(
    force: bool = False,
    completeness_id: str = DEFAULT_COMPLETENESS_ID,
    connectivity_id: str = DEFAULT_CONNECTIVITY_ID,
    manifest_path: str = DEFAULT_MANIFEST_PATH,
    results_dir: str = DEFAULT_RESULTS_DIR,
    n_run: int | None = None,
    t_run_ms: float | None = None,
    random_seed: int | None = None,
    exp_name: str = DEFAULT_EXP_NAME,
    n_proc: int = 1,
) -> Path | None:
    path_comp, path_con = resolve_baseline_inputs(
        completeness_id=completeness_id,
        connectivity_id=connectivity_id,
        manifest_path=manifest_path,
        repo_root=Path(__file__),
    )
    results_path = resolve_results_dir(results_dir)
    results_path.mkdir(parents=True, exist_ok=True)
    params = build_run_params(n_run=n_run, t_run_ms=t_run_ms, random_seed=random_seed)
    print("Running baseline simulation with manifest-resolved inputs...")
    print(f"Completeness: {path_comp}")
    print(f"Connectivity: {path_con}")
    print(f"n_run={params['n_run']} seed={params.get('random_seed')}")
    return run_exp(
        exp_name=exp_name,
        neu_exc=NEU_SUGAR,
        path_res=str(results_path),
        path_comp=str(path_comp),
        path_con=str(path_con),
        params=params,
        n_proc=n_proc,
        force_overwrite=force,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="Overwrite existing baseline outputs")
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST_PATH, help="Input manifest path")
    parser.add_argument(
        "--completeness-id",
        default=DEFAULT_COMPLETENESS_ID,
        help="Manifest identifier for completeness table",
    )
    parser.add_argument(
        "--connectivity-id",
        default=DEFAULT_CONNECTIVITY_ID,
        help="Manifest identifier for connectivity table",
    )
    parser.add_argument("--results-dir", default=DEFAULT_RESULTS_DIR, help="Directory for run outputs")
    parser.add_argument("--n-run", type=int, default=None, help="Trial count (default: PARAMS n_run)")
    parser.add_argument("--t-run-ms", type=float, default=None, help="Trial duration in ms")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for Poisson trials")
    parser.add_argument("--exp-name", default=DEFAULT_EXP_NAME, help="Output experiment name")
    parser.add_argument("--n-proc", type=int, default=1, help="Parallel workers (1 recommended)")
    args = parser.parse_args(argv)
    run_baseline(
        force=args.force,
        completeness_id=args.completeness_id,
        connectivity_id=args.connectivity_id,
        manifest_path=args.manifest,
        results_dir=args.results_dir,
        n_run=args.n_run,
        t_run_ms=args.t_run_ms,
        random_seed=args.seed,
        exp_name=args.exp_name,
        n_proc=args.n_proc,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
