# Research documentation mapping

Last updated: 2026-07-18

This document maps the **Research Documentation Pack** (canonical specification) to repository implementation. The pack lives at the **repository root** (`03_EXPERIMENT_REGISTRY.csv`, `11_CLAIMS_REGISTER.csv`, etc.). A legacy mirror exists under `connectome_research_docs/`; treat the root copies as authoritative unless a human review says otherwise.

## Summary

| Research document | Purpose | Repository implementation | Enforced by |
|---|---|---|---|
| `00_PROJECT_STATE.md` | Current scientific snapshot and caveats | Root `00_PROJECT_STATE.md` | Human review; overlaps engineering `TASKS.md` / `ROADMAP.md` |
| `01_LIVING_RESEARCH_LOG.md` | Chronological lab notebook | Root `01_LIVING_RESEARCH_LOG.md` | Human review |
| `02_METHODS_MASTER.md` | Publication-ready methods | Root `02_METHODS_MASTER.md` | Human review |
| `03_EXPERIMENT_REGISTRY.csv` | Experiment metadata and outputs | Root CSV; scripts in `perturbation/`, `test_run.py` | `tools/validate_research_docs.py` |
| `04_RESULTS_LEDGER.csv` | Result-level effects and status | Root CSV; outputs under `results/` | `tools/validate_research_docs.py` |
| `05_CODE_CHANGELOG.md` | Code/method changes | Root markdown | Human review |
| `06_DECISION_LOG.md` | Why major choices were made | Root markdown | Required-file check |
| `07_ISSUES_AND_CAVEATS.md` | Reviewer-proof guardrails | Root markdown | Required-file check |
| `08_DATA_PROVENANCE.md` | Dataset versioning requirements | Root markdown + `data/input_manifest.json` + `data/input_provenance_registry.yaml` | `tools/validate_reproducibility.py` (`--require-provenance` in CI) |
| `09_REPRODUCIBILITY_CHECKLIST.md` | Pre-submission rerun checklist | Root markdown | Partially automated via CI smoke path; full checklist still manual |
| `10_PUBLICATION_NARRATIVE_TRACKER.md` | Paper/competition framing | Root markdown | Human review |
| `11_CLAIMS_REGISTER.csv` | Claims ↔ evidence ↔ status | Root CSV | `tools/validate_research_docs.py` |
| `12_LITERATURE_AND_SOURCE_NOTES.md` | Source papers | Root markdown | Required-file check |
| `docs_config.yaml` | Status labels and claim standards | Root YAML | Loaded by `tools/validate_research_docs.py` |

## Per-document detail

### `03_EXPERIMENT_REGISTRY.csv`

**Purpose:** Register every simulation, graph analysis, rerun, or statistical test with parameters, scripts, outputs, validation status, and linked claim IDs.

**Implemented:**

- Nine experiments (E001–E009) recorded with scripts, trial counts, and `claim_ids`.
- Cross-reference validation: `claim_ids` must exist in `11_CLAIMS_REGISTER.csv`.
- Duplicate `experiment_id` detection.
- Validated experiments with non-wildcard `primary_output` can be checked against on-disk files (optional strict mode).

**Not yet implemented:**

- Automatic binding to `output_manifest.json` or git commit hash per experiment.
- CI enforcement of validated `primary_output` existence (wildcards like `results/hq_*.parquet` remain manual).

**Enforced by:** `tools/validate_research_docs.py`, CI step `Validate research documentation pack`.

### `04_RESULTS_LEDGER.csv`

**Purpose:** Result-level table with effect sizes, p/q values, interpretation, and paper placement.

**Implemented:**

- Twelve results (R001–R012) linked to experiments.
- `experiment_id` foreign-key validation.
- Duplicate `result_id` detection.

**Not yet implemented:**

- Automated q-value verification against `results/statistics.csv`.
- Binding results to output manifest checksums.

**Enforced by:** `tools/validate_research_docs.py`.

### `11_CLAIMS_REGISTER.csv`

**Purpose:** Every interpretable claim mapped to evidence files, status, caveats, and safe wording.

**Implemented:**

- Seven claims (C001–C007) with evidence references.
- Evidence path resolution for repo-relative scripts (`perturbation/*.py`, root scripts) and `results/*` files.
- Wildcard and notebook references (`hq_*`, `Pasted text.txt`) are skipped intentionally.

**Not yet implemented:**

- Commit hash per claim.
- Strict `--require-provenance` linkage to `data/input_manifest.json`.

**Enforced by:** `tools/validate_research_docs.py`.

### `08_DATA_PROVENANCE.md` + input manifest

**Purpose:** Document completeness/connectivity/annotation versions and per-run provenance requirements.

**Implemented:**

- `data/input_manifest.json` with SHA-256 checksums for five connectome inputs.
- `data/input_provenance_registry.yaml` with source-backed DOI/URL, license, access date, row counts, and materialization IDs.
- `docs/materialization-policy.md` for materialization 630 vs 783.
- `tools/validate_reproducibility.py` validates checksums, smoke config alignment, and claim-ready provenance via `--require-provenance` (enabled in CI).

**Not yet implemented:**

- Binding experiment registry entries to output manifests.

**Enforced by:** `tools/validate_reproducibility.py`, `tools/build_input_manifest.py`, `data/input_provenance_registry.yaml`.

### `09_REPRODUCIBILITY_CHECKLIST.md`

**Purpose:** Pre-submission checklist for environment, data, simulation, statistics, figures, and narrative.

**Implemented (partial automation):**

| Checklist section | Automated coverage |
|---|---|
| Environment | `output_manifest.json` records `environment` when outputs declared |
| Data file versions | `data/input_manifest.json` + `configs/smoke_run.yaml` |
| Random seed | `run_config.random_seed` in output manifest |
| Git commit | `repo_commit` in output manifest |
| Smoke artifact checksum | CI smoke provenance step |

**Not yet implemented:**

- Brian2 version pinning in CI.
- Parquet output checksumming for simulation runs.
- Figure-to-source CSV linkage validation.

**Enforced by:** `tools/validate_reproducibility.py` (partial); remainder is manual.

### `06_DECISION_LOG.md`, `07_ISSUES_AND_CAVEATS.md`

**Purpose:** Preserve methodological decisions and reviewer-proof caveats (trial counts, silencing model, FDR, graph nulls).

**Implemented:**

- Markdown records at repo root mirror the canonical pack.
- Engineering docs (`AGENTS.md`, `docs/reproducibility-audit.md`) reference the same guardrails.

**Not yet implemented:**

- Machine validation of decision IDs against code changes.

**Enforced by:** Required-file presence in `tools/validate_research_docs.py`.

### `docs_config.yaml`

**Purpose:** Status labels and minimum claim standards (matched trials, zero-spike retention, FDR).

**Implemented:**

- Loaded by `tools/validate_research_docs.py` for status-label validation.
- Legacy compound statuses (`validated/revised`, `validated-in-code`) accepted via prefix rules.

**Not yet implemented:**

- Automated enforcement of `minimum_claim_standard` fields against experiment rows.

**Enforced by:** `tools/validate_research_docs.py` (status labels only).

## Engineering cross-links

| Engineering artifact | Research pack link |
|---|---|
| `tools/validate_research_docs.py` | Validates registry, ledger, claims cross-references |
| `tools/validate_reproducibility.py` | Validates input/output manifests per `08_DATA_PROVENANCE` |
| `configs/smoke_run.yaml` | Smoke materialization per `08_DATA_PROVENANCE` |
| `.github/workflows/reproducibility-tools.yml` | CI for manifests + research docs |
| `ROADMAP.md` | Prioritized gaps derived from this mapping |

## Legacy mirror

`connectome_research_docs/` contains a copy of the pack plus `tools/append_log_entry.py`. Prefer editing **root-level** research files. The subdirectory `connectome_research_docs/tools/validate_research_docs.py` delegates to `tools/validate_research_docs.py`.

## Next highest-impact gaps

1. Fill authoritative provenance in `data/input_manifest.json`.
2. Bind experiment registry entries to `output_manifest.json` and commit hash.
3. Enforce `docs_config.yaml` `minimum_claim_standard` against experiment rows.
4. Automate remaining `09_REPRODUCIBILITY_CHECKLIST.md` simulation/statistics items.
