"""Polarity maps are named assumptions, not a single biological truth."""
from __future__ import annotations

import pandas as pd

from perturbation.cell_groups import NT_MAPS, transmitter_polarity


def test_both_maps_exist_and_disagree_on_glutamate():
    assert "classical_fast" in NT_MAPS
    assert "shiu_2024" in NT_MAPS
    glu = "glutamate"
    assert glu in NT_MAPS["shiu_2024"]["inhibitory"]
    assert glu not in NT_MAPS["classical_fast"]["inhibitory"]
    assert glu not in NT_MAPS["classical_fast"]["excitatory"]


def test_known_nt_preferred_over_top_nt():
    # known_nt wins when top_nt is unmapped under the map; a contradictory
    # top_nt is reported as "conflicting" (see test below), not overridden.
    ann = pd.DataFrame(
        {
            "known_nt": ["acetylcholine", None],
            "top_nt": ["glutamate", "gaba"],
        }
    )
    labels = transmitter_polarity(ann, nt_map="classical_fast")
    assert list(labels) == ["excitatory", "inhibitory"]


def test_conflict_when_known_and_predicted_disagree():
    ann = pd.DataFrame(
        {
            "known_nt": ["acetylcholine"],
            "top_nt": ["gaba"],
        }
    )
    labels = transmitter_polarity(ann, nt_map="classical_fast")
    assert labels.iloc[0] == "conflicting"


def test_glutamate_unmapped_unless_shiu_map():
    ann = pd.DataFrame({"known_nt": [None], "top_nt": ["glutamate"]})
    assert transmitter_polarity(ann, "classical_fast").iloc[0] == "unmapped"
    assert transmitter_polarity(ann, "shiu_2024").iloc[0] == "inhibitory"
