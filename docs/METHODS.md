# Methods (code-backed)

If this file disagrees with `model.py` or `perturbation/statistics.py`, the
code wins. Update this file after a methods change; do not “fix” the code to
match a narrative.

## Network

- Implementation: Brian2 2.5.1, `prefs.codegen.target = 'numpy'`
- Neurons: rows of the completeness table (630 unless a run says 783)
- Synapses: rows of the connectivity parquet; `on_pre='g += w'`
- Equations: `dv/dt = (v_0 - v + g) / t_mbr`, `dg/dt = -g / tau`
- Default trial: 1000 ms. `model.py` default `n_run` is 30;
  `perturbation/baseline.py` currently sets `n_run = 5`. **Always write the
  trial count of the actual run.**

## Lesion

Outgoing weights of the target set → 0. Incoming synapses unchanged. Call this
**output silencing**, not ablation.

## Readout

Neurons with `super_class == "motor"` in the annotation table, restricted to
IDs present in the completeness table. Per-trial total firing rate in Hz.
Trials with zero motor spikes are **kept as 0 Hz**.

## Statistics (minimum for a claim)

1. Matched baseline vs lesion trial counts
2. Zero-spike trials retained
3. Trial count stated
4. Welch two-sample t-test (`equal_var=False`)
5. Benjamini–Hochberg FDR across the family of tests in that batch
6. Exploratory screens labeled as screens

## Polarity grouping

`perturbation/cell_groups.py` assigns excitatory / inhibitory / unmapped
under a **named** map. Default for new work is `classical_fast` (ACh
excitatory, GABA inhibitory, glutamate unmapped). `shiu_2024` additionally
treats glutamate as inhibitory. Both maps must be reported if polarity is
part of the claim.

## Sensory contexts currently wired

- Sugar: 21 right-side sugar-responsive IDs in `perturbation/baseline.py`
- None: empty excitation list (tests H2, silent inhibition)
- JO / other contexts: only if a config file lists exact root IDs for that run
