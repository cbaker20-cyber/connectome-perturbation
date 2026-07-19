# Reproducibility audit notes

Last updated: 2026-07-18

This note records a conservative audit of remaining reproducibility gaps. It does not certify scientific validity.

## Resolved in recent PRs

- Connectome inputs resolve through `tools/path_resolver.py` and `data/input_manifest.json`.
- Materialization **630** is documented as the canonical smoke/default target (`docs/materialization-policy.md`).
- Smoke config `selected_inputs` are validated against resolver filenames and the input manifest (`tools/validate_reproducibility.py --smoke-config`).
- Output manifests bind `run_config` (seed, materialization, selected inputs), `environment`, and `repo_commit` when outputs are declared; CI runs the full smoke artifact → output manifest → validate sequence.
- Research documentation pack validated in CI: experiment ↔ claim ↔ result cross-references, duplicate ID detection, resolvable evidence paths (`tools/validate_research_docs.py`).

## Remaining hard-coded paths (accepted or pending)

| Location | Issue | Severity |
|---|---|---|
| `perturbation/statistics.py`, `motor_analysis.py`, `visualize.py` | Hard-coded `results/` output directory | medium — document per-run `path_res` when rerunning |
| `example.ipynb`, `figures.ipynb` | Inline `./2023_03_23_*` paths | medium — not yet routed through resolver |
| `perturbation/visualize.py` | `sys.path.insert(0, "perturbation")` only | low — no data-path assumption |
| `tools/path_resolver.py` | Legacy `Drosophila_brain_model/` fallback | low — intentional backwards compatibility |

## Undocumented assumptions

- `flywire_annotations.tsv` is treated as shared across 630 and 783 checkouts; release mapping is not verified.
- `baseline.py` uses 5 trials while `model.py` defaults to 30; outputs must state actual trial counts.
- Annotation overlap counts in project docs are historical notebook values, not bound to current manifest checksums.

## Missing provenance checks

- `results/perturbation_summary.csv` is not tied to input checksums, config, or commit.
- Toy graph artifact sequence is not yet wired into CI (metadata smoke path only).

## Next highest-value improvements

1. Bind experiment registry entries to output manifests and commit hash.
2. Enforce `docs_config.yaml` `minimum_claim_standard` against experiment rows.
3. Migrate notebooks to manifest-resolved paths or document explicit materialization per notebook cell.
