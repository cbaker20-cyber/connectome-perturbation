"""Unit tests for Sugar vs JO motor context-shift / DVI plumbing."""

from __future__ import annotations

import csv
import math
from pathlib import Path

import pytest

from connectome_analysis.context_comparison import (
    CLAIM_STATUS,
    build_synthetic_context_shift_fixture,
    compare_motor_context_profiles,
    compute_sugar_vs_jo_context_shift_rows,
    differential_vulnerability_index,
    resolve_annotations_path,
    resolve_baseline_path,
    resolve_context_shift_output_path,
    write_sugar_vs_jo_context_shift_csv,
)
from tools.path_resolver import repo_root_from


def test_dvi_known_answer_extremes_and_balanced():
    assert differential_vulnerability_index(10.0, 0.0) == pytest.approx(10.0 / (10.0 + 1e-12))
    assert differential_vulnerability_index(0.0, 10.0) == pytest.approx(-10.0 / (10.0 + 1e-12))
    assert differential_vulnerability_index(5.0, 5.0) == pytest.approx(0.0, abs=1e-12)
    mixed = differential_vulnerability_index(8.0, 2.0)
    assert mixed == pytest.approx(6.0 / (10.0 + 1e-12))


def test_dvi_rejects_invalid_rates():
    with pytest.raises(ValueError, match="non-negative"):
        differential_vulnerability_index(-1.0, 1.0)
    with pytest.raises(ValueError, match="finite"):
        differential_vulnerability_index(math.nan, 1.0)
    with pytest.raises(TypeError, match="numeric"):
        differential_vulnerability_index(True, 1.0)  # type: ignore[arg-type]


def test_compare_profiles_fills_missing_rates_and_preserves_string_ids():
    sugar = {"9007199254740993": 4.0, "motor_a": 2.0}
    jo = {"9007199254740993": 1.0, "motor_b": 3.0}
    rows = compare_motor_context_profiles(sugar, jo)
    by_id = {row["motor_id"]: row for row in rows}
    assert set(by_id) == {"9007199254740993", "motor_a", "motor_b"}
    assert by_id["motor_a"]["jo_hz"] == 0.0
    assert by_id["motor_b"]["sugar_hz"] == 0.0
    assert by_id["9007199254740993"]["context_bias"] == "sugar"
    assert by_id["motor_b"]["context_bias"] == "jo"
    assert all(row["claim_status"] == CLAIM_STATUS for row in rows)


def test_compare_profiles_rejects_duplicates_and_empty():
    with pytest.raises(ValueError, match="non-empty"):
        compare_motor_context_profiles({}, {"a": 1.0})
    with pytest.raises(ValueError, match="duplicates"):
        compare_motor_context_profiles({"a": 1.0}, {"a": 1.0}, motor_ids=["a", "a"])


def test_synthetic_fixture_dvi_ranking_is_deterministic():
    rows = compute_sugar_vs_jo_context_shift_rows()
    assert [row["motor_id"] for row in rows] == [
        "motor_jo_biased",
        "motor_sugar_biased",
        "motor_mixed",
        "9007199254740993",
        "motor_balanced",
    ]
    by_id = {row["motor_id"]: row for row in rows}
    assert by_id["motor_sugar_biased"]["dvi"] > 0
    assert by_id["motor_jo_biased"]["dvi"] < 0
    assert by_id["motor_balanced"]["abs_dvi"] == pytest.approx(0.0, abs=1e-9)
    assert by_id["motor_mixed"]["dvi"] == pytest.approx(
        differential_vulnerability_index(8.0, 2.0)
    )
    # Absolute DVI ranks extremes first; sugar/jo extremes share abs_dvi ≈ 1.
    assert by_id["motor_sugar_biased"]["abs_dvi"] == pytest.approx(
        by_id["motor_jo_biased"]["abs_dvi"]
    )
    assert all(int(row["fixture_seed"]) == 60 for row in rows)


def test_path_resolver_used_for_annotations_and_output_boundaries(tmp_path):
    ann = resolve_annotations_path("flywire_annotations.tsv")
    assert ann.name == "flywire_annotations.tsv"
    assert ann.exists()

    out = resolve_context_shift_output_path("results/sugar_vs_jo_context_shift.csv")
    assert out.name == "sugar_vs_jo_context_shift.csv"
    root = repo_root_from()
    assert out.is_relative_to(root)

    with pytest.raises(ValueError, match="within the repository"):
        resolve_baseline_path(tmp_path / "outside.parquet")


def test_write_csv_uses_repo_path_resolver_and_known_columns(tmp_path):
    # Write under a temp directory that we treat as a fake repo root by copying
    # the resolver boundary check via explicit repo_root (tmp must contain marker).
    (tmp_path / "README.md").write_text("fixture root\n", encoding="utf-8")
    out = write_sugar_vs_jo_context_shift_csv(
        "results/sugar_vs_jo_context_shift.csv",
        repo_root=tmp_path,
    )
    assert out.exists()
    assert out == tmp_path / "results" / "sugar_vs_jo_context_shift.csv"

    with out.open(encoding="utf-8", newline="") as handle:
        reader_rows = list(csv.DictReader(handle))
    assert reader_rows
    assert {row["claim_status"] for row in reader_rows} == {CLAIM_STATUS}
    assert "motor_sugar_biased" in {row["motor_id"] for row in reader_rows}
    assert "9007199254740993" in {row["motor_id"] for row in reader_rows}


def test_repo_default_writer_produces_tracked_results_csv():
    path = write_sugar_vs_jo_context_shift_csv()
    assert path == repo_root_from() / "results" / "sugar_vs_jo_context_shift.csv"
    assert path.exists()
    fixture = build_synthetic_context_shift_fixture()
    assert fixture["claim_status"] == CLAIM_STATUS
