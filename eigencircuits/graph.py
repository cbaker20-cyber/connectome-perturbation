from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix

from .common import ANN, COMP, CON, root_ids


def load_signed_matrix(completeness=COMP, connectivity=CON):
    ids = root_ids(pd.read_csv(completeness, index_col=0).index)
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate neuron IDs")
    edges = pd.read_parquet(connectivity)
    n = len(ids)
    pre = edges.Presynaptic_Index.to_numpy()
    post = edges.Postsynaptic_Index.to_numpy()
    for index, label in [(pre, "Presynaptic"), (post, "Postsynaptic")]:
        if not np.issubdtype(index.dtype, np.integer) or np.any((index < 0) | (index >= n)):
            raise ValueError(f"invalid {label} indices")
        # Compare exact int64 arrays without allocating millions of Python strings.
        if not np.array_equal(np.asarray(ids, dtype=np.int64)[index], edges[label+"_ID"].to_numpy()):
            raise ValueError(f"{label} index/ID mismatch")
    data = edges["Excitatory x Connectivity"].to_numpy(dtype=float)
    if not np.isfinite(data).all() or np.any(data == 0):
        raise ValueError("nonfinite or zero input weights; inspect instead of silently dropping rows")
    w = csr_matrix((data, (post, pre)), shape=(n, n))
    w.sum_duplicates()
    if np.any(w.data == 0):
        raise ValueError("opposite-sign duplicate edges cancel")
    return w, np.asarray(ids)


def strong_matrix(w, fraction=.05):
    """Threshold absolute postsynaptic input fractions; retain the original sign."""
    if not 0 < fraction <= 1:
        raise ValueError("fraction must be in (0,1]")
    incoming = np.asarray(abs(w).sum(axis=1)).ravel()
    coo = w.tocoo()
    keep = np.abs(coo.data) >= fraction * incoming[coo.row]
    return csr_matrix((coo.data[keep], (coo.row[keep], coo.col[keep])), shape=w.shape)


def features(w, ids, annotations=ANN):
    from perturbation.cell_groups import transmitter_polarity
    outgoing = w.tocsc()
    positive = np.asarray((w > 0).sum(axis=0)).ravel()
    negative = np.asarray((w < 0).sum(axis=0)).ravel()
    signs = np.select([(positive > 0) & (negative == 0), (negative > 0) & (positive == 0),
                       (positive > 0) & (negative > 0)], ["excitatory", "inhibitory", "mixed"], default="no_outputs")
    f = pd.DataFrame({"root_id": ids, "in_degree": np.diff(w.indptr),
                      "out_degree": np.diff(outgoing.indptr),
                      "in_strength": np.asarray(abs(w).sum(axis=1)).ravel(),
                      "out_strength": np.asarray(abs(w).sum(axis=0)).ravel(),
                      "strong_out_mass": np.asarray(abs(strong_matrix(w)).sum(axis=0)).ravel(),
                      "model_sign": signs})
    ann = pd.read_csv(annotations, sep="\t", dtype={"root_id": str}, low_memory=False)
    if ann.root_id.duplicated().any():
        raise ValueError("duplicate annotation IDs; resolve before joining")
    for name in ["classical_fast", "shiu_2024"]:
        ann[name] = transmitter_polarity(ann, name)
    columns = ["root_id", "cell_type", "super_class", "top_nt", "known_nt", "classical_fast", "shiu_2024"]
    f = f.merge(ann[columns], on="root_id", how="left", validate="one_to_one", indicator=True)
    f["annotation_available"] = f.pop("_merge").eq("both")
    return f
