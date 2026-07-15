"""Strict CSV parsing for targeted-validation summary artifacts.

This module validates only repository-local serialization and schema shape. It does
not assess biological validity, execute simulations, or support neuroscience claims.
"""

from __future__ import annotations

import csv
import io
from collections.abc import Sequence

_REQUIRED_COLUMNS = ("source", "target", "n_run", "t_run_ms")


def parse_targeted_validation_summary_csv(
    artifact_bytes: bytes,
    *,
    numeric_fields: Sequence[str],
) -> list[dict[str, str]]:
    """Parse a UTF-8 CSV artifact under an exact, caller-declared schema.

    The header must contain exactly the four required identity/parameter columns plus
    the caller-declared numeric fields, in that order. Duplicate headers, blank rows,
    missing or extra cells, ambiguous whitespace, and invalid UTF-8 fail closed.
    Returned values remain strings so semantic conversion stays centralized in the
    existing summary validator.
    """

    if not isinstance(artifact_bytes, bytes) or not artifact_bytes:
        raise ValueError("artifact_bytes must be non-empty bytes")
    if not isinstance(numeric_fields, Sequence) or isinstance(numeric_fields, (str, bytes)):
        raise ValueError("numeric_fields must be an array")

    fields = list(numeric_fields)
    if not fields or any(not isinstance(field, str) or not field for field in fields):
        raise ValueError("numeric_fields must contain non-empty strings")
    if len(fields) != len(set(fields)):
        raise ValueError("numeric_fields must not contain duplicates")
    if set(_REQUIRED_COLUMNS).intersection(fields):
        raise ValueError("numeric_fields must not repeat required columns")
    if any(field != field.strip() for field in fields):
        raise ValueError("numeric_fields must not contain surrounding whitespace")

    try:
        text = artifact_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("summary CSV must be valid UTF-8") from exc
    if text.startswith("\ufeff"):
        raise ValueError("summary CSV must not contain a UTF-8 BOM")
    if "\x00" in text:
        raise ValueError("summary CSV must not contain NUL bytes")

    expected_header = [*_REQUIRED_COLUMNS, *fields]
    reader = csv.reader(io.StringIO(text, newline=""), strict=True)
    try:
        header = next(reader)
    except StopIteration as exc:
        raise ValueError("summary CSV must contain a header") from exc
    except csv.Error as exc:
        raise ValueError("summary CSV is malformed") from exc

    if len(header) != len(set(header)):
        raise ValueError("summary CSV header must not contain duplicate columns")
    if header != expected_header:
        raise ValueError(f"summary CSV header must equal {expected_header!r}")

    rows: list[dict[str, str]] = []
    try:
        for line_number, values in enumerate(reader, start=2):
            if not values or all(value == "" for value in values):
                raise ValueError(f"summary CSV row {line_number} must not be blank")
            if len(values) != len(expected_header):
                raise ValueError(
                    f"summary CSV row {line_number} has {len(values)} cells; expected {len(expected_header)}"
                )
            if any(value == "" for value in values):
                raise ValueError(f"summary CSV row {line_number} must not contain empty cells")
            if any(value != value.strip() for value in values):
                raise ValueError(f"summary CSV row {line_number} must not contain surrounding whitespace")
            rows.append(dict(zip(expected_header, values, strict=True)))
    except csv.Error as exc:
        raise ValueError("summary CSV is malformed") from exc

    if not rows:
        raise ValueError("summary CSV must contain at least one data row")
    return rows
