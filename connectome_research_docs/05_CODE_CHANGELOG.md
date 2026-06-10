# 05 Code and Methods Changelog

Use this file for anything that changes how results are produced or interpreted. Every change should explain the scientific consequence, not just the code consequence.

---

## M001 — Local environment and memory configuration

**Date:** 2026-03-20  
**Files/area:** WSL2, Ubuntu, Brian2, GCC  
**Change:** Set up WSL2/Ubuntu environment and increased WSL memory to 12 GB after default memory caused out-of-memory crashes.  
**Scientific consequence:** Enabled stable whole-brain simulations. Memory constraints explain why early trials were run sequentially and why high trial counts have computational cost.

---

## M002 — Sequential execution instead of full parallel execution

**Date:** 2026-03-26  
**Files/area:** `perturb.py`, `baseline.py`, model execution settings  
**Change:** Switched from `n_proc=-1` to `n_proc=1` because parallel execution caused OOM on WSL.  
**Scientific consequence:** Results became stable and reproducible on local hardware, but runtime increased. Trial counts should be planned around compute cost.

---

## M003 — Perturbation wrapper around upstream silencing

**Date:** 2026-03-26  
**Files/area:** `perturb.py`, `baseline.py`, `analyze.py`  
**Change:** Wrapped upstream model silencing so arbitrary groups can be silenced, simulated, and compared against baseline.  
**Scientific consequence:** Created the project’s core experimental capability: systematic in silico causal perturbation.

---

## M004 — FlyWire annotation-based group selection

**Date:** 2026-03-30  
**Files/area:** `cell_groups.py`  
**Change:** Added group lookup by `super_class`, `cell_class`, and `cell_type` using FlyWire annotations.  
**Scientific consequence:** Perturbations became biologically interpretable.

---

## M005 — Exploratory 5-trial screen policy

**Date:** 2026-03-30 to 2026-04-01  
**Files/area:** sweep scripts  
**Change:** Used 5-trial sweeps for speed.  
**Scientific consequence:** Good for candidate discovery but unreliable for final effect signs. This was proven by the LO flip between 5 and 30 trials.

---

## M006 — 30-trial validation policy

**Date:** 2026-04-02  
**Files/area:** high-quality rerun outputs  
**Change:** Reran candidate classes at 30 trials.  
**Scientific consequence:** Upgraded AN result and revised LO interpretation. Established that 30 trials should be the default for paper-quality perturbation claims.

---

## M007 — Matched baseline/perturbation trial counts

**Date:** 2026-04-02  
**Files/area:** statistical analysis  
**Change:** Reran baseline at 30 trials after discovering baseline/perturbation trial-count mismatch.  
**Scientific consequence:** Prevented underpowered or inconsistent comparisons. AN became significant after the baseline issue was corrected.

---

## M008 — Zero-spike trial retention

**Date:** current code state, 2026-06-10 review  
**Files/area:** `statistics.py`, `analyze_graph_outputs.py` optional spike audit  
**Change:** Trial-rate computation now collects trial IDs from the unfiltered spike table and reindexes selected-neuron spike counts so zero-spike trials are retained as 0 Hz.  
**Scientific consequence:** Prevents upward bias in mean firing rates and avoids silently dropping valid trials.

---

## M009 — Welch t-test and Benjamini-Hochberg FDR

**Date:** current code state, 2026-06-10 review  
**Files/area:** `statistics.py`  
**Change:** Current code uses Welch’s t-test for baseline vs perturbation total motor firing and then applies Benjamini-Hochberg FDR correction.  
**Scientific consequence:** Stronger inference and reviewer-proof multiple-comparison handling.

---

## M010 — Graph null-model / pathway analysis split

**Date:** current code state, 2026-06-10 review  
**Files/area:** `path_analysis.py`, `analyze_graph_outputs.py`  
**Change:** Added task-specific source-to-target pathway analysis and degree-matched null logic.  
**Scientific consequence:** Prevents overclaiming global graph centrality. Supports a more mature story: perturbation effects are functional and may depend on task-specific pathways rather than whole-brain centrality alone.
