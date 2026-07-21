"""Compare motor firing profiles across Sugar vs Johnston's Organ (JO) contexts.

Computes a node-wise Differential Vulnerability Index (DVI) for motor targets:

    DVI_i = (r_i^{sugar} - r_i^{JO}) / (r_i^{sugar} + r_i^{JO} + eps)

Positive DVI indicates sugar-biased motor activity; negative indicates JO /
grooming bias. Absolute DVI quantifies context-shift magnitude independent of
sign.

Default exports use a fixed-seed synthetic fixture so CI and smoke paths do not
require Brian2 baseline Parquets. Real baselines may be supplied explicitly;
outputs remain ``not_interpretable_as_neuroscience`` until a full provenance
chain (manifest, seed, commit, validation) is attached.
"""

from __future__ import annotations

import csv
import math
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from tools.path_resolver import repo_root_from, require_repo_path, resolve_input

CLAIM_STATUS = "not_interpretable_as_neuroscience"
DEFAULT_OUTPUT = "results/sugar_vs_jo_context_shift.csv"
DVI_EPSILON = 1e-12
CONTEXT_BIAS_THRESHOLD = 1e-9


def differential_vulnerability_index(
    sugar_hz: float,
    jo_hz: float,
    *,
    epsilon: float = DVI_EPSILON,
) -> float:
    """Return signed DVI for one motor node.

    ``DVI = (sugar_hz - jo_hz) / (sugar_hz + jo_hz + epsilon)``.

    Both rates must be finite and non-negative. The result lies in
    ``(-1, 1)`` for finite non-negative inputs when ``epsilon > 0``.
    """
    if isinstance(sugar_hz, bool) or isinstance(jo_hz, bool):
        raise TypeError("rates must be numeric, not bool")
    sugar = float(sugar_hz)
    jo = float(jo_hz)
    if not math.isfinite(sugar) or not math.isfinite(jo):
        raise ValueError("rates must be finite")
    if sugar < 0.0 or jo < 0.0:
        raise ValueError("rates must be non-negative")
    if not math.isfinite(epsilon) or epsilon <= 0.0:
        raise ValueError("epsilon must be a positive finite number")
    return (sugar - jo) / (sugar + jo + epsilon)


def _as_nonneg_rate_map(rates: Mapping[Any, Any], *, label: str) -> dict[str, float]:
    if not rates:
        raise ValueError(f"{label} must be a non-empty mapping")
    out: dict[str, float] = {}
    for key, value in rates.items():
        motor_id = str(key)
        if not motor_id:
            raise ValueError(f"{label} keys must be non-empty stringifiable IDs")
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{label}[{motor_id!r}] must be a finite number")
        number = float(value)
        if not math.isfinite(number) or number < 0.0:
            raise ValueError(f"{label}[{motor_id!r}] must be non-negative and finite")
        if motor_id in out:
            raise ValueError(f"{label} contains duplicate motor_id {motor_id!r}")
        out[motor_id] = number
    return out


def _context_bias_label(dvi: float, *, threshold: float = CONTEXT_BIAS_THRESHOLD) -> str:
    if dvi > threshold:
        return "sugar"
    if dvi < -threshold:
        return "jo"
    return "balanced"


def compare_motor_context_profiles(
    sugar_rates: Mapping[Any, Any],
    jo_rates: Mapping[Any, Any],
    motor_ids: Sequence[Any] | None = None,
    *,
    epsilon: float = DVI_EPSILON,
) -> list[dict[str, object]]:
    """Build node-wise Sugar vs JO comparison rows for motor targets.

    When ``motor_ids`` is omitted, the union of both rate maps is used (sorted
    for determinism). Missing rates default to ``0.0`` so silent motors in one
    context remain visible in the shift table.
    """
    sugar = _as_nonneg_rate_map(sugar_rates, label="sugar_rates")
    jo = _as_nonneg_rate_map(jo_rates, label="jo_rates")

    if motor_ids is None:
        ids = sorted(set(sugar) | set(jo))
    else:
        ids = [str(mid) for mid in motor_ids]
        if not ids:
            raise ValueError("motor_ids must be non-empty when provided")
        if any(not mid for mid in ids):
            raise ValueError("motor_ids must contain only non-empty IDs")
        if len(set(ids)) != len(ids):
            raise ValueError("motor_ids must not contain duplicates")

    rows: list[dict[str, object]] = []
    for motor_id in ids:
        sugar_hz = sugar.get(motor_id, 0.0)
        jo_hz = jo.get(motor_id, 0.0)
        dvi = differential_vulnerability_index(sugar_hz, jo_hz, epsilon=epsilon)
        delta = sugar_hz - jo_hz
        rows.append(
            {
                "motor_id": motor_id,
                "sugar_hz": sugar_hz,
                "jo_hz": jo_hz,
                "delta_hz": delta,
                "abs_delta_hz": abs(delta),
                "dvi": dvi,
                "abs_dvi": abs(dvi),
                "context_bias": _context_bias_label(dvi),
                "claim_status": CLAIM_STATUS,
            }
        )
    return rows


def build_synthetic_context_shift_fixture(*, seed: int = 60) -> dict[str, object]:
    """Return a fixed known-answer Sugar/JO motor rate fixture.

    Motor targets encode sugar-biased, JO-biased, balanced, and mixed profiles
    so DVI ranking is independently checkable without Brian2 outputs.
    """
    # seed retained for provenance / CSV metadata; rates are intentionally fixed.
    _ = int(seed)
    sugar_rates = {
        "motor_sugar_biased": 10.0,
        "motor_jo_biased": 0.0,
        "motor_balanced": 5.0,
        "motor_mixed": 8.0,
        "9007199254740993": 4.0,  # 64-bit-safe string ID sentinel
    }
    jo_rates = {
        "motor_sugar_biased": 0.0,
        "motor_jo_biased": 10.0,
        "motor_balanced": 5.0,
        "motor_mixed": 2.0,
        "9007199254740993": 1.0,
    }
    motor_ids = [
        "motor_sugar_biased",
        "motor_jo_biased",
        "motor_balanced",
        "motor_mixed",
        "9007199254740993",
    ]
    return {
        "seed": int(seed),
        "context_ids": ["sugar", "jo"],
        "motor_ids": motor_ids,
        "sugar_rates": sugar_rates,
        "jo_rates": jo_rates,
        "claim_status": CLAIM_STATUS,
    }


def compute_sugar_vs_jo_context_shift_rows(
    fixture: Mapping[str, object] | None = None,
    *,
    epsilon: float = DVI_EPSILON,
) -> list[dict[str, object]]:
    """Compute context-shift rows from a fixture (synthetic by default)."""
    data = dict(fixture) if fixture is not None else build_synthetic_context_shift_fixture()
    sugar_rates = data["sugar_rates"]
    jo_rates = data["jo_rates"]
    motor_ids = data.get("motor_ids")
    if not isinstance(sugar_rates, Mapping) or not isinstance(jo_rates, Mapping):
        raise ValueError("fixture must provide sugar_rates and jo_rates mappings")
    ids: Sequence[Any] | None
    if motor_ids is None:
        ids = None
    elif isinstance(motor_ids, Sequence) and not isinstance(motor_ids, (str, bytes)):
        ids = motor_ids
    else:
        raise ValueError("fixture motor_ids must be a sequence of IDs")

    rows = compare_motor_context_profiles(
        sugar_rates,
        jo_rates,
        ids,
        epsilon=epsilon,
    )
    fixture_seed = data.get("seed")
    for row in rows:
        row["fixture_seed"] = int(fixture_seed) if fixture_seed is not None else ""
    # Rank by descending absolute DVI, then motor_id for determinism.
    rows.sort(key=lambda r: (-float(r["abs_dvi"]), str(r["motor_id"])))  # type: ignore[arg-type]
    return rows


def write_sugar_vs_jo_context_shift_csv(
    output_path: str | Path = DEFAULT_OUTPUT,
    *,
    repo_root: Path | None = None,
    fixture: Mapping[str, object] | None = None,
    epsilon: float = DVI_EPSILON,
) -> Path:
    """Write Sugar vs JO motor context-shift table under the repository root."""
    root = repo_root_from(repo_root)
    out = require_repo_path(root, root / Path(output_path), "context shift output")
    out.parent.mkdir(parents=True, exist_ok=True)
    rows = compute_sugar_vs_jo_context_shift_rows(fixture, epsilon=epsilon)
    fieldnames = [
        "motor_id",
        "sugar_hz",
        "jo_hz",
        "delta_hz",
        "abs_delta_hz",
        "dvi",
        "abs_dvi",
        "context_bias",
        "claim_status",
        "fixture_seed",
    ]
    with out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return out


def resolve_annotations_path(
    identifier: str = "flywire_annotations.tsv",
    *,
    repo_root: Path | None = None,
) -> Path:
    """Resolve annotation inputs through ``tools.path_resolver``."""
    return resolve_input(identifier, repo_root=repo_root)


def resolve_baseline_path(
    path: str | Path,
    *,
    repo_root: Path | None = None,
) -> Path:
    """Resolve a repo-relative baseline spike path and require it stay in-repo."""
    root = repo_root_from(repo_root)
    return require_repo_path(root, root / Path(path), "baseline spike path")


def resolve_context_shift_output_path(
    path: str | Path = DEFAULT_OUTPUT,
    *,
    repo_root: Path | None = None,
) -> Path:
    """Resolve the context-shift CSV output path through the path resolver."""
    root = repo_root_from(repo_root)
    return require_repo_path(root, root / Path(path), "context shift output")


if __name__ == "__main__":
    path = write_sugar_vs_jo_context_shift_csv()
    print(path)
