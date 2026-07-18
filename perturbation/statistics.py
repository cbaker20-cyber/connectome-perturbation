import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

from tools.path_resolver import ensure_repo_on_path

ensure_repo_on_path(Path(__file__))
sys.path.insert(0, "perturbation")

from cell_groups import get_group


PATH_RES = Path("results")
BASELINE_NAME = "baseline_sugar"
T_RUN = 1.0
ALPHA = 0.05

TARGETS = [
    ("hq_LO", "LO"),
    ("hq_AN", "AN"),
    ("hq_LOP>LO.ME", "LOP>LO.ME"),
    ("hq_LHCENT", "LHCENT"),
    ("hq_ME>LO", "ME>LO"),
    ("hq_Kenyon_Cell", "Kenyon_Cell"),
    ("perturb_descending", "descending"),
    ("perturb_sensory", "sensory"),
    ("perturb_central", "central"),
    ("perturb_ascending", "ascending"),
]


def load_spike_table(exp_name, path_res=PATH_RES):
    """
    Load one spike-event table from results/{exp_name}.parquet.

    Expected columns:
        - trial
        - flywire_id
    """
    path = Path(path_res) / f"{exp_name}.parquet"

    if not path.exists():
        raise FileNotFoundError(f"Missing result file: {path}")

    df = pd.read_parquet(path)

    required_cols = {"trial", "flywire_id"}
    missing_cols = required_cols - set(df.columns)

    if missing_cols:
        raise ValueError(
            f"{path} is missing required columns: {sorted(missing_cols)}"
        )

    return df


def trial_rates(df, neuron_ids, t_run=T_RUN, trial_ids=None):
    """
    Compute total population firing rate for selected neurons in each trial.

    Important fix:
    This keeps trials where the selected neurons fired zero spikes.

    Previous behavior:
        The old version filtered to selected neurons first, then used
        df["trial"].unique(). That silently removed trials where the selected
        neurons had zero spikes.

    New behavior:
        Trial IDs are collected from the unfiltered spike table first.
        After counting selected-neuron spikes, we reindex all trials and fill
        missing trials with 0.
    """
    if t_run <= 0:
        raise ValueError("t_run must be positive.")

    if trial_ids is None:
        trial_ids = sorted(pd.unique(df["trial"]))

    trial_index = pd.Index(trial_ids, name="trial")
    neuron_ids = set(neuron_ids)

    selected_spikes = df[df["flywire_id"].isin(neuron_ids)]

    spike_counts_by_trial = selected_spikes.groupby("trial").size()

    rates_hz = (
        spike_counts_by_trial
        .reindex(trial_index, fill_value=0)
        .astype(float)
        .div(float(t_run))
    )

    return rates_hz.to_numpy(dtype=float)


def test_condition(
    exp_name,
    label=None,
    baseline_name=BASELINE_NAME,
    motor_ids=None,
    t_run=T_RUN,
    path_res=PATH_RES,
):
    """
    Compare baseline sugar stimulation against one perturbation condition.

    Returns raw p-values only. FDR correction is applied later across all tests.
    """
    if label is None:
        label = exp_name

    if motor_ids is None:
        motor_ids = get_group(super_class="motor")

    base_df = load_spike_table(baseline_name, path_res=path_res)
    exp_df = load_spike_table(exp_name, path_res=path_res)

    base_rates = trial_rates(base_df, motor_ids, t_run=t_run)
    exp_rates = trial_rates(exp_df, motor_ids, t_run=t_run)

    baseline_mean = float(np.mean(base_rates)) if len(base_rates) else np.nan
    perturbed_mean = float(np.mean(exp_rates)) if len(exp_rates) else np.nan

    delta = perturbed_mean - baseline_mean

    if baseline_mean == 0 or np.isnan(baseline_mean):
        pct_change = np.nan
    else:
        pct_change = (delta / baseline_mean) * 100.0

    if len(base_rates) < 2 or len(exp_rates) < 2:
        t_stat = np.nan
        p_value_raw = np.nan
    else:
        # Welch's t-test avoids assuming equal variance between conditions.
        t_stat, p_value_raw = stats.ttest_ind(
            base_rates,
            exp_rates,
            equal_var=False,
            nan_policy="omit",
        )
        t_stat = float(t_stat)
        p_value_raw = float(p_value_raw)

    return {
        "label": label,
        "exp_name": exp_name,
        "baseline_mean_hz": baseline_mean,
        "perturbed_mean_hz": perturbed_mean,
        "delta_hz": delta,
        "pct_change": pct_change,
        "t_stat": t_stat,
        "p_value_raw": p_value_raw,
        "n_baseline_trials": int(len(base_rates)),
        "n_perturbed_trials": int(len(exp_rates)),
    }


def apply_fdr_correction(df, alpha=ALPHA, p_col="p_value_raw"):
    """
    Apply Benjamini-Hochberg FDR correction across all valid p-values.

    Adds:
        - p_value_fdr
        - significant_uncorrected
        - significant_fdr
        - significant

    The old `significant` column is kept for compatibility, but now it means
    FDR-corrected significance, not raw p < 0.05.
    """
    df = df.copy()

    df["p_value_fdr"] = np.nan
    df["significant_uncorrected"] = False
    df["significant_fdr"] = False

    valid = df[p_col].notna()

    df.loc[valid, "significant_uncorrected"] = df.loc[valid, p_col] < alpha

    if valid.any():
        reject, q_values, _, _ = multipletests(
            df.loc[valid, p_col].to_numpy(dtype=float),
            alpha=alpha,
            method="fdr_bh",
        )

        df.loc[valid, "p_value_fdr"] = q_values
        df.loc[valid, "significant_fdr"] = reject

    # Backward-compatible columns for old plotting/figure scripts.
    df["significant"] = df["significant_fdr"]
    df["p_value"] = df["p_value_fdr"]

    return df


def run_statistics(
    targets=TARGETS,
    baseline_name=BASELINE_NAME,
    alpha=ALPHA,
    t_run=T_RUN,
    path_res=PATH_RES,
    output_name="statistics.csv",
):
    """
    Run all configured perturbation comparisons and save results/statistics.csv.
    """
    path_res = Path(path_res)

    rows = []
    motor_ids = get_group(super_class="motor")

    for exp_name, label in targets:
        try:
            result = test_condition(
                exp_name=exp_name,
                label=label,
                baseline_name=baseline_name,
                motor_ids=motor_ids,
                t_run=t_run,
                path_res=path_res,
            )
            rows.append(result)

        except FileNotFoundError as e:
            print(f"{label:20s}  missing: {e}")

        except Exception as e:
            print(f"{label:20s}  error: {e}")

    if not rows:
        print("No statistics were computed; no valid result files were found.")
        return pd.DataFrame()

    df = pd.DataFrame(rows).set_index("label")

    # FDR correction happens before rounding, using full-precision raw p-values.
    df = apply_fdr_correction(df, alpha=alpha)

    save_df = df.copy()

    round_cols = [
        "baseline_mean_hz",
        "perturbed_mean_hz",
        "delta_hz",
        "pct_change",
        "t_stat",
        "p_value_raw",
        "p_value_fdr",
        "p_value",
    ]

    for col in round_cols:
        if col in save_df.columns:
            save_df[col] = save_df[col].round(4)

    path_res.mkdir(parents=True, exist_ok=True)

    out_path = path_res / output_name
    save_df.to_csv(out_path)

    for label, row in save_df.iterrows():
        sig = "*" if bool(row["significant_fdr"]) else "ns"

        print(
            f"{label:20s}  "
            f"delta={row['delta_hz']:8.1f} Hz  "
            f"raw p={row['p_value_raw']:.4g}  "
            f"FDR q={row['p_value_fdr']:.4g}  "
            f"{sig}"
        )

    print(f"Saved to {out_path}")

    return df


if __name__ == "__main__":
    run_statistics()
