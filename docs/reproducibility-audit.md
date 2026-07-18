# Reproducibility audit notes

Last updated: 2026-07-18

This note records a conservative audit of remaining reproducibility gaps. It does not certify scientific validity.

## Resolved in recent PRs

- Connectome inputs resolve through `tools/path_resolver.py` and `data/input_manifest.json`.
- Materialization **630** is documented as the canonical smoke/default target (`docs/materialization-policy.md`).
- Smoke config `selected_inputs` are validated against resolver filenames and the input manifest (`tools/validate_reproducibility.py --smoke-config`).

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

- `--require-provenance` is not enabled in CI because authoritative source fields are still empty.
- No output manifest is required in CI yet (`--skip-output-manifest`); full smoke artifact sequence remains manual.
- `results/perturbation_summary.csv` is not tied to input checksums, config, or commit.

## Next highest-value improvements

1. Fill authoritative provenance in `data/input_manifest.json`.
2. Run and commit validated output manifests for the metadata smoke artifact sequence.
3. Migrate notebooks to manifest-resolved paths or document explicit materialization per notebook cell.
