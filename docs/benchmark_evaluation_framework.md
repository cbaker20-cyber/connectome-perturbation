# Benchmark and evaluation framework

Last updated: 2026-07-19

This document defines the standardized benchmark registry and evaluation reporting for perturbation experiments. It improves scientific credibility infrastructure only; it does not rerun simulations or change biological conclusions.

## Purpose

Provide a machine-verifiable catalog of:

- benchmark datasets and required inputs;
- linked experiment registry rows;
- evaluation metrics and claim tiers;
- reference outputs with checksums;
- standardized JSON evaluation reports.

## Components

| Artifact | Role |
|---|---|
| `data/benchmark_registry.yaml` | Canonical benchmark definitions (BM001–BM003) |
| `configs/benchmark_evaluation.yaml` | Claim-tier evaluation requirements |
| `tools/validate_benchmarks.py` | Registry validation and report generation |
| `tools/report_benchmark_evaluation.py` | Writes `benchmark_evaluation_report.json` |
| `docs_config.yaml` | Shared minimum claim standards |

## Registered benchmarks

| ID | Tier | Experiment | Primary metric | Reference output |
|---|---|---|---|---|
| BM001 | infrastructure | E010 | reproducibility_validation_pass | `results/reproducibility_smoke_artifact.json` |
| BM002 | infrastructure | — | expected_graph_metrics_match | optional `results/toy_graph_artifact.json` |
| BM003 | validated | E007 | total_motor_population_firing_rate_per_trial | `results/statistics.csv` (pinned SHA-256) |

## Claim tiers

- **infrastructure** — metadata plumbing only; not interpretable as neuroscience.
- **exploratory** — low-trial screens; requires provenance and reference outputs.
- **validated** — requires matched trial counts, FDR reporting policy, zero-spike retention, and pinned reference outputs.

## Usage

```bash
python tools/validate_benchmarks.py
python tools/report_benchmark_evaluation.py --output benchmark_evaluation_report.json
```

## Traceability chain

`Benchmark Registry → Experiment Registry → Input Manifest → Reference Outputs → Evaluation Report`

CI validates the committed benchmark registry on every pull request.

## Open blockers

- Legacy experiments E001–E009 are documented in the experiment registry but not yet registered as benchmarks.
- BM002 optional toy graph artifact is not generated in CI yet.
- Evaluation reports do not yet compare live rerun metrics against reference CSV values (checksum-only for now).
