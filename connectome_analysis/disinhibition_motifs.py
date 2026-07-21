"""Search signed connectome motifs that can explain motor disinhibition.

Issue #59: locate inhibitory (GABAergic / glutamatergic) intermediates on
paths from sensory drive to motor outputs, then keep motifs where a linear
signed-rate proxy predicts ``delta_hz > 0`` after silencing the intermediate.

This module is structural / model-proxy plumbing. Outputs are not Brian2 spike
rates and must not be treated as validated neuroscience claims without the full
reproducibility spine (manifest, seed, commit, validation record).
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
from typing import Iterable, Optional, Sequence

import numpy as np
import pandas as pd

from tools.path_resolver import resolve_input

# Default sugar sensory root IDs used by the sugar-feeding baseline.
DEFAULT_SUGAR_IDS: list[int] = [
    720575940624963786,
    720575940630233916,
    720575940637568838,
    720575940638202345,
    720575940617000768,
    720575940630797113,
    720575940632889389,
    720575940621754367,
    720575940621502051,
    720575940640649691,
]

INHIBITORY_NTS = frozenset({"gaba", "glutamate"})
SIGNED_WEIGHT_CANDIDATES = (
    "Excitatory x Connectivity",
    "signed_weight",
    "weight",
)
PRE_CANDIDATES = ("Presynaptic_ID", "pre_root_id", "source", "pre")
POST_CANDIDATES = ("Postsynaptic_ID", "post_root_id", "target", "post")


def _first_existing(columns: Iterable[str], candidates: Sequence[str]) -> Optional[str]:
    cols = set(columns)
    for name in candidates:
        if name in cols:
            return name
    return None


def resolve_analysis_path(identifier: str, *, manifest_path: str = "data/input_manifest.json") -> Path:
    """Resolve an input through the repository path resolver."""
    return resolve_input(identifier, manifest_path=manifest_path)


def load_annotations(path: Path) -> pd.DataFrame:
    ann = pd.read_csv(path, sep="\t", low_memory=False)
    if "root_id" not in ann.columns:
        raise ValueError(f"annotations must contain root_id; columns={list(ann.columns)}")
    out = ann.copy()
    out["root_id"] = pd.to_numeric(out["root_id"], errors="coerce")
    out = out.dropna(subset=["root_id"])
    out["root_id"] = out["root_id"].astype("int64").map(int)
    return out


def load_signed_edges(path: Path) -> pd.DataFrame:
    """Load directed edges with signed synaptic weight."""
    raw = pd.read_parquet(path) if path.suffix == ".parquet" else pd.read_csv(path)
    pre = _first_existing(raw.columns, PRE_CANDIDATES)
    post = _first_existing(raw.columns, POST_CANDIDATES)
    weight = _first_existing(raw.columns, SIGNED_WEIGHT_CANDIDATES)
    missing = [label for label, value in (("pre", pre), ("post", post), ("signed weight", weight)) if value is None]
    if missing:
        raise ValueError(f"Could not infer signed edge schema ({missing}). Columns: {list(raw.columns)}")

    edges = raw.loc[:, [pre, post, weight]].copy()
    edges.columns = ["source", "target", "signed_weight"]
    edges["source"] = pd.to_numeric(edges["source"], errors="coerce")
    edges["target"] = pd.to_numeric(edges["target"], errors="coerce")
    edges["signed_weight"] = pd.to_numeric(edges["signed_weight"], errors="coerce")
    edges = edges.dropna(subset=["source", "target", "signed_weight"])
    edges = edges[edges["signed_weight"] != 0]
    edges["source"] = edges["source"].astype("int64").map(int)
    edges["target"] = edges["target"].astype("int64").map(int)
    edges["signed_weight"] = edges["signed_weight"].astype(float)
    return edges.groupby(["source", "target"], as_index=False)["signed_weight"].sum()


def select_ids(
    annotations: pd.DataFrame,
    *,
    super_class: Optional[str] = None,
    cell_class: Optional[str] = None,
    top_nts: Optional[Iterable[str]] = None,
) -> set[int]:
    mask = pd.Series(True, index=annotations.index)
    if super_class is not None:
        mask &= annotations["super_class"].astype(str).str.lower().eq(super_class.lower())
    if cell_class is not None:
        mask &= annotations["cell_class"].astype(str).str.lower().eq(cell_class.lower())
    if top_nts is not None:
        allowed = {str(nt).lower() for nt in top_nts}
        mask &= annotations["top_nt"].astype(str).str.lower().isin(allowed)
    return set(annotations.loc[mask, "root_id"].map(int).tolist())


def inhibitory_interneuron_ids(annotations: pd.DataFrame) -> set[int]:
    """GABAergic / glutamatergic neurons used as candidate inhibitory intermediates."""
    return select_ids(annotations, top_nts=INHIBITORY_NTS)


def estimate_intermediate_activity(
    edges: pd.DataFrame,
    sources: set[int],
    intermediates: set[int],
    *,
    source_drive: float = 1.0,
) -> dict[int, float]:
    """Estimate intermediate drive as summed signed weight from sensory sources."""
    activity: dict[int, float] = defaultdict(float)
    relevant = edges[edges["source"].isin(sources) & edges["target"].isin(intermediates)]
    for row in relevant.itertuples(index=False):
        activity[int(row.target)] += source_drive * float(row.signed_weight)
    return dict(activity)


def enumerate_disinhibition_motifs(
    edges: pd.DataFrame,
    *,
    sources: set[int],
    intermediates: set[int],
    motors: set[int],
    min_delta_hz: float = 0.0,
    hz_scale: float = 1.0,
) -> pd.DataFrame:
    """Enumerate sensory → inhibitory intermediate → motor motifs.

    Motif filter: the intermediate→motor edge must be inhibitory (signed weight
    < 0). Silencing the intermediate removes that inhibition, so the linear
    proxy predicts ``delta_hz = -signed_weight(I→M) * activity(I) * hz_scale``.
    Rows with ``delta_hz > min_delta_hz`` are retained (default: strictly > 0).
    """
    if not sources or not intermediates or not motors:
        return pd.DataFrame(
            columns=[
                "source_id",
                "intermediate_id",
                "motor_id",
                "source_to_intermediate_weight",
                "intermediate_to_motor_weight",
                "intermediate_nt",
                "intermediate_activity",
                "delta_hz",
                "motif_type",
            ]
        )

    activity = estimate_intermediate_activity(edges, sources, intermediates)
    src_to_inh = edges[edges["source"].isin(sources) & edges["target"].isin(intermediates)]
    inh_to_motor = edges[
        edges["source"].isin(intermediates)
        & edges["target"].isin(motors)
        & (edges["signed_weight"] < 0)
    ]

    # Index source→intermediate edges for join.
    upstream: dict[int, list[tuple[int, float]]] = defaultdict(list)
    for row in src_to_inh.itertuples(index=False):
        upstream[int(row.target)].append((int(row.source), float(row.signed_weight)))

    rows: list[dict[str, object]] = []
    for row in inh_to_motor.itertuples(index=False):
        intermediate = int(row.source)
        motor = int(row.target)
        inh_weight = float(row.signed_weight)
        act = float(activity.get(intermediate, 0.0))
        # Only intermediates that receive sensory drive can mediate sensory→motor release.
        if act <= 0:
            continue
        delta = (-inh_weight) * act * float(hz_scale)
        if not (delta > min_delta_hz):
            continue
        for source_id, src_weight in upstream.get(intermediate, []):
            # Prefer excitatory sensory drive onto the inhibitor (classic feedforward inhibition).
            if src_weight <= 0:
                continue
            rows.append(
                {
                    "source_id": source_id,
                    "intermediate_id": intermediate,
                    "motor_id": motor,
                    "source_to_intermediate_weight": src_weight,
                    "intermediate_to_motor_weight": inh_weight,
                    "intermediate_activity": act,
                    "delta_hz": float(delta),
                    "motif_type": "sensory_excites_inhibitor_inhibits_motor",
                }
            )

    if not rows:
        return pd.DataFrame(
            columns=[
                "source_id",
                "intermediate_id",
                "motor_id",
                "source_to_intermediate_weight",
                "intermediate_to_motor_weight",
                "intermediate_nt",
                "intermediate_activity",
                "delta_hz",
                "motif_type",
            ]
        )

    result = pd.DataFrame(rows)
    return result.sort_values(
        ["delta_hz", "intermediate_id", "motor_id", "source_id"],
        ascending=[False, True, True, True],
    ).reset_index(drop=True)


def annotate_motif_neurotransmitters(motifs: pd.DataFrame, annotations: pd.DataFrame) -> pd.DataFrame:
    if motifs.empty:
        out = motifs.copy()
        if "intermediate_nt" not in out.columns:
            out["intermediate_nt"] = pd.Series(dtype=object)
        return out
    nt_map = (
        annotations.loc[:, ["root_id", "top_nt"]]
        .drop_duplicates("root_id")
        .set_index("root_id")["top_nt"]
        .to_dict()
    )
    out = motifs.copy()
    out["intermediate_nt"] = out["intermediate_id"].map(nt_map)
    return out


def summarize_intermediates(motifs: pd.DataFrame) -> pd.DataFrame:
    """Collapse motifs to ranked inhibitory intermediates."""
    if motifs.empty:
        return pd.DataFrame(
            columns=[
                "intermediate_id",
                "intermediate_nt",
                "n_motifs",
                "n_motors",
                "n_sources",
                "total_delta_hz",
                "mean_delta_hz",
                "max_delta_hz",
            ]
        )
    grouped = motifs.groupby(["intermediate_id", "intermediate_nt"], dropna=False)
    rows = []
    for (intermediate_id, intermediate_nt), g in grouped:
        rows.append(
            {
                "intermediate_id": int(intermediate_id),
                "intermediate_nt": intermediate_nt,
                "n_motifs": int(len(g)),
                "n_motors": int(g["motor_id"].nunique()),
                "n_sources": int(g["source_id"].nunique()),
                "total_delta_hz": float(g["delta_hz"].sum()),
                "mean_delta_hz": float(g["delta_hz"].mean()),
                "max_delta_hz": float(g["delta_hz"].max()),
            }
        )
    return pd.DataFrame(rows).sort_values("total_delta_hz", ascending=False).reset_index(drop=True)


def run_disinhibition_motif_search(
    *,
    connectivity_id: str = "2023_03_23_connectivity_630_final.parquet",
    annotations_id: str = "flywire_annotations.tsv",
    manifest_path: str = "data/input_manifest.json",
    source_ids: Optional[Sequence[int]] = None,
    output_path: str | Path = "results/disinhibition_motifs.csv",
    min_delta_hz: float = 0.0,
    hz_scale: float = 1.0,
) -> pd.DataFrame:
    """Resolve inputs, search motifs, and write the results CSV."""
    con_path = resolve_analysis_path(connectivity_id, manifest_path=manifest_path)
    ann_path = resolve_analysis_path(annotations_id, manifest_path=manifest_path)

    annotations = load_annotations(ann_path)
    edges = load_signed_edges(con_path)

    sources = set(int(x) for x in (source_ids if source_ids is not None else DEFAULT_SUGAR_IDS))
    intermediates = inhibitory_interneuron_ids(annotations)
    motors = select_ids(annotations, super_class="motor")

    motifs = enumerate_disinhibition_motifs(
        edges,
        sources=sources,
        intermediates=intermediates,
        motors=motors,
        min_delta_hz=min_delta_hz,
        hz_scale=hz_scale,
    )
    motifs = annotate_motif_neurotransmitters(motifs, annotations)

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    motifs.to_csv(out, index=False)
    return motifs


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--connectivity", default="2023_03_23_connectivity_630_final.parquet")
    parser.add_argument("--annotations", default="flywire_annotations.tsv")
    parser.add_argument("--manifest", default="data/input_manifest.json")
    parser.add_argument("--output", default="results/disinhibition_motifs.csv")
    parser.add_argument("--min-delta-hz", type=float, default=0.0)
    parser.add_argument("--hz-scale", type=float, default=1.0)
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    motifs = run_disinhibition_motif_search(
        connectivity_id=args.connectivity,
        annotations_id=args.annotations,
        manifest_path=args.manifest,
        output_path=args.output,
        min_delta_hz=args.min_delta_hz,
        hz_scale=args.hz_scale,
    )
    summary = summarize_intermediates(motifs)
    print(f"Wrote {len(motifs)} motif rows to {args.output}")
    print(f"Unique inhibitory intermediates with delta_hz > 0: {summary.shape[0]}")
    if not summary.empty:
        print(summary.head(10).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
