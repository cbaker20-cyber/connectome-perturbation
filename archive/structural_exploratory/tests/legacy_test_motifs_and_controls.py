"""Unit tests for disinhibition motif search and AN betweenness controls."""

from __future__ import annotations

from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd
import pytest

from connectome_analysis.an_betweenness import (
    ascending_neuron_ids,
    build_an_betweenness_table,
    build_digraph,
    compute_source_target_betweenness,
    empirical_p_values,
    run_degree_matched_fdr_control,
)
from connectome_analysis.disinhibition_motifs import (
    annotate_motif_neurotransmitters,
    enumerate_disinhibition_motifs,
    estimate_intermediate_activity,
    inhibitory_interneuron_ids,
    summarize_intermediates,
)
from tools.path_resolver import resolve_input


def _toy_signed_edges() -> pd.DataFrame:
    """Sensory --+--> GABA inhibitor ---> motor (classic feedforward inhibition)."""
    return pd.DataFrame(
        [
            {"source": 1, "target": 10, "signed_weight": 2.0},  # sensory excites inhibitor
            {"source": 10, "target": 100, "signed_weight": -3.0},  # inhibitor inhibits motor
            {"source": 1, "target": 100, "signed_weight": 0.5},  # weak direct drive
            {"source": 2, "target": 11, "signed_weight": 1.0},  # second sensory→inhibitor
            {"source": 11, "target": 101, "signed_weight": -1.5},
            # Non-motif: excitatory intermediate onto motor should not count.
            {"source": 1, "target": 12, "signed_weight": 4.0},
            {"source": 12, "target": 100, "signed_weight": 2.0},
            # Silent inhibitor with no sensory drive should not count.
            {"source": 13, "target": 100, "signed_weight": -9.0},
        ]
    )


def _toy_annotations() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "root_id": [1, 2, 10, 11, 12, 13, 100, 101, 200, 201, 202],
            "super_class": [
                "sensory",
                "sensory",
                "central",
                "central",
                "central",
                "central",
                "motor",
                "motor",
                "central",
                "ascending",
                "ascending",
            ],
            "cell_class": [
                "sugar",
                "sugar",
                "IN",
                "IN",
                "IN",
                "IN",
                "MN",
                "MN",
                "central",
                "AN",
                "AN",
            ],
            "top_nt": [
                "acetylcholine",
                "acetylcholine",
                "gaba",
                "glutamate",
                "acetylcholine",
                "gaba",
                "acetylcholine",
                "acetylcholine",
                "acetylcholine",
                "acetylcholine",
                "acetylcholine",
            ],
        }
    )


def test_path_resolver_resolves_annotations_and_connectivity():
    ann = resolve_input("flywire_annotations.tsv")
    con = resolve_input("2023_03_23_connectivity_630_final.parquet")
    assert ann.name == "flywire_annotations.tsv"
    assert con.name == "2023_03_23_connectivity_630_final.parquet"
    assert ann.exists()
    assert con.exists()


def test_inhibitory_interneuron_ids_select_gaba_and_glutamate():
    ids = inhibitory_interneuron_ids(_toy_annotations())
    assert ids == {10, 11, 13}


def test_estimate_intermediate_activity_sums_signed_source_drive():
    activity = estimate_intermediate_activity(_toy_signed_edges(), sources={1, 2}, intermediates={10, 11, 12, 13})
    assert activity[10] == pytest.approx(2.0)
    assert activity[11] == pytest.approx(1.0)
    assert activity[12] == pytest.approx(4.0)
    assert 13 not in activity


def test_enumerate_disinhibition_motifs_keeps_positive_delta_only():
    motifs = enumerate_disinhibition_motifs(
        _toy_signed_edges(),
        sources={1, 2},
        intermediates={10, 11, 12, 13},
        motors={100, 101},
        min_delta_hz=0.0,
    )
    assert not motifs.empty
    assert (motifs["delta_hz"] > 0).all()
    assert set(motifs["intermediate_id"]) == {10, 11}
    assert 12 not in set(motifs["intermediate_id"])  # excitatory onto motor
    assert 13 not in set(motifs["intermediate_id"])  # no sensory drive

    # delta = (-inh_weight) * activity
    row_10 = motifs.loc[motifs["intermediate_id"] == 10].iloc[0]
    assert row_10["delta_hz"] == pytest.approx(6.0)  # -(-3) * 2
    row_11 = motifs.loc[motifs["intermediate_id"] == 11].iloc[0]
    assert row_11["delta_hz"] == pytest.approx(1.5)  # -(-1.5) * 1


def test_annotate_and_summarize_motifs():
    motifs = enumerate_disinhibition_motifs(
        _toy_signed_edges(),
        sources={1, 2},
        intermediates={10, 11, 12, 13},
        motors={100, 101},
    )
    annotated = annotate_motif_neurotransmitters(motifs, _toy_annotations())
    assert set(annotated["intermediate_nt"]) <= {"gaba", "glutamate"}
    summary = summarize_intermediates(annotated)
    assert list(summary["intermediate_id"]) == [10, 11]
    assert summary.loc[0, "total_delta_hz"] == pytest.approx(6.0)


def test_run_disinhibition_writes_csv(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from connectome_analysis import disinhibition_motifs as mod

    edges = _toy_signed_edges()
    ann = _toy_annotations()
    con_path = tmp_path / "toy_connectivity.parquet"
    ann_path = tmp_path / "toy_annotations.tsv"
    edges_export = edges.rename(
        columns={
            "source": "Presynaptic_ID",
            "target": "Postsynaptic_ID",
            "signed_weight": "Excitatory x Connectivity",
        }
    )
    edges_export.to_parquet(con_path, index=False)
    ann.to_csv(ann_path, sep="\t", index=False)

    monkeypatch.setattr(mod, "resolve_analysis_path", lambda identifier, manifest_path="data/input_manifest.json": {
        "toy_con": con_path,
        "toy_ann": ann_path,
    }[identifier])

    out = tmp_path / "disinhibition_motifs.csv"
    result = mod.run_disinhibition_motif_search(
        connectivity_id="toy_con",
        annotations_id="toy_ann",
        source_ids=[1, 2],
        output_path=out,
    )
    assert out.exists()
    loaded = pd.read_csv(out)
    assert len(loaded) == len(result)
    assert (loaded["delta_hz"] > 0).all()


def _pathway_graph() -> tuple[nx.DiGraph, pd.DataFrame]:
    """Small digraph where AN nodes sit on sugar→motor shortest paths."""
    edges = pd.DataFrame(
        [
            {"source": 1, "target": 20, "weight": 5.0, "distance": 0.2},  # sugar → AN
            {"source": 20, "target": 100, "weight": 5.0, "distance": 0.2},  # AN → motor
            {"source": 1, "target": 30, "weight": 1.0, "distance": 1.0},  # sugar → central
            {"source": 30, "target": 100, "weight": 1.0, "distance": 1.0},  # longer path
            {"source": 2, "target": 21, "weight": 4.0, "distance": 0.25},
            {"source": 21, "target": 101, "weight": 4.0, "distance": 0.25},
            {"source": 2, "target": 31, "weight": 1.0, "distance": 1.0},
            {"source": 31, "target": 101, "weight": 1.0, "distance": 1.0},
            {"source": 30, "target": 31, "weight": 1.0, "distance": 1.0},
        ]
    )
    graph = build_digraph(edges)
    annotations = pd.DataFrame(
        {
            "root_id": [1, 2, 20, 21, 30, 31, 100, 101],
            "super_class": [
                "sensory",
                "sensory",
                "ascending",
                "ascending",
                "central",
                "central",
                "motor",
                "motor",
            ],
            "cell_class": ["sugar", "sugar", "AN", "AN", "central", "central", "MN", "MN"],
        }
    )
    return graph, annotations


def test_ascending_neuron_ids_prefer_cell_class_an():
    _, annotations = _pathway_graph()
    assert ascending_neuron_ids(annotations) == {20, 21}


def test_source_target_betweenness_elevates_an_on_paths():
    graph, _ = _pathway_graph()
    btw = compute_source_target_betweenness(graph, sources=[1, 2], targets=[100, 101], weight="distance")
    assert btw.get(20, 0.0) > 0.0
    assert btw.get(21, 0.0) > 0.0
    # Peripheral central nodes still have some betweenness but AN should be competitive.
    assert btw.get(20, 0.0) >= btw.get(30, 0.0)


def test_empirical_p_values_and_fdr_control_on_toy_metrics():
    rng = np.random.default_rng(0)
    focus = pd.DataFrame(
        {
            "neuron_id": [20, 21],
            "source_target_betweenness": [0.8, 0.7],
            "total_strength": [10.0, 10.0],
        }
    )
    pool = pd.DataFrame(
        {
            "neuron_id": list(range(1000, 1020)),
            "source_target_betweenness": rng.uniform(0.0, 0.2, size=20),
            "total_strength": np.full(20, 10.0),
        }
    )
    metrics = pd.concat([focus, pool], ignore_index=True)
    results = run_degree_matched_fdr_control(
        metrics,
        focus_ids={20, 21},
        null_pool_ids=set(pool["neuron_id"]),
        n_permutations=50,
        seed=0,
        metrics_to_test=("source_target_betweenness",),
        statistics=("mean",),
    )
    assert not results.empty
    assert "q_greater_bh" in results.columns
    assert "significant_greater_bh" in results.columns
    row = results.iloc[0]
    assert row["actual_value"] == pytest.approx(0.75)
    assert row["p_greater"] < 0.05

    p = empirical_p_values(np.array([0.1, 0.2, 0.3]), 0.9)
    assert p["p_greater"] == pytest.approx(1 / 4)


def test_build_an_betweenness_table_writes_control_schema(tmp_path: Path):
    graph, annotations = _pathway_graph()
    control = build_an_betweenness_table(
        graph,
        annotations,
        sources=[1, 2],
        targets=[100, 101],
        n_permutations=30,
        seed=3,
    )
    required = {
        "focus_group",
        "metric",
        "statistic",
        "actual_value",
        "null_mean",
        "p_greater",
        "q_greater_bh",
        "significant_greater_bh",
        "n_an_in_graph",
        "claim_status",
    }
    assert required.issubset(control.columns)
    assert (control["focus_group"] == "AN").all()
    assert control["n_an_in_graph"].iloc[0] == 2

    out = tmp_path / "an_betweenness_control.csv"
    control.to_csv(out, index=False)
    loaded = pd.read_csv(out)
    assert len(loaded) == len(control)
