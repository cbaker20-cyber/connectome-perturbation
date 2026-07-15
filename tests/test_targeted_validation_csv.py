import pytest

from connectome_analysis.targeted_validation_csv import (
    parse_targeted_validation_summary_csv,
)


HEADER = "source,target,n_run,t_run_ms,score\n"
ROWS = (
    "sugar,AN,30,1000,1.0\n"
    "sugar,brain_motor_neuron,30,1000,2.0\n"
    "gustatory,AN,30,1000,3.0\n"
    "gustatory,brain_motor_neuron,30,1000,4.0\n"
)


def test_parses_exact_declared_schema_without_type_coercion():
    parsed = parse_targeted_validation_summary_csv(
        (HEADER + ROWS).encode("utf-8"), numeric_fields=["score"]
    )

    assert len(parsed) == 4
    assert parsed[0] == {
        "source": "sugar",
        "target": "AN",
        "n_run": "30",
        "t_run_ms": "1000",
        "score": "1.0",
    }


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ("target,source,n_run,t_run_ms,score\n" + ROWS, "header must equal"),
        ("source,target,n_run,t_run_ms,score,extra\n", "header must equal"),
        ("source,target,n_run,t_run_ms,score,score\n", "duplicate columns"),
        (HEADER, "at least one data row"),
        (HEADER + "\n" + ROWS, "must not be blank"),
        (HEADER + "sugar,AN,30,1000\n", "cells; expected"),
        (HEADER + "sugar,AN,30,1000,1.0,extra\n", "cells; expected"),
        (HEADER + "sugar,AN,30,1000,\n", "empty cells"),
        (HEADER + " sugar,AN,30,1000,1.0\n", "surrounding whitespace"),
        ('source,target,n_run,t_run_ms,score\n"sugar,AN,30,1000,1.0\n', "malformed"),
    ],
)
def test_rejects_ambiguous_or_malformed_rows(payload, message):
    with pytest.raises(ValueError, match=message):
        parse_targeted_validation_summary_csv(payload.encode("utf-8"), numeric_fields=["score"])


def test_rejects_invalid_utf8_bom_and_nul():
    with pytest.raises(ValueError, match="valid UTF-8"):
        parse_targeted_validation_summary_csv(b"\xff", numeric_fields=["score"])
    with pytest.raises(ValueError, match="must not contain a UTF-8 BOM"):
        parse_targeted_validation_summary_csv(("\ufeff" + HEADER + ROWS).encode("utf-8"), numeric_fields=["score"])
    with pytest.raises(ValueError, match="NUL"):
        parse_targeted_validation_summary_csv((HEADER + ROWS + "\x00").encode("utf-8"), numeric_fields=["score"])


def test_requires_explicit_unique_numeric_fields():
    payload = (HEADER + ROWS).encode("utf-8")
    with pytest.raises(ValueError, match="non-empty strings"):
        parse_targeted_validation_summary_csv(payload, numeric_fields=[])
    with pytest.raises(ValueError, match="must not contain duplicates"):
        parse_targeted_validation_summary_csv(payload, numeric_fields=["score", "score"])
    with pytest.raises(ValueError, match="must not repeat required"):
        parse_targeted_validation_summary_csv(payload, numeric_fields=["n_run"])
    with pytest.raises(ValueError, match="surrounding whitespace"):
        parse_targeted_validation_summary_csv(payload, numeric_fields=[" score"])
