# AGENTS.md

Rules for AI agents and human contributors working on this repository.

## Prime directive

Make the project reproducible before making biological claims. This repository is currently in provenance and reproducibility triage.

## Hard rules

- Do not delete tracked data or results unless a human explicitly approves it in a reviewed PR.
- Do not add secrets, tokens, credentials, private notes, or undisclosed datasets.
- Do not claim neuroscience conclusions from existing outputs until the exact input manifest, command, config, seed, commit, environment, and validation record are attached.
- Prefer small, reviewable PRs.
- Preserve existing exploratory work unless replacing it with a clearly simpler, tested path.
- Record important assumptions, blockers, and decisions in repository files, not only in chat.

## Current engineering priorities

1. Build and validate an input manifest for existing input-like files.
2. Remove hard-coded `Drosophila_brain_model/` assumptions by routing paths through one resolver.
3. Add a fixed-seed, tiny smoke path that writes `output_manifest.json`.
4. Add validation checks for manifests, checksums, paths, and output schema.
5. Only then attempt larger simulations or claims.

## Benchmark comparison reports

Quantitative benchmark comparison reports live in `data/benchmark_registry.yaml` with thresholds in `configs/benchmark_evaluation.yaml`.

- Run `python tools/report_benchmark_comparison.py --fail-on-regression` to write `benchmark_comparison_report.json`.
- Each benchmark reports expected vs observed metrics, absolute/relative error, thresholds, and reproducibility status.
- CI generates smoke/toy artifacts and validates comparison reports on every pull request.
- See `docs/benchmark_comparison_reports.md`.

## Scientific standards

Every interpretable run should eventually include:

- input manifest with SHA-256 checksums;
- dataset names, materializations, source URLs/DOIs, licenses, and access dates;
- configuration and random seed;
- command used;
- Git commit;
- environment file or lockfile;
- runtime metadata;
- output manifest;
- validation result.

Separate verified facts, assumptions, hypotheses, and future ideas.

## Safe automation behavior

When blocked, document the blocker and pivot to another reproducibility or documentation task. Do not fabricate missing provenance.