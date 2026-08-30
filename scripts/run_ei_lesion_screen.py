#!/usr/bin/env python3
"""Lesion excitatory vs inhibitory populations and compare motor ΔHz.

This is the first experiment of the reset scientific program. It does not
declare a winner among the competing accounts in docs/RESEARCH_QUESTION.md.

Default n_run is small so the command is a screen, not a paper claim.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from perturbation.baseline import NEU_SUGAR  # noqa: E402
from perturbation.cell_groups import NT_MAPS, get_group, get_polarity_group  # noqa: E402
from perturbation.perturb import run_single_perturbation  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--context", choices=["sugar", "none"], default="sugar")
    parser.add_argument("--nt-map", choices=sorted(NT_MAPS), default="classical_fast")
    parser.add_argument("--n-run", type=int, default=5)
    parser.add_argument(
        "--max-lesion",
        type=int,
        default=200,
        help="cap lesion size so a first screen is tractable",
    )
    parser.add_argument("--results-dir", default="results/ei_screen")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    neu_exc = list(NEU_SUGAR) if args.context == "sugar" else []
    results_dir = Path(args.results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)

    groups = {
        "excitatory": get_polarity_group("excitatory", nt_map=args.nt_map),
        "inhibitory": get_polarity_group("inhibitory", nt_map=args.nt_map),
        "motor": get_group(super_class="motor"),
    }

    rows = []
    for name, ids in groups.items():
        ids = [int(i) for i in ids]
        capped = bool(args.max_lesion and len(ids) > args.max_lesion)
        if capped:
            ids = ids[: args.max_lesion]
        exp_name = f"lesion_{args.nt_map}_{name}"
        print(f"{name}: n={len(ids)} capped={capped} map={args.nt_map}")
        rows.append(
            {
                "group": name,
                "nt_map": args.nt_map,
                "context": args.context,
                "n_silenced": len(ids),
                "capped": capped,
                "nt_map_description": NT_MAPS[args.nt_map]["description"],
            }
        )
        if args.dry_run:
            continue
        run_single_perturbation(
            neuron_ids=ids,
            exp_name=exp_name,
            force=args.force,
            results_dir=str(results_dir),
            n_run=args.n_run,
            neu_exc=neu_exc,
        )

    summary = pd.DataFrame(rows)
    out = results_dir / f"ei_screen_{args.context}_{args.nt_map}.csv"
    summary.to_csv(out, index=False)
    print(f"wrote {out}")
    print(summary.to_string(index=False))
    print("\nNT-map assumption (do not treat as fact):")
    print(NT_MAPS[args.nt_map]["description"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
