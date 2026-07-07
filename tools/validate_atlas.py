"""Validate FLY Grand Atlas JSONL run records.

This intentionally uses only the Python standard library so the first CI check
can run before the research environment is fully repaired.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RUNS_PATH = ROOT / "atlas" / "perturbations" / "example_toy_run.jsonl"

REQUIRED_TOP_LEVEL = {
    "run_id",
    "created_at",
    "code_version",
    "context",
    "model",
    "input_data",
    "perturbation",
    "metrics",
    "outputs",
    "validation_status",
}

VALID_STATUSES = {"toy_validated", "exploratory", "blocked", "invalid", "validated"}
VALID_TARGET_TYPES = {"node", "edge", "node_set", "edge_set", "none"}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate_run_record(record: dict[str, Any]) -> None:
    missing = REQUIRED_TOP_LEVEL - set(record)
    _require(not missing, f"missing top-level fields: {sorted(missing)}")

    _require(record["validation_status"] in VALID_STATUSES, "invalid validation_status")

    context = record["context"]
    _require(isinstance(context.get("input_neurons"), list), "input_neurons must be a list")
    _require(isinstance(context.get("output_neurons"), list), "output_neurons must be a list")
    _require(all(isinstance(x, str) for x in context["input_neurons"]), "input neuron IDs must be strings")
    _require(all(isinstance(x, str) for x in context["output_neurons"]), "output neuron IDs must be strings")

    perturbation = record["perturbation"]
    _require(perturbation.get("target_type") in VALID_TARGET_TYPES, "invalid perturbation target_type")
    _require(isinstance(perturbation.get("targets"), list), "perturbation targets must be a list")
    _require(all(isinstance(x, str) for x in perturbation["targets"]), "perturbation targets must be strings")

    metrics = record["metrics"]
    _require(isinstance(metrics.get("primary"), str) and metrics["primary"], "metrics.primary is required")

    outputs = record["outputs"]
    _require(isinstance(outputs.get("files"), list), "outputs.files must be a list")


def iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                yield line_number, json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSON: {exc}") from exc


def main() -> int:
    _require(RUNS_PATH.exists(), f"missing run file: {RUNS_PATH}")
    count = 0
    for line_number, record in iter_jsonl(RUNS_PATH):
        validate_run_record(record)
        count += 1
    _require(count > 0, "no run records found")
    print(f"Validated {count} atlas run record(s) from {RUNS_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
