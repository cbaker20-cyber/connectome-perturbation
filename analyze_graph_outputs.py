"""
analyze_graph_outputs.py

Post-hoc validation and figure generation for graph_analysis.py outputs.

This script:
1. Reads graph_analysis.py output CSVs.
2. Recomputes empirical bootstrap p-values from the saved null distributions.
3. Applies Benjamini-Hochberg FDR correction using statsmodels.
4. Checks that zeros in graph/null metrics are retained rather than silently dropped.
5. Optionally audits spike-trial rate handling to confirm zero-spike trials are kept as 0 Hz.
6. Generates publication-ready null-distribution figures with actual observed values overlaid.

Example:
python analyze_graph_outputs.py \
  --graph-dir "C:\\Users\\Baker\\Drosophila_Data\\results\\graph_analysis" \
  --alpha 0.05
"""

from __future__ import annotations

import argparse
import re
import warnings
from pathlib import Path
from typing import Iterable, Optional

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.stats.multitest import multipletests


REQUIRED_GRAPH_FILES = {
    "node_metrics": "graph_node_metrics.csv",
    "cell_class_summary": "graph_cell_class_summary.csv",
    "super_class_summary": "graph_super_class_summary.csv",
    "null_results": "degree_matched_null_results.csv",
    "null_distribution": "degree_matched_null_distribution.csv",
}

PLOT_LABELS = {
    "betweenness_centrality": "Betweenness centrality",
    "weighted_degree_centrality": "Weighted degree centrality",
    "weighted_in_degree_centrality": "Weighted in-degree centrality",
    "weighted_out_degree_centrality": "Weighted out-degree centrality",
    "total_strength": "Total synaptic strength",
    "in_strength": "Input synaptic strength",
    "out_strength": "Output synaptic strength",
    "mean": "mean",
    "median": "median",
    "sum": "sum",
    "max": "maximum",
}


def configure_matplotlib() -> None:
    """Set conservative publication-style defaults."""
    plt.rcParams.update(
        {
            "figure.dpi": 150,
            "savefig.dpi": 600,
            "font.size": 11,
            "axes.labelsize": 12,
            "axes.titlesize": 13,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
            "legend.fontsize": 10,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )


def read_graph_outputs(graph_dir: Path) -> dict[str, pd.DataFrame]:
    """Read all graph_analysis.py output files."""
    graph_dir = Path(graph_dir)
    data = {}

    missing = []
    for key, filename in REQUIRED_GRAPH_FILES.items():
        path = graph_dir / filename
        if not path.exists():
            missing.append(str(path))
        else:
            data[key] = pd.read_csv(path)

    if missing:
        raise FileNotFoundError(
            "Missing required graph-analysis outputs:\n" + "\n".join(missing)
        )

    return data


def find_null_column(null_df: pd.DataFrame, metric: str, statistic: str) -> str:
    """
    Find the null-distribution column corresponding to one metric/statistic row.

    graph_analysis.py currently writes columns like:
        betweenness_centrality_mean
        total_strength_sum

    Older drafts may have used:
        null_betweenness_centrality_mean
    """
    exact_candidates = [
        f"{metric}_{statistic}",
        f"null_{metric}_{statistic}",
    ]
    for col in exact_candidates:
        if col in null_df.columns:
            return col

    # Fallback: permissive matching, but avoid accidentally matching in/out variants.
    metric_norm = re.sub(r"[^a-z0-9]+", "", str(metric).lower())
    stat_norm = re.sub(r"[^a-z0-9]+", "", str(statistic).lower())

    candidates = []
    for col in null_df.columns:
        if col == "bootstrap_iteration":
            continue
        col_norm = re.sub(r"[^a-z0-9]+", "", str(col).lower())
        if metric_norm in col_norm and col_norm.endswith(stat_norm):
            candidates.append(col)

    if len(candidates) == 1:
        return candidates[0]

    raise ValueError(
        f"Could not uniquely identify null-distribution column for "
        f"metric={metric!r}, statistic={statistic!r}. Candidates={candidates}. "
        f"Available columns={list(null_df.columns)}"
    )


def empirical_pvalues(null_values: np.ndarray, actual_value: float) -> dict[str, float]:
    """
    Recompute empirical bootstrap p-values using the same +1 correction used
    in graph_analysis.py.
    """
    values = np.asarray(null_values, dtype=float)
    values = values[~np.isnan(values)]

    if len(values) == 0 or np.isnan(actual_value):
        return {
            "n_bootstrap_observed": 0,
            "p_greater_empirical": np.nan,
            "p_less_empirical": np.nan,
            "p_two_sided_empirical": np.nan,
            "null_mean_recomputed": np.nan,
            "null_std_recomputed": np.nan,
            "z_score_recomputed": np.nan,
            "percentile_recomputed": np.nan,
        }

    n = len(values)
    p_greater = (np.sum(values >= actual_value) + 1) / (n + 1)
    p_less = (np.sum(values <= actual_value) + 1) / (n + 1)
    p_two_sided = min(1.0, 2.0 * min(p_greater, p_less))

    null_mean = float(np.mean(values))
    null_std = float(np.std(values, ddof=1)) if n > 1 else np.nan
    z_score = float((actual_value - null_mean) / null_std) if null_std > 0 else np.nan
    percentile = float(np.mean(values <= actual_value) * 100.0)

    return {
        "n_bootstrap_observed": int(n),
        "p_greater_empirical": float(p_greater),
        "p_less_empirical": float(p_less),
        "p_two_sided_empirical": float(p_two_sided),
        "null_mean_recomputed": null_mean,
        "null_std_recomputed": null_std,
        "z_score_recomputed": z_score,
        "percentile_recomputed": percentile,
    }


def apply_bh_fdr(df: pd.DataFrame, p_col: str, alpha: float, prefix: str) -> pd.DataFrame:
    """Apply Benjamini-Hochberg FDR correction to one p-value column."""
    out = df.copy()
    q_col = f"q_{prefix}_bh"
    sig_col = f"significant_{prefix}_bh"

    out[q_col] = np.nan
    out[sig_col] = False

    valid = out[p_col].notna()
    if valid.any():
        reject, q_values, _, _ = multipletests(
            out.loc[valid, p_col].to_numpy(dtype=float),
            alpha=alpha,
            method="fdr_bh",
        )
        out.loc[valid, q_col] = q_values
        out.loc[valid, sig_col] = reject

    return out


def recompute_null_statistics(
    null_results: pd.DataFrame,
    null_distribution: pd.DataFrame,
    alpha: float = 0.05,
) -> pd.DataFrame:
    """
    Recompute empirical p-values and FDR-corrected q-values from saved nulls.

    This is the main statistical audit for graph_analysis.py outputs.
    """
    required_cols = {"metric", "statistic", "actual_value"}
    missing = required_cols - set(null_results.columns)
    if missing:
        raise ValueError(f"degree_matched_null_results.csv missing columns: {missing}")

    rows = []
    for _, row in null_results.iterrows():
        metric = row["metric"]
        statistic = row["statistic"]
        actual = float(row["actual_value"])
        null_col = find_null_column(null_distribution, metric, statistic)

        # Important: do NOT filter values != 0. Zeros are valid graph/null values.
        values_raw = pd.to_numeric(null_distribution[null_col], errors="coerce")
        zero_count = int((values_raw == 0).sum())
        nan_count = int(values_raw.isna().sum())
        values = values_raw.dropna().to_numpy(dtype=float)

        stats = empirical_pvalues(values, actual)

        out_row = row.to_dict()
        out_row.update(stats)
        out_row["null_distribution_column"] = null_col
        out_row["zero_values_retained_in_null"] = zero_count
        out_row["nan_values_excluded_from_null"] = nan_count

        # Compare recomputed p-values against the original graph_analysis.py outputs.
        for original_col, recomputed_col in [
            ("p_greater", "p_greater_empirical"),
            ("p_less", "p_less_empirical"),
            ("p_two_sided", "p_two_sided_empirical"),
        ]:
            if original_col in null_results.columns:
                out_row[f"abs_delta_{original_col}"] = abs(
                    float(row[original_col]) - float(out_row[recomputed_col])
                )

        rows.append(out_row)

    check_df = pd.DataFrame(rows)

    # Directional test: use this if your preregistered hypothesis is
    # "AN/ascending centrality is greater than the degree-matched null."
    check_df = apply_bh_fdr(
        check_df,
        p_col="p_greater_empirical",
        alpha=alpha,
        prefix="greater",
    )

    # Conservative/non-directional test: report this if you want any deviation
    # from the null, in either direction.
    check_df = apply_bh_fdr(
        check_df,
        p_col="p_two_sided_empirical",
        alpha=alpha,
        prefix="two_sided",
    )

    return check_df


def validate_zero_metric_handling(
    node_metrics: pd.DataFrame,
    null_distribution: pd.DataFrame,
) -> pd.DataFrame:
    """
    Check that zero-valued graph metrics are visible and not implicitly dropped.

    For graph metrics, "zero-spike trial" logic does not apply directly because
    there are no spike trials. The analogous graph-theory failure mode is dropping
    neurons or bootstrap draws with zero centrality/strength. This report confirms
    that zeros are counted rather than filtered out.
    """
    rows = []

    numeric_node_cols = [
        col for col in node_metrics.columns
        if col != "root_id" and pd.api.types.is_numeric_dtype(node_metrics[col])
    ]
    for col in numeric_node_cols:
        s = pd.to_numeric(node_metrics[col], errors="coerce")
        rows.append(
            {
                "table": "graph_node_metrics.csv",
                "column": col,
                "n_rows": int(len(s)),
                "n_non_nan": int(s.notna().sum()),
                "n_zero": int((s == 0).sum()),
                "zero_fraction": float((s == 0).mean()),
            }
        )

    for col in null_distribution.columns:
        if col == "bootstrap_iteration":
            continue
        s = pd.to_numeric(null_distribution[col], errors="coerce")
        rows.append(
            {
                "table": "degree_matched_null_distribution.csv",
                "column": col,
                "n_rows": int(len(s)),
                "n_non_nan": int(s.notna().sum()),
                "n_zero": int((s == 0).sum()),
                "zero_fraction": float((s == 0).mean()),
            }
        )

    return pd.DataFrame(rows)


def validate_bootstrap_integrity(check_df: pd.DataFrame) -> pd.DataFrame:
    """Create a compact pass/fail report for bootstrap counts and p-value agreement."""
    rows = []
    for _, row in check_df.iterrows():
        expected_n = row.get("n_bootstrap", np.nan)
        observed_n = row.get("n_bootstrap_observed", np.nan)

        p_delta_cols = [c for c in check_df.columns if c.startswith("abs_delta_p_")]
        max_p_delta = np.nan
        if p_delta_cols:
            max_p_delta = float(np.nanmax([row.get(c, np.nan) for c in p_delta_cols]))

        rows.append(
            {
                "metric": row["metric"],
                "statistic": row["statistic"],
                "expected_n_bootstrap": expected_n,
                "observed_n_bootstrap": observed_n,
                "bootstrap_count_ok": bool(expected_n == observed_n),
                "max_abs_delta_original_vs_recomputed_p": max_p_delta,
                "p_values_match_original": bool(
                    np.isnan(max_p_delta) or max_p_delta < 1e-12
                ),
                "significant_greater_bh": bool(row.get("significant_greater_bh", False)),
                "significant_two_sided_bh": bool(row.get("significant_two_sided_bh", False)),
            }
        )
    return pd.DataFrame(rows)


def pretty_metric_name(metric: str, statistic: str) -> str:
    """Human-readable label for plots."""
    metric_label = PLOT_LABELS.get(metric, metric.replace("_", " "))
    stat_label = PLOT_LABELS.get(statistic, statistic.replace("_", " "))
    return f"{stat_label.capitalize()} {metric_label}"


def safe_filename(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", text).strip("_")


def plot_null_distribution(
    row: pd.Series,
    null_distribution: pd.DataFrame,
    output_dir: Path,
    alpha: float = 0.05,
    use_directional_q: bool = True,
) -> Path:
    """
    Plot empirical degree-matched null distribution against actual observed value.
    """
    metric = str(row["metric"])
    statistic = str(row["statistic"])
    null_col = str(row["null_distribution_column"])
    actual = float(row["actual_value"])

    values = pd.to_numeric(null_distribution[null_col], errors="coerce").dropna().to_numpy(dtype=float)
    if len(values) == 0:
        raise ValueError(f"No valid null values for {metric}/{statistic}.")

    null_mean = float(row.get("null_mean_recomputed", np.mean(values)))
    z = row.get("z_score_recomputed", np.nan)

    if use_directional_q:
        p = row.get("p_greater_empirical", np.nan)
        q = row.get("q_greater_bh", np.nan)
        p_label = "one-sided empirical p"
        q_label = "BH-FDR q"
    else:
        p = row.get("p_two_sided_empirical", np.nan)
        q = row.get("q_two_sided_bh", np.nan)
        p_label = "two-sided empirical p"
        q_label = "BH-FDR q"

    fig, ax = plt.subplots(figsize=(6.2, 4.2))

    ax.hist(
        values,
        bins="auto",
        density=True,
        alpha=0.75,
        edgecolor="white",
        linewidth=0.6,
        label="Degree-matched null",
    )

    ax.axvline(null_mean, linestyle="--", linewidth=2.0, label="Null mean")
    ax.axvline(actual, linestyle="-", linewidth=2.5, label="Observed AN / ascending")

    title = pretty_metric_name(metric, statistic)
    ax.set_title(title)
    ax.set_xlabel(title)
    ax.set_ylabel("Density")

    text = (
        f"Observed = {actual:.3g}\n"
        f"Null mean = {null_mean:.3g}\n"
        f"z = {z:.2f}\n"
        f"{p_label} = {p:.3g}\n"
        f"{q_label} = {q:.3g}"
    )
    ax.text(
        0.98,
        0.96,
        text,
        transform=ax.transAxes,
        ha="right",
        va="top",
        bbox={"boxstyle": "round,pad=0.35", "facecolor": "white", "edgecolor": "0.7", "alpha": 0.95},
    )

    ax.legend(frameon=False, loc="best")
    fig.tight_layout()

    output_dir.mkdir(parents=True, exist_ok=True)
    base = safe_filename(f"null_distribution_{metric}_{statistic}")
    png_path = output_dir / f"{base}.png"
    svg_path = output_dir / f"{base}.svg"
    pdf_path = output_dir / f"{base}.pdf"

    fig.savefig(png_path, bbox_inches="tight")
    fig.savefig(svg_path, bbox_inches="tight")
    fig.savefig(pdf_path, bbox_inches="tight")
    plt.close(fig)

    return png_path


def plot_all_null_distributions(
    check_df: pd.DataFrame,
    null_distribution: pd.DataFrame,
    output_dir: Path,
    alpha: float = 0.05,
) -> list[Path]:
    """Generate one null-distribution figure per metric/statistic test."""
    paths = []
    for _, row in check_df.iterrows():
        paths.append(
            plot_null_distribution(
                row=row,
                null_distribution=null_distribution,
                output_dir=output_dir,
                alpha=alpha,
                use_directional_q=True,
            )
        )
    return paths


def plot_compact_top_panel(
    check_df: pd.DataFrame,
    null_distribution: pd.DataFrame,
    output_dir: Path,
    metric_order: Optional[list[str]] = None,
    max_panels: int = 6,
) -> Path:
    """
    Generate a compact multi-panel figure for the strongest tests.

    Ranking uses q_greater_bh, then p_greater_empirical.
    """
    if metric_order is not None:
        keep = []
        for key in metric_order:
            metric, statistic = key.rsplit("_", 1)
            hit = check_df[(check_df["metric"] == metric) & (check_df["statistic"] == statistic)]
            if len(hit):
                keep.append(hit.iloc[0])
        plot_df = pd.DataFrame(keep)
    else:
        plot_df = check_df.sort_values(["q_greater_bh", "p_greater_empirical"]).head(max_panels)

    if plot_df.empty:
        raise ValueError("No rows available for compact panel plot.")

    n = len(plot_df)
    ncols = min(3, n)
    nrows = int(np.ceil(n / ncols))

    fig, axes = plt.subplots(nrows=nrows, ncols=ncols, figsize=(5.2 * ncols, 3.8 * nrows))
    axes = np.atleast_1d(axes).ravel()

    for ax, (_, row) in zip(axes, plot_df.iterrows()):
        null_col = row["null_distribution_column"]
        values = pd.to_numeric(null_distribution[null_col], errors="coerce").dropna().to_numpy(dtype=float)
        actual = float(row["actual_value"])
        null_mean = float(row.get("null_mean_recomputed", np.mean(values)))

        ax.hist(values, bins="auto", density=True, alpha=0.75, edgecolor="white", linewidth=0.5)
        ax.axvline(null_mean, linestyle="--", linewidth=1.8)
        ax.axvline(actual, linestyle="-", linewidth=2.3)

        title = pretty_metric_name(row["metric"], row["statistic"])
        ax.set_title(title)
        ax.set_xlabel("Centrality / strength statistic")
        ax.set_ylabel("Density")
        ax.text(
            0.98,
            0.96,
            f"z={row['z_score_recomputed']:.2f}\nq={row['q_greater_bh']:.3g}",
            transform=ax.transAxes,
            ha="right",
            va="top",
            bbox={"boxstyle": "round,pad=0.25", "facecolor": "white", "edgecolor": "0.75", "alpha": 0.95},
        )

    for ax in axes[n:]:
        ax.axis("off")

    fig.suptitle("Observed AN / ascending graph centrality vs degree-matched null", y=1.02, fontsize=14)
    fig.tight_layout()

    output_dir.mkdir(parents=True, exist_ok=True)
    out = output_dir / "null_distribution_compact_panel.png"
    fig.savefig(out, bbox_inches="tight")
    fig.savefig(output_dir / "null_distribution_compact_panel.svg", bbox_inches="tight")
    fig.savefig(output_dir / "null_distribution_compact_panel.pdf", bbox_inches="tight")
    plt.close(fig)
    return out


# Optional spike-output audit -------------------------------------------------

def trial_rates_keep_zeros(
    spike_df: pd.DataFrame,
    neuron_ids: Iterable,
    t_run_s: float,
    trial_ids: Optional[Iterable] = None,
) -> pd.Series:
    """
    Compute population firing rate per trial while keeping zero-spike trials.

    This audits the separate spike-output statistics pipeline. It is not needed
    for graph metrics, which have no spike trials.
    """
    if t_run_s <= 0:
        raise ValueError("t_run_s must be positive.")
    required = {"trial", "flywire_id"}
    missing = required - set(spike_df.columns)
    if missing:
        raise ValueError(f"Spike table missing required columns: {missing}")

    if trial_ids is None:
        trial_ids = sorted(pd.unique(spike_df["trial"]))

    trial_index = pd.Index(trial_ids, name="trial")
    neuron_ids = set(neuron_ids)
    selected = spike_df[spike_df["flywire_id"].isin(neuron_ids)]
    counts = selected.groupby("trial").size()

    rates = counts.reindex(trial_index, fill_value=0).astype(float) / float(t_run_s)
    return rates


def optional_spike_zero_audit(
    baseline_spikes: Optional[Path],
    perturbation_spikes: Optional[Path],
    neuron_ids_csv: Optional[Path],
    neuron_id_col: str,
    t_run_s: float,
    output_dir: Path,
) -> Optional[Path]:
    """Run optional zero-spike-trial audit if spike paths are provided."""
    if baseline_spikes is None or perturbation_spikes is None or neuron_ids_csv is None:
        return None

    baseline_spikes = Path(baseline_spikes)
    perturbation_spikes = Path(perturbation_spikes)
    neuron_ids_csv = Path(neuron_ids_csv)

    base_df = pd.read_parquet(baseline_spikes)
    pert_df = pd.read_parquet(perturbation_spikes)
    ids_df = pd.read_csv(neuron_ids_csv)
    if neuron_id_col not in ids_df.columns:
        raise ValueError(f"{neuron_ids_csv} missing neuron-id column {neuron_id_col!r}.")

    neuron_ids = ids_df[neuron_id_col].dropna().unique()
    all_trials = sorted(set(base_df["trial"].unique()).union(set(pert_df["trial"].unique())))

    base_rates = trial_rates_keep_zeros(base_df, neuron_ids, t_run_s=t_run_s, trial_ids=all_trials)
    pert_rates = trial_rates_keep_zeros(pert_df, neuron_ids, t_run_s=t_run_s, trial_ids=all_trials)

    report = pd.DataFrame(
        {
            "condition": ["baseline", "perturbation"],
            "n_trials_expected": [len(all_trials), len(all_trials)],
            "n_trials_returned": [len(base_rates), len(pert_rates)],
            "n_zero_spike_trials_retained": [int((base_rates == 0).sum()), int((pert_rates == 0).sum())],
            "mean_rate_hz": [float(base_rates.mean()), float(pert_rates.mean())],
        }
    )

    out = output_dir / "optional_zero_spike_trial_audit.csv"
    report.to_csv(out, index=False)
    return out


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate graph-analysis null statistics and generate publication figures."
    )
    parser.add_argument(
        "--graph-dir",
        type=Path,
        required=True,
        help="Directory containing graph_analysis.py output CSVs.",
    )
    parser.add_argument("--alpha", type=float, default=0.05)
    parser.add_argument(
        "--fig-dir",
        type=Path,
        default=None,
        help="Optional figure output directory. Defaults to graph-dir/figures.",
    )

    # Optional spike audit args.
    parser.add_argument("--baseline-spikes", type=Path, default=None)
    parser.add_argument("--perturbation-spikes", type=Path, default=None)
    parser.add_argument("--neuron-ids-csv", type=Path, default=None)
    parser.add_argument("--neuron-id-col", default="root_id")
    parser.add_argument("--t-run-s", type=float, default=1.0)

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    configure_matplotlib()

    graph_dir = args.graph_dir
    fig_dir = args.fig_dir or (graph_dir / "figures")

    data = read_graph_outputs(graph_dir)
    node_metrics = data["node_metrics"]
    null_results = data["null_results"]
    null_distribution = data["null_distribution"]

    check_df = recompute_null_statistics(
        null_results=null_results,
        null_distribution=null_distribution,
        alpha=args.alpha,
    )
    check_path = graph_dir / "graph_null_significance_recomputed_fdr.csv"
    check_df.to_csv(check_path, index=False)

    integrity_df = validate_bootstrap_integrity(check_df)
    integrity_path = graph_dir / "graph_null_integrity_check.csv"
    integrity_df.to_csv(integrity_path, index=False)

    zero_metric_df = validate_zero_metric_handling(node_metrics, null_distribution)
    zero_metric_path = graph_dir / "zero_metric_retention_check.csv"
    zero_metric_df.to_csv(zero_metric_path, index=False)

    figure_paths = plot_all_null_distributions(
        check_df=check_df,
        null_distribution=null_distribution,
        output_dir=fig_dir,
        alpha=args.alpha,
    )
    panel_path = plot_compact_top_panel(
        check_df=check_df,
        null_distribution=null_distribution,
        output_dir=fig_dir,
    )

    spike_audit_path = optional_spike_zero_audit(
        baseline_spikes=args.baseline_spikes,
        perturbation_spikes=args.perturbation_spikes,
        neuron_ids_csv=args.neuron_ids_csv,
        neuron_id_col=args.neuron_id_col,
        t_run_s=args.t_run_s,
        output_dir=graph_dir,
    )

    print("\nValidation complete.")
    print(f"Recomputed FDR table:      {check_path}")
    print(f"Bootstrap integrity check: {integrity_path}")
    print(f"Zero metric retention:     {zero_metric_path}")
    print(f"Individual figures:        {fig_dir} ({len(figure_paths)} files x PNG/SVG/PDF)")
    print(f"Compact panel:             {panel_path}")
    if spike_audit_path is not None:
        print(f"Optional spike audit:       {spike_audit_path}")

    print("\nTop tests by directional BH-FDR q-value:")
    cols = [
        "metric",
        "statistic",
        "actual_value",
        "null_mean_recomputed",
        "z_score_recomputed",
        "p_greater_empirical",
        "q_greater_bh",
        "significant_greater_bh",
        "p_two_sided_empirical",
        "q_two_sided_bh",
        "significant_two_sided_bh",
    ]
    cols = [c for c in cols if c in check_df.columns]
    print(check_df.sort_values("q_greater_bh")[cols].head(20).to_string(index=False))


if __name__ == "__main__":
    main()
