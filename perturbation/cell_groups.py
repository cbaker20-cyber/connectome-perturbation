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

# Transmitter → coarse polarity is NOT unique in Drosophila.
# These maps are *explicit assumptions* for grouping, not biological facts.
# Glutamate in particular is excitatory at some synapses and inhibitory at others.
NT_MAPS = {
    "shiu_2024": {
        "description": (
            "Matches Shiu et al. 2024 LIF assumptions: ACh excitatory, "
            "GABA inhibitory, glutamate treated as inhibitory. "
            "Neuromodulators are left unmapped."
        ),
        "excitatory": {"acetylcholine", "ach"},
        "inhibitory": {"gaba", "glutamate", "glu"},
    },
    "classical_fast": {
        "description": (
            "Fast transmitters only, glutamate left unmapped because its "
            "sign is mixed in Drosophila (GluCl vs excitatory glutamate receptors)."
        ),
        "excitatory": {"acetylcholine", "ach"},
        "inhibitory": {"gaba"},
    },
}


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


def _normalize_nt(value) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip().lower()


def transmitter_polarity(ann: pd.DataFrame, nt_map: str = "classical_fast") -> pd.Series:
    """Assign each neuron a polarity label under an *explicit* NT map.

    Labels: excitatory | inhibitory | unmapped | conflicting
    Preference order for the source column: known_nt, then top_nt.
    Conflicting = known_nt and top_nt map to opposite polarities.
    """
    if nt_map not in NT_MAPS:
        raise ValueError(f"unknown nt_map {nt_map!r}; choose from {sorted(NT_MAPS)}")
    spec = NT_MAPS[nt_map]
    exc = spec["excitatory"]
    inh = spec["inhibitory"]

    def map_one(nt: str) -> str:
        if not nt:
            return "unmapped"
        if nt in exc:
            return "excitatory"
        if nt in inh:
            return "inhibitory"
        return "unmapped"

    known = ann["known_nt"].map(_normalize_nt) if "known_nt" in ann.columns else pd.Series("", index=ann.index)
    pred = ann["top_nt"].map(_normalize_nt) if "top_nt" in ann.columns else pd.Series("", index=ann.index)
    known_pol = known.map(map_one)
    pred_pol = pred.map(map_one)

    out = pred_pol.copy()
    # Prefer experimentally listed transmitter when present.
    has_known = known_pol.ne("unmapped")
    out.loc[has_known] = known_pol.loc[has_known]
    conflict = (
        known_pol.isin(["excitatory", "inhibitory"])
        & pred_pol.isin(["excitatory", "inhibitory"])
        & known_pol.ne(pred_pol)
    )
    out.loc[conflict] = "conflicting"
    return out


def get_polarity_group(polarity: str, nt_map: str = "classical_fast") -> list:
    """Root IDs whose assigned polarity matches ``polarity`` under ``nt_map``."""
    ann = load_annotated_sim_neurons()
    labels = transmitter_polarity(ann, nt_map=nt_map)
    return ann.loc[labels == polarity, "root_id"].tolist()


def polarity_counts(nt_map: str = "classical_fast") -> pd.Series:
    ann = load_annotated_sim_neurons()
    return transmitter_polarity(ann, nt_map=nt_map).value_counts()


if __name__ == "__main__":
    print(list_groups("super_class"))
    print()
    motor = get_group(super_class="motor")
    print(f"Motor neurons in sim: {len(motor)}")
    descending = get_group(super_class="descending")
    print(f"Descending neurons in sim: {len(descending)}")
    print()
    for name in NT_MAPS:
        print(f"NT map {name}: {NT_MAPS[name]['description']}")
        print(polarity_counts(name))
        print()
