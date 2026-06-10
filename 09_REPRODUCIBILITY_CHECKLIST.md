# 09 Reproducibility Checklist

Use this before submitting a paper, poster, or competition application.

## Environment

- [ ] Operating system recorded.
- [ ] Python version recorded.
- [ ] Brian2 version recorded.
- [ ] `environment.yml` or `environment_full.yml` archived.
- [ ] WSL memory or compute resource documented.
- [ ] Random seed policy documented.

## Data

- [ ] Completeness file version recorded.
- [ ] Connectivity file version recorded.
- [ ] Annotation file version recorded.
- [ ] Annotation overlap recomputed and saved.
- [ ] Motor neuron list saved.
- [ ] Stimulated sensory neuron list saved.
- [ ] Silenced neuron lists saved for every condition.

## Simulation

- [ ] Baseline rerun with accepted trial count.
- [ ] Perturbation reruns use same trial count as baseline.
- [ ] Trial duration recorded.
- [ ] Poisson input rate recorded.
- [ ] `n_proc` setting recorded.
- [ ] Output Parquet files saved and checksummed.

## Statistics

- [ ] Zero-spike trials retained.
- [ ] Per-trial total motor rates saved.
- [ ] Raw p-values saved.
- [ ] FDR q-values saved.
- [ ] Multiple-comparison family defined.
- [ ] Non-significant trends clearly labeled.

## Figures

- [ ] Every figure has a source CSV/Parquet.
- [ ] Every figure has the script used to generate it.
- [ ] Axis labels include units.
- [ ] Exploratory figures are labeled exploratory.
- [ ] Validated figures distinguish q-significant vs non-significant results.

## Narrative

- [ ] Claims in abstract map to `11_CLAIMS_REGISTER.csv`.
- [ ] Methods do not overstate silencing as experimental ablation.
- [ ] LO result is described as revised after validation, not hidden.
- [ ] Negative graph/null results are framed as rigor/control.
