# Connectome materialization policy

This document records how the repository distinguishes FlyWire-style materialization **630** and **783** inputs, which dataset bundle is used for reproducibility smoke work, and how `tools/path_resolver.py` selects files. It is a reproducibility contract only; it does not certify that any local file is authoritative, complete, or biologically valid.

## Verified local inventory

The committed `data/input_manifest.json` records byte checksums for five connectome-like inputs:

| Materialization | Role | Tracked path |
|---|---|---|
| 630 | completeness table | `2023_03_23_completeness_630_final.csv` |
| 630 | connectivity table | `2023_03_23_connectivity_630_final.parquet` |
| 783 | completeness table | `Completeness_783.csv` |
| 783 | connectivity table | `Connectivity_783.parquet` |
| shared | annotation table | `flywire_annotations.tsv` |

Both materializations are present in the checkout. They are **not interchangeable**: switching materialization changes neuron counts, edge tables, and downstream overlap with annotations.

## Canonical smoke target: materialization 630

**Decision:** use materialization **630** for metadata-first smoke runs and as the default script target until a reviewed 783 rerun is explicitly requested.

**Why 630 (repository evidence, not a biological claim):**

1. `perturbation/baseline.py`, `perturbation/perturb.py`, and `test_run.py` default to the `2023_03_23_*_630_final` filenames.
2. `perturbation/graph_analysis.py` and `perturbation/path_analysis.py` default to `2023_03_23_connectivity_630_final.parquet`.
3. `perturbation/cell_groups.py` joins `flywire_annotations.tsv` against the 630 completeness table.
4. `configs/smoke_run.yaml` now records `selected_materialization: "630"` with explicit input filenames.

Materialization **783** remains available for future comparison runs but is not the default smoke bundle. A 783 experiment requires an explicit config change and a fresh output manifest; do not assume annotation overlap or script defaults transfer unchanged.

## How the path resolver chooses datasets

`tools/path_resolver.py` is the single entry point for connectome input paths.

### Lookup order

For a caller-supplied identifier (manifest path, filename, legacy `Drosophila_brain_model/<file>`, role, or materialization token):

1. **Normalize** legacy prefixes (`Drosophila_brain_model/foo.parquet` → `foo.parquet`).
2. **Manifest match** against `data/input_manifest.json` using, in order:
   - the original identifier
   - the normalized identifier
   - the basename (`Path(identifier).name`)
3. **Direct repo-relative file** if the path exists under the repository root.
4. **Legacy subdirectory fallback** at `Drosophila_brain_model/<basename>` for older checkouts.

Every resolved path must stay inside the repository root.

### Ambiguity is rejected

If more than one manifest row matches the same identifier, the resolver raises `ValueError` instead of picking a file silently. This matters because the manifest currently contains:

- two `connectivity_table` rows (630 and 783)
- two `completeness_table` rows (630 and 783)
- two rows whose `guessed_materialization` is `630` or `783`

Therefore:

| Identifier type | Safe? | Notes |
|---|---|---|
| Exact filename, e.g. `2023_03_23_connectivity_630_final.parquet` | yes | Preferred for scripts and smoke configs |
| Legacy prefixed filename | yes | Prefix is stripped before lookup |
| `connectivity_table` or `completeness_table` | **no** | Ambiguous across materializations |
| `630` or `783` alone | **no** | Multiple rows share each materialization token |

Use `resolve_materialization_inputs("630")` or explicit filenames when you need the whole bundle.

### Materialization helper

```python
from tools.path_resolver import resolve_materialization_inputs

paths = resolve_materialization_inputs("630")
# paths["completeness"], paths["connectivity"], paths["annotations"]
```

Constants live in `tools/path_resolver.py`:

- `SMOKE_MATERIALIZATION = "630"`
- `MATERIALIZATION_FILENAMES`
- `ANNOTATIONS_INPUT = "flywire_annotations.tsv"`

## Expected input manifest

Smoke and perturbation tooling expect `data/input_manifest.json` with:

### Top-level fields

- `schema_version`
- `generated_at_utc` (timezone-aware ISO-8601)
- `input_count` equal to `len(inputs)`
- `inputs` list

### Per-input fields

Required by `tools/validate_reproducibility.py`:

- `path`, `filename`, `extension`, `size_bytes`, `sha256`
- `guessed_role`, `provenance` object with all required provenance keys
- optional `guessed_materialization` when inferable from the filename

Regenerate checksums with:

```bash
python tools/build_input_manifest.py
python tools/validate_reproducibility.py \
  --input-manifest data/input_manifest.json \
  --skip-output-manifest
```

Claim-ready runs additionally require non-empty provenance via `--require-provenance`. Maintain authoritative values in `data/input_provenance_registry.yaml` and regenerate with `python tools/build_input_manifest.py`.

Validate smoke config alignment with:

```bash
python tools/validate_reproducibility.py \
  --input-manifest data/input_manifest.json \
  --smoke-config configs/smoke_run.yaml \
  --skip-output-manifest
```

Remaining audit notes live in `docs/reproducibility-audit.md`.

## Switching to materialization 783

To run against 783 without changing resolver code:

1. Pass explicit filenames to script CLIs, or call `resolve_materialization_inputs("783")`.
2. Update the run config (`selected_materialization`, `selected_inputs`) and regenerate the output manifest.
3. Recompute annotation overlap and rerun baseline/perturbation outputs; do not merge 630 and 783 result tables.

## Open blockers

- `flywire_annotations.tsv` is shared across materializations in this checkout; its exact release mapping to 783 tables is not verified here.
- Notebooks (`example.ipynb`, `figures.ipynb`) still embed inline paths and should be updated separately.
