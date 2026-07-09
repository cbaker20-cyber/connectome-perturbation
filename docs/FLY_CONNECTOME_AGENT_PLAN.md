# FLY Connectome Agent Plan

Created from the hourly FLY Connectome work loop.

## Mission

Build a reproducible computational neuroscience project using public *Drosophila* connectome data to generate testable perturbation predictions. The project should be honest enough for serious science: every claim must trace to source data, code, parameters, run logs, and validation.

## Current repo status

The repository is in provenance and reproducibility triage. The next win is not a flashy model; it is a clean end-to-end smoke run that proves the project can go from approved input manifest to schema-valid output.

Current known blockers:

1. Authoritative source manifest is missing for tracked connectome/annotation files.
2. SHA-256 checksums and schemas are not attached to experiments.
3. Scripts refer to `Drosophila_brain_model/` paths while files appear at repo root.
4. The tracked `results/perturbation_summary.csv` has no attached run command, commit, config, random seed, or execution log.
5. Materialization-style 630 and 783 inputs coexist without a selected canonical smoke-run dataset.
6. No tiny fixed-seed smoke run is documented as the safe first reproducible target.

## Work sequence

### Phase 1 — Reproducibility spine

- Inventory existing data files without moving/deleting them.
- Generate `data/input_manifest.json` with filename, size, SHA-256, guessed role, source URL/DOI field, license field, materialization field, and validation status.
- Add `configs/smoke_run.yaml` with fixed seed, tiny runtime, selected materialization, output directory, and maximum resource budget.
- Add path resolver helper so scripts use manifest paths instead of hard-coded `Drosophila_brain_model/`.
- Add smoke-run command that writes an output manifest.

### Phase 2 — Scientific credibility

- Define perturbation types: neuron-class knockout, edge-weight reduction, pathway interruption, hub removal, random matched controls.
- Define metrics before running experiments: reachability, centrality shifts, shortest-path disruption, motor-output proxy changes, connected-component changes, and null-model comparison.
- Add statistical validation: paired random controls, permutation tests, effect sizes, multiple-comparison correction.
- Require every figure/table to include data version, commit, config, and run ID.

### Phase 3 — Research framing

- Convert outputs into hypotheses suitable for lab validation.
- Separate computation-only claims from biological claims.
- Build a Regeneron/ISEF-style evidence chain: background, gap, method, controls, results, limitations, next lab validation.

## Immediate Cursor/Codex prompt

```text
You are working in cbaker20-cyber/connectome-perturbation. Do not make biological claims. First make the repo reproducible.

Tasks:
1. Inspect the repo structure and identify all tracked input-like data files.
2. Create a manifest builder script that records filename, size, sha256, extension, guessed materialization, and missing provenance fields.
3. Add a tiny smoke config with fixed seed and a minimal runtime budget.
4. Reconcile hard-coded Drosophila_brain_model/ paths by adding a path resolver; do not copy large data files.
5. Add a command documented in README that runs the smoke path and writes output_manifest.json.
6. Add tests or validation checks for manifest existence, checksums, path resolution, and output schema.
7. Do not delete existing data/results until a manifest and backup explanation exist.

Definition of done:
- A clean checkout can create the environment, build the input manifest, run one tiny smoke command, and produce schema-valid output with run config, commit, seed, and input checksums recorded.
```

## What Copeland needs to connect or activate

- GitHub is already connected here and the repo is accessible.
- Codex should be connected to the same GitHub account and granted access to `cbaker20-cyber/connectome-perturbation`.
- In Codex, run `/init` in the repo to create or update `AGENTS.md` with project instructions.
- If using Codex cloud tasks, enable ChatGPT ↔ GitHub connection and repository access.
- If using Codex locally, install/use Codex app, CLI, or VS Code/Cursor-compatible IDE extension and sign in with ChatGPT.
- If using browser research workflows, enable Codex in-app browser only if needed; do not enable broad browser/devtools access unless a specific task requires it.
- For stronger recurring automation, connect Google Drive if project notes/literature live there, Gmail only if outreach/lab-contact email is needed, and Slack/Discord only if project coordination is actually happening there.

## Hard rule

No result counts as science until it is reproducible from a clean checkout with a manifest, fixed config, seed, run log, and validation record.
