import sys
sys.path.insert(0, "perturbation")
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from pathlib import Path

def plot_motor_impact():
    df = pd.read_csv("results/motor_impact.csv", index_col="exp_name")
    df = df[df.index.str.startswith("perturb_") & ~df.index.str.startswith("perturb_group")]
    df.index = df.index.str.replace("perturb_", "")
    df = df.sort_values("motor_delta_hz")

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # plot 1: total motor firing change
    colors = ["#d62728" if x < 0 else "#2ca02c" for x in df["motor_delta_hz"]]
    axes[0].barh(df.index, df["motor_delta_hz"], color=colors)
    axes[0].axvline(0, color="black", linewidth=0.8)
    axes[0].set_xlabel("Total motor neuron firing change (Hz)")
    axes[0].set_title("Motor output change by silenced group")
    axes[0].set_xlim(-1300, 100)

    # plot 2: inhibited vs disinhibited motor neurons
    x = np.arange(len(df))
    width = 0.35
    axes[1].barh(x - width/2, df["motor_neurons_inhibited"], width, label="Inhibited", color="#d62728")
    axes[1].barh(x + width/2, df["motor_neurons_disinhibited"], width, label="Disinhibited", color="#2ca02c")
    axes[1].set_yticks(x)
    axes[1].set_yticklabels(df.index)
    axes[1].set_xlabel("Number of motor neurons")
    axes[1].set_title("Motor neurons inhibited vs disinhibited")
    axes[1].legend()

    plt.tight_layout()
    Path("results").mkdir(exist_ok=True)
    plt.savefig("results/motor_impact_figure.png", dpi=150, bbox_inches="tight")
    print("Saved to results/motor_impact_figure.png")

if __name__ == "__main__":
    plot_motor_impact()
