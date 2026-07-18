from __future__ import annotations

from pathlib import Path

import pandas as pd

from tools.path_resolver import DEFAULT_MANIFEST_PATH, resolve_input

DEFAULT_ANNOTATIONS_ID = "flywire_annotations.tsv"
DEFAULT_COMPLETENESS_ID = "2023_03_23_completeness_630_final.csv"

# Backwards-compatible aliases: these values are manifest identifiers, not paths.
ANN_PATH = DEFAULT_ANNOTATIONS_ID
SIM_PATH = DEFAULT_COMPLETENESS_ID


def resolve_cell_group_inputs(
    annotations_id: str = DEFAULT_ANNOTATIONS_ID,
    completeness_id: str = DEFAULT_COMPLETENESS_ID,
    manifest_path: str = DEFAULT_MANIFEST_PATH,
    repo_root: Path | None = None,
):
    return (
        resolve_input(annotations_id, manifest_path=manifest_path, repo_root=repo_root),
        resolve_input(completeness_id, manifest_path=manifest_path, repo_root=repo_root),
    )


def load_annotated_sim_neurons(
    annotations_id: str = DEFAULT_ANNOTATIONS_ID,
    completeness_id: str = DEFAULT_COMPLETENESS_ID,
    manifest_path: str = DEFAULT_MANIFEST_PATH,
):
    ann_path, sim_path = resolve_cell_group_inputs(
        annotations_id=annotations_id,
        completeness_id=completeness_id,
        manifest_path=manifest_path,
    )
    ann = pd.read_csv(ann_path, sep="	", low_memory=False)
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
