# Minimum claim standard enforcement

Last updated: 2026-07-19

This document describes how `docs_config.yaml` `minimum_claim_standard` is enforced against the experiment registry and results ledger. It validates research metadata only and does not change scientific methods.

## Source of truth

`docs_config.yaml`:

```yaml
minimum_claim_standard:
  require_matched_trial_counts: true
  require_zero_spike_trial_retention: true
  require_fdr_correction: true
  exploratory_trial_count_label: "5-trial screen"
  preferred_validation_trials: 30
```

## Enforcement tool

`tools/validate_research_docs.py` validates:

| Check | Rule |
|---|---|
| Trial counts | Exploratory experiments must not record ≥30 trials; validated experiments must record ≥30 matched trials |
| Claim tier | Status labels map to `exploratory`, `validated`, `infrastructure`, or `non_trial` |
| Exploratory vs validated | Exploratory rows referencing validated claims must document an exploratory caveat |
| Statistical requirements | Validated statistical experiments must document FDR correction |
| Zero-spike retention | Validated perturbation experiments must document zero-spike trial retention |
| Registry consistency | Results ledger statuses must align with parent experiment tier; raw p-values require FDR q-values or an FDR caveat |
| Benchmark tier (optional) | When `data/benchmark_registry.yaml` exists, experiment tier must match linked benchmark `claim_tier` |

## Usage

```bash
python tools/validate_research_docs.py
python tools/validate_research_docs.py --skip-minimum-claim-standard
```

CI runs the strict path on every pull request.

## Backwards compatibility

Legacy fixtures may pass `--skip-minimum-claim-standard` to retain basic registry checks without tier enforcement.
