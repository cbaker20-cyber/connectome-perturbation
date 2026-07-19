# Quantitative benchmark comparison reports

Last updated: 2026-07-19

This document describes the quantitative benchmark comparison reporting layer. It improves scientific evaluation infrastructure only; it does not rerun simulations or change biological methods, perturbation algorithms, or statistical analyses.

## Purpose

For each registered benchmark, automatically report:

- expected metrics
- observed metrics
- absolute error
- relative error
- confidence interval (when applicable; otherwise `null`)
- pass/fail thresholds
- reproducibility status

## Components

| Artifact | Role |
|---|---|
| `data/benchmark_registry.yaml` | Benchmark definitions with expected metrics and reference outputs |
| `configs/benchmark_evaluation.yaml` | Default pass/fail thresholds by metric profile |
| `tools/benchmark_comparison.py` | Comparison engine |
| `tools/report_benchmark_comparison.py` | Writes `benchmark_comparison_report.json` |

## Registered benchmarks

| ID | Tier | Comparison source | Metrics compared |
|---|---|---|---|
| BM001 | infrastructure | `results/reproducibility_smoke_artifact.json` | `reproducibility_validation_pass` |
| BM002 | infrastructure | `results/toy_graph_artifact.json` (optional) | `node_count`, `edge_count`, `weak_component_count` |
| BM003 | validated | `results/statistics.csv` | `ascending_delta_hz`, `lo_delta_hz`, `row_count` + SHA-256 reproducibility |

## Usage

```bash
python tools/write_smoke_artifact.py --output results/reproducibility_smoke_artifact.json
python tools/write_toy_graph_artifact.py --output results/toy_graph_artifact.json
python tools/report_benchmark_comparison.py --fail-on-regression
```

## Report schema (per metric)

```json
{
  "name": "ascending_delta_hz",
  "expected": -129.0,
  "observed": -129.0,
  "absolute_error": 0.0,
  "relative_error": 0.0,
  "confidence_interval": null,
  "thresholds": {
    "absolute_error_max": 0.01,
    "relative_error_max": 0.001
  },
  "status": "pass"
}
```

## Open blockers

- Confidence intervals are not yet computed from trial-level outputs (field reserved as `null`).
- BM002 toy graph artifact is optional; observed metrics fall back to deterministic fixture computation.
- Live reruns are not compared automatically; reports compare committed reference outputs only.
