"""
fix_two_sided_p.py

Corrects the empirical_p_two_sided formula in every degree/distance-matched
null summary CSV under a results/ tree, using each group's own *_perms.csv
as ground truth (recomputes null_mean, null_std, z_score, empirical_p_one_sided
too, and WARNS if a summary file disagrees with the perms file on anything
other than the two-sided p-value -- that disagreement means the summary file
is stale/from a different run, not just buggy, and should not be silently
overwritten).

Bug being fixed (scripts/run_degree_matched_nulls.py, historical line ~308):
    n_extreme_two = np.sum(np.abs(null_arr) >= abs(obs_delta))         # WRONG: distance from 0
Corrected:
    n_extreme_two = np.sum(np.abs(null_arr - null_mean) >= abs(obs_delta - null_mean))  # distance from null mean

Usage:
    python fix_two_sided_p.py --results-dir results --apply
    (omit --apply to do a dry run that only prints the report)
"""
import argparse
import csv
from pathlib import Path
import numpy as np
import pandas as pd

TOL = 1e-6

def recompute(perms_vals: np.ndarray, obs: float) -> dict:
    n = len(perms_vals)
    null_mean = float(np.mean(perms_vals))
    null_std = float(np.std(perms_vals, ddof=1)) if n > 1 else float("nan")
    z = (obs - null_mean) / null_std if null_std and null_std > 0 else float("nan")

    n_extreme_one = int(np.sum(perms_vals <= obs)) if obs < 0 else int(np.sum(perms_vals >= obs))
    p_one = (n_extreme_one + 1) / (n + 1)

    n_extreme_two = int(np.sum(np.abs(perms_vals - null_mean) >= abs(obs - null_mean)))
    p_two = (n_extreme_two + 1) / (n + 1)

    return dict(n_permutations=n, null_mean=null_mean, null_std=null_std,
                z_score=z, empirical_p_one_sided=p_one, empirical_p_two_sided=p_two)


def find_group_from_perms_filename(path: Path):
    # e.g. jo_degree_matched_nulls_Kenyon_Cell_perms.csv -> kind=jo_degree_matched_nulls, group=Kenyon_Cell
    stem = path.stem  # strip .csv
    assert stem.endswith("_perms")
    stem = stem[: -len("_perms")]
    # kind is one of the three known prefixes
    for kind in ("jo_degree_matched_nulls", "jo_distance_matched_nulls", "sugar_degree_matched_nulls", "sugar_distance_matched_nulls"):
        if stem.startswith(kind + "_"):
            group = stem[len(kind) + 1 :]
            return kind, group
    return None, None


def process(results_dir: Path, apply: bool):
    report_rows = []
    perms_files = sorted(results_dir.rglob("*_perms.csv"))
    for pf in perms_files:
        kind, group = find_group_from_perms_filename(pf)
        if kind is None:
            print(f"SKIP (unrecognized name pattern): {pf}")
            continue
        perms_df = pd.read_csv(pf)
        if "delta_hz" not in perms_df.columns:
            print(f"SKIP (no delta_hz column): {pf}")
            continue
        vals = perms_df["delta_hz"].to_numpy(dtype=float)

        # candidate summary files, in priority order
        candidates = [
            pf.parent / f"{kind}_{group}.csv",          # per-group file
            pf.parent / f"{kind}.csv",                    # combined/default file
            pf.parent / f"{kind}_ALL_GROUPS.csv",          # combined file, alt name
        ]
        summary_path, summary_row_idx, summary_df, obs = None, None, None, None
        for cand in candidates:
            if not cand.exists():
                continue
            df = pd.read_csv(cand)
            if "group" in df.columns:
                match = df.index[df["group"].str.lower() == group.lower()]
                if len(match) == 1:
                    summary_path, summary_row_idx, summary_df = cand, match[0], df
                    obs = float(df.loc[match[0], "observed_delta_hz"])
                    break
            elif len(df) == 1 and "observed_delta_hz" in df.columns:
                summary_path, summary_row_idx, summary_df = cand, 0, df
                obs = float(df.loc[0, "observed_delta_hz"])
                break
        if summary_path is None:
            print(f"NO SUMMARY FOUND for {pf} (group={group}, kind={kind}) -- skipping")
            continue

        recomputed = recompute(vals, obs)
        old_row = summary_df.loc[summary_row_idx]

        stale_flags = []
        if int(old_row.get("n_permutations", -1)) != recomputed["n_permutations"]:
            stale_flags.append(
                f"n_permutations mismatch: summary says {old_row.get('n_permutations')}, "
                f"perms file has {recomputed['n_permutations']} rows -> SUMMARY IS STALE, not just buggy"
            )
        for col in ("null_mean", "null_std", "z_score"):
            if col in old_row and abs(float(old_row[col]) - recomputed[col]) > max(TOL, 1e-2):
                stale_flags.append(f"{col} mismatch: summary={old_row[col]}, recomputed={recomputed[col]:.4f}")

        p_two_old = float(old_row.get("empirical_p_two_sided", float("nan")))
        p_two_new = recomputed["empirical_p_two_sided"]
        changed = abs(round(p_two_old, 4) - round(p_two_new, 4)) > TOL

        report_rows.append(dict(
            file=str(summary_path.relative_to(results_dir.parent)),
            group=group, kind=kind,
            n_perms=recomputed["n_permutations"],
            p_two_old=p_two_old, p_two_new=p_two_new, changed=changed,
            stale="; ".join(stale_flags) if stale_flags else "",
        ))

        if apply and not stale_flags:
            # Safe to patch in place: only the two-sided p-value column changes.
            summary_df.loc[summary_row_idx, "empirical_p_two_sided"] = round(p_two_new, 4)
            summary_df.to_csv(summary_path, index=False)
        elif apply and stale_flags:
            print(f"NOT WRITING {summary_path} (group={group}): summary disagrees with its own "
                  f"perms file beyond the two-sided p-value -- this is a stale/mismatched file, "
                  f"not a fixable one. Regenerate it from the perms file instead of patching it.")

    return report_rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results-dir", default="results")
    ap.add_argument("--apply", action="store_true", help="write fixes; omit for dry run")
    args = ap.parse_args()

    rows = process(Path(args.results_dir), args.apply)
    print(f"\n{'file':60s} {'group':12s} {'n':>4s} {'p2_old':>8s} {'p2_new':>8s} {'changed':>8s}  stale_flags")
    for r in rows:
        print(f"{r['file']:60s} {r['group']:12s} {r['n_perms']:4d} "
              f"{r['p_two_old']:8.4f} {r['p_two_new']:8.4f} {str(r['changed']):>8s}  {r['stale']}")

    n_changed = sum(1 for r in rows if r["changed"] and not r["stale"])
    n_stale = sum(1 for r in rows if r["stale"])
    print(f"\n{n_changed} files corrected in place. {n_stale} files flagged as stale/mismatched "
          f"(not written -- see 'stale_flags' column; regenerate these from their perms files).")


if __name__ == "__main__":
    main()