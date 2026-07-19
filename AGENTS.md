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

## Input provenance

Authoritative dataset metadata lives in `data/input_provenance_registry.yaml` and is merged into `data/input_manifest.json` by `tools/build_input_manifest.py`.

- Every tracked connectome input should have `validation_status: provenance_complete` before biological claims.
- CI runs `python tools/validate_reproducibility.py --require-provenance` on the committed input manifest.
- Update the YAML registry (not hand-edited JSON) when releases, licenses, URLs/DOIs, or row counts change; then regenerate the manifest.

## Current engineering priorities

1. Build and validate an input manifest for existing input-like files.
2. Remove hard-coded `Drosophila_brain_model/` assumptions by routing paths through one resolver.
3. Add a fixed-seed, tiny smoke path that writes `output_manifest.json`.
4. Add validation checks for manifests, checksums, paths, and output schema.
5. Only then attempt larger simulations or claims.

## Output manifest binding

When an output manifest declares produced artifacts (`outputs` non-empty):

- `tools/write_output_manifest.py` must copy `run_config` from the referenced YAML config (seed, materialization, selected inputs).
- Record `repo_commit`, `environment`, and input manifest checksums at write time.
- Record `experiment_id` and `experiment_registry_path` when the run config or `--experiment-id` supplies them.
- `tools/validate_reproducibility.py` enforces run-config binding when outputs exist; use `--require-experiment-binding` for registry cross-checks in CI.
- Metadata-only manifests with empty `outputs` may skip strict run-config binding.

## Research documentation pack

The canonical research specification lives at the **repository root** (`03_EXPERIMENT_REGISTRY.csv`, `11_CLAIMS_REGISTER.csv`, `09_REPRODUCIBILITY_CHECKLIST.md`, etc.). See `docs/research_document_mapping.md` for the full mapping.

- Run `python tools/validate_research_docs.py` before claiming registry/ledger/claims consistency.
- CI validates the research documentation pack on every pull request.
- Prefer editing root-level research files; `connectome_research_docs/` is a legacy mirror.

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