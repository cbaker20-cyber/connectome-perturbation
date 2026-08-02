from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.path_resolver import resolve_input

ANN_ID = "flywire_annotations.tsv"
SIM_ID = "2023_03_23_completeness_630_final.csv"
DEFAULT_MANIFEST = "data/input_manifest.json"


def load_annotated_sim_neurons(manifest_path: str = DEFAULT_MANIFEST):
    ann_path = resolve_input(ANN_ID, manifest_path=manifest_path)
    sim_path = resolve_input(SIM_ID, manifest_path=manifest_path)
    ann = pd.read_csv(ann_path, sep="\t", low_memory=False)
    sim = pd.read_csv(sim_path, index_col=0)
    sim_ids = set(sim.index.values)
    ann = ann[ann["root_id"].isin(sim_ids)]
    return ann


def get_group(cell_class=None, super_class=None, cell_type=None):
    ann = load_annotated_sim_neurons()
    mask = pd.Series([True] * len(ann), index=ann.index)
    if cell_class:
        mask &= ann["cell_class"] == cell_class
    if super_class:
        mask &= ann["super_class"] == super_class
    if cell_type:
        mask &= ann["cell_type"] == cell_type
    return ann.loc[mask, "root_id"].tolist()


def list_groups(by="super_class"):
    ann = load_annotated_sim_neurons()
    return ann.groupby(by)["root_id"].count().sort_values(ascending=False)


if __name__ == "__main__":
    print(list_groups("super_class"))
    print()
    motor = get_group(super_class="motor")
    print(f"Motor neurons in sim: {len(motor)}")
    descending = get_group(super_class="descending")
    print(f"Descending neurons in sim: {len(descending)}")
