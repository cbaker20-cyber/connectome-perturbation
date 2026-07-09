# Claim ledger

This ledger keeps the FLY connectome project honest by separating repository facts, scientific assumptions, hypotheses, and future work. It is intentionally conservative: a statement should not move into the `verified` category unless it is backed by a reproducible artifact, source citation, or validator output.

## Labels

| Label | Meaning | Evidence required before use in reports |
| --- | --- | --- |
| `verified` | Directly supported by a repository artifact, validator output, source document, or reproduced command. | File path, commit, command, manifest checksum, source URL/DOI, or test result. |
| `assumption` | A working interpretation that may be reasonable but is not yet proven for this repo/dataset. | Must name what would falsify or confirm it. |
| `hypothesis` | A testable scientific or engineering claim planned for experiment. | Must have a proposed metric, control, and expected direction. |
| `future_work` | A useful idea that is not implemented or validated yet. | Must not be worded as completed work. |
| `blocked` | A claim or task that cannot advance without a missing artifact, permission, citation, or dataset fact. | Must name the missing item exactly. |

## Current project claims

| Claim | Label | Evidence / blocker | Next action |
| --- | --- | --- | --- |
| The current reproducibility PR is metadata-first and does not validate biological conclusions. | `verified` | PR #17 description and `claim_status: not_interpretable_as_neuroscience` contract in `tools/write_output_manifest.py` / `tools/validate_reproducibility.py`. | Keep this sentence in README/project summaries until a real experiment is reproduced. |
| Input-like files can be represented in `data/input_manifest.json` with SHA-256 and size metadata. | `verified` | `tools/build_input_manifest.py` and validator requirements. | Run locally/CI and review generated manifest. |
| Output manifests should be checked against the input manifest, config file, and declared output artifacts. | `verified` | `tools/validate_reproducibility.py` validates config checksum, input manifest reference, input checksums, and optional declared outputs. | Keep adding regression tests whenever a new manifest field is introduced. |
| Existing historical result CSVs are interpretable as scientific evidence. | `blocked` | `TASKS.md` notes existing results are not tied to command, config, seed, commit, or input checksums. | Do not cite these results as evidence until they are regenerated under a validated manifest. |
| Materialization 630 is the correct canonical smoke target. | `assumption` | `TASKS.md` lists materialization choice as undecided. | Document source, schema, reason for 630 vs 783, and expected row counts. |
| The project can identify robust perturbation effects in the fly connectome. | `hypothesis` | Requires defined perturbation classes, metrics, null controls, and multiple-comparison plan. | Write experiment design before running or presenting results. |
| A judge/mentor-facing status page can safely explain the project without overclaiming. | `future_work` | No status page exists yet. | Use this ledger to write a conservative summary after provenance is filled. |

## Promotion rules

Before moving a claim to `verified`, add at least one of:

1. A command that can be rerun from a clean checkout.
2. A manifest path with matching SHA-256 / size facts.
3. A test name or CI check that passed.
4. A source citation with access date, license/terms, and dataset release/materialization.
5. A committed notebook/script plus exact config and seed.

## Report-writing guardrail

Avoid these phrases until the relevant claim is verified:

- "shows that"
- "proves"
- "the connectome demonstrates"
- "biologically significant"
- "causes"
- "validated model"

Safer alternatives:

- "metadata plumbing is in place for..."
- "this run is not yet biologically interpretable"
- "the next experiment will test whether..."
- "under this planned metric/control design..."
