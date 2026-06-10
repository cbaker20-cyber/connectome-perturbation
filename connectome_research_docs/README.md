# Connectome Perturbation Living Research Record

Created: 2026-06-10
Project: connectome-perturbation

This folder is a living documentation system for the Drosophila/FlyWire connectome perturbation project. It is designed to keep scientific claims, code changes, methods versions, exploratory findings, validated findings, caveats, and next steps in separate but cross-linked records.

## How to use this system

1. Start every work session in `01_LIVING_RESEARCH_LOG.md` using the daily template in `templates/daily_lab_entry_template.md`.
2. Register every simulation, graph analysis, rerun, or statistical test in `03_EXPERIMENT_REGISTRY.csv` before or immediately after running it.
3. Put every result that might appear in a poster, paper, or competition application in `04_RESULTS_LEDGER.csv` and `11_CLAIMS_REGISTER.csv`.
4. Log every code or methodological change in `05_CODE_CHANGELOG.md`, even if it feels small.
5. Update `02_METHODS_MASTER.md` only after a method becomes the current accepted pipeline.
6. Never upgrade an exploratory screen into a validated claim unless it has a matching entry in the results ledger and claims register.

## File map

| File | Purpose |
|---|---|
| `00_PROJECT_STATE.md` | Current snapshot of the project, strongest claims, and active caveats. |
| `01_LIVING_RESEARCH_LOG.md` | Chronological lab notebook reconstructed from your journals, with space for future entries. |
| `02_METHODS_MASTER.md` | Current version of the methodology, written in publication-ready form. |
| `03_EXPERIMENT_REGISTRY.csv` | Master table of experiments/analyses, parameters, outputs, and validation status. |
| `04_RESULTS_LEDGER.csv` | Result-level table: effect sizes, p/q values, status, and interpretation. |
| `05_CODE_CHANGELOG.md` | Code and methods changes with scientific consequences. |
| `06_DECISION_LOG.md` | Why major choices were made. Useful for judges/reviewers. |
| `07_ISSUES_AND_CAVEATS.md` | Known limitations, false starts, and guardrails. |
| `08_DATA_PROVENANCE.md` | Where datasets came from, what version they are, and how they are used. |
| `09_REPRODUCIBILITY_CHECKLIST.md` | Steps needed to rerun the project from scratch. |
| `10_PUBLICATION_NARRATIVE_TRACKER.md` | Paper/competition story, claims, figures, and reviewer-proof framing. |
| `11_CLAIMS_REGISTER.csv` | Every claim mapped to evidence, status, caveats, and required next action. |
| `12_LITERATURE_AND_SOURCE_NOTES.md` | Source papers and how they support the methods. |
| `templates/` | Copy/paste templates for future entries. |
| `tools/` | Small helper scripts to add new entries and validate the docs. |

## Status labels

Use these exact labels consistently:

- `planned`: not run yet.
- `exploratory`: run with low trial count, prototype code, or incomplete controls.
- `validated`: rerun with accepted trial count and accepted statistics.
- `revised`: earlier result changed after better controls/statistics.
- `negative`: result did not support the tested hypothesis but is still scientifically meaningful.
- `deprecated`: no longer part of the active analysis.

## Rule for the current project

A finding from 5 trials is an exploratory lead, not a final claim. A finding becomes a strong claim only after matched baseline/perturbation trial counts, zero-spike-trial handling, and multiple-comparison correction are documented.
