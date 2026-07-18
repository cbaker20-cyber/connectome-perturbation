# 00 Project State

Last updated: 2026-07-18

## One-sentence project summary

This project extends a whole-adult-Drosophila leaky integrate-and-fire brain model by adding systematic cell-group silencing, cell-type annotation, motor-output analysis, statistical validation, and graph/pathway controls to test which neuron classes causally influence feeding- and grooming-related motor activity.

## Current strongest scientific story

The strongest validated direction is not “visual lobula disinhibition is the headline.” That was an important exploratory lead, but it changed after 30-trial validation. The stronger story is:

> Whole-brain connectome perturbation can identify functional control layers in a biologically grounded fly brain simulation. In the feeding/sugar-input condition, sensory, central, descending, AN/antennal, and ascending groups show robust motor-output effects, while disinhibition appears as a recurring circuit motif. The project’s methodological value is that silencing and rigorous controls reveal effects that activation-only simulations or low-trial screens can misclassify.

## Current validated / near-validated claims

| Claim ID | Claim | Current status | Why it matters |
|---|---|---|---|
| C001 | The perturbation engine can silence arbitrary neuron groups and compare downstream firing against a baseline. | validated-in-code | This is the project’s core technical contribution. |
| C002 | FlyWire annotations were joined to modeled neurons with 106,216 overlapping cells, about 83.4% of the 127,400-neuron simulation. | documented | This gives biological meaning to perturbation targets. |
| C003 | Descending neuron silencing reduces most motor output but disinhibits a subset of motor neurons. | validated as phenomenon; details need rerun table | Shows mixed excitatory/suppressive control. |
| C004 | Sensory, central, descending, AN, and ascending perturbations show significant motor-output effects in the current statistical notebook/log. | validated in notebook; must preserve exact statistics file | Strongest current result set. |
| C005 | Low-trial screens can produce wrong sign interpretations: LO was +21.0 Hz at 5 trials but -34.4 Hz at 30 trials. | validated methodological lesson | This is a major rigor point for judges/reviewers. |
| C006 | Zero-spike trials must be retained as 0 Hz in trial-level statistics. | implemented in code | Prevents biased trial-rate estimates. |
| C007 | Graph/pathway analyses should use degree-matched nulls and task-specific source-to-target metrics rather than only global centrality. | active analysis track | Prevents overclaiming topology results. |

## Active caveats

1. Five-trial sweeps are exploratory only.
2. Current silencing sets all outgoing weights from targeted neurons to zero. This models output silencing/axon removal, not a fully biophysical hyperpolarization or synaptic plasticity process.
3. Annotation counts can differ between FlyWire/Schlegel releases and local files. Record exact annotation file version and row count for every analysis.
4. Some current files use different default trial counts: `model.py` defaults to 30 trials, while `baseline.py` currently sets `PARAMS["n_run"] = 5`. Documentation and scripts must state the actual run parameters for each output.
5. A negative graph/null result is not a failed project; it is evidence that the correct functional question may be pathway/task-specific rather than global centrality-based.

## Immediate next updates to make in the repo

- ~~Add this `docs/` folder to the GitHub repo.~~ (done)
- Commit `data/input_manifest.json` with SHA-256 checksums for tracked connectome inputs. (done; authoritative provenance fields still missing)
- Route all perturbation analysis scripts through `tools/path_resolver.py` instead of hard-coded `Drosophila_brain_model/` paths. (done; legacy subdirectory fallback retained)
- Document materialization 630 vs 783, resolver selection rules, and expected input manifests in `docs/materialization-policy.md`. (done; 630 is canonical smoke target)
- Validate `configs/smoke_run.yaml` against resolver filenames and the input manifest in CI. (done via `tools/validate_reproducibility.py --smoke-config`)
- Save exact `results/statistics.csv`, `results/motor_impact.csv`, and any graph null outputs into a versioned `results_manifest.csv`.
- Add commit hashes to experiment registry entries after each code run.
- Create a `config/experiment_configs/` folder so every run has a frozen YAML config.
- Fill source-backed provenance fields in `data/input_manifest.json` before any biological claim.
