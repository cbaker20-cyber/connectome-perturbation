import copy

import pytest

from connectome_analysis.targeted_validation_summary import (
    validate_targeted_validation_summary_rows,
)


def manifest():
    return {"parameters": {"n_run": 30, "t_run_ms": 1000}}


def rows():
    return [
        {"source": "sugar", "target": "AN", "n_run": 30, "t_run_ms": 1000, "score": 1.0},
        {
            "source": "sugar",
            "target": "brain_motor_neuron",
            "n_run": 30,
            "t_run_ms": 1000,
            "score": 2.0,
        },
        {"source": "gustatory", "target": "AN", "n_run": 30, "t_run_ms": 1000, "score": 3.0},
        {
            "source": "gustatory",
            "target": "brain_motor_neuron",
            "n_run": 30,
            "t_run_ms": 1000,
            "score": 4.0,
        },
    ]


def test_accepts_complete_consistent_finite_summary():
    validate_targeted_validation_summary_rows(rows(), manifest(), numeric_fields=["score"])


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda value: value.pop(), "cover exactly the four"),
        (lambda value: value.append(copy.deepcopy(value[0])), "duplicate cells"),
        (lambda value: value[0].__setitem__("source", "unexpected"), "cover exactly the four"),
        (lambda value: value[0].__setitem__("n_run", 29), "disagrees with manifest"),
        (lambda value: value[0].__setitem__("t_run_ms", 999), "disagrees with manifest"),
        (lambda value: value[0].__setitem__("score", float("nan")), "must be finite"),
        (lambda value: value[0].__setitem__("score", float("inf")), "must be finite"),
        (lambda value: value[0].pop("score"), "missing required fields"),
    ],
)
def test_rejects_incomplete_inconsistent_or_nonfinite_rows(mutate, message):
    value = rows()
    mutate(value)

    with pytest.raises(ValueError, match=message):
        validate_targeted_validation_summary_rows(value, manifest(), numeric_fields=["score"])


def test_requires_explicit_unique_numeric_fields():
    with pytest.raises(ValueError, match="non-empty strings"):
        validate_targeted_validation_summary_rows(rows(), manifest(), numeric_fields=[])

    with pytest.raises(ValueError, match="must not contain duplicates"):
        validate_targeted_validation_summary_rows(rows(), manifest(), numeric_fields=["score", "score"])

    with pytest.raises(ValueError, match="must not repeat"):
        validate_targeted_validation_summary_rows(rows(), manifest(), numeric_fields=["n_run"])
