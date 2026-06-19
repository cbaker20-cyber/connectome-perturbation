# Connectome Perturbation Cursor Task Queue

Work from top to bottom. Open one PR per task. Do not push directly to main. Do not invent research progress. Use sourced notes and small, testable changes only.

## Current goal

Catalog and stabilize the fly connectome perturbation project so future coding/research work is reproducible.

## Operating rules

- Read README.md, docs/cursor-ready-issues.md, and the repository tree before editing.
- Make one branch and one draft PR per task.
- Do not push directly to main.
- Do not commit large datasets unless they are already tracked intentionally.
- Do not commit secrets, tokens, notebooks with private outputs, generated caches, or environment folders.
- Do not make neuroscience claims without citations in docs.
- Prefer documentation, reproducibility, and tests before adding features.
- If a dataset or paper is missing, document the blocker instead of guessing.

## Task 1: Repository inventory and progress log

Goal: create a project status document that honestly catalogs what exists.

Acceptance criteria:
- Create docs/progress-log.md.
- List repository files/directories at a high level.
- Identify current entry points, scripts, notebooks, data files, and missing documentation.
- Record known goal, current assumptions, blockers, and next actions.
- Do not change code behavior.

## Task 2: README project overview

Goal: improve README.md so a future agent/human knows what the project is.

Acceptance criteria:
- Add a concise project summary.
- Add setup/run instructions if they can be inferred safely.
- Add a section for data sources and cite or mark missing sources.
- Add a section for safety/reproducibility notes.
- Do not claim results that are not present.

## Task 3: Data handling audit

Goal: prevent accidental large/private data misuse.

Acceptance criteria:
- Inspect tracked data-like files and file sizes.
- Add or improve .gitignore for caches, environments, outputs, and large derived data.
- Create docs/data-policy.md explaining what should and should not be committed.
- Do not delete data unless clearly generated and unnecessary; if unsure, document it.

## Task 4: Reproducible environment plan

Goal: make the project easier to run later.

Acceptance criteria:
- Identify language/runtime and dependencies from existing files.
- If no dependency file exists, propose one in docs/environment-plan.md instead of guessing.
- If dependency files exist, document setup commands.
- Do not install or pin random dependencies without evidence.

## Task 5: First minimal tests or validation checks

Goal: add a small validation layer appropriate to the current codebase.

Acceptance criteria:
- If Python scripts exist, add minimal tests for importability or simple pure functions.
- If notebooks/data only, add docs/validation-plan.md instead.
- Do not require external large datasets for tests.

## Hard rules

- No fabricated progress.
- No unsupported biological/neuroscience claims.
- No secrets or private data.
- No large generated files.
- Stop and explain if blocked.
