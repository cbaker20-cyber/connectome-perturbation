# Connectome-Perturbation: Project History

## Executive Summary

The Connectome-Perturbation project aims to investigate the **dynamic leverage of long-range projection neurons** within the *Drosophila* connectome. By programmatically perturbing sensory and central pathways across varying contexts, the project reconstructs how these long-range projections (such as Ascending Neurons, or ANs) govern motor output. Grounded in the FlyWire v630 dataset, the repository has evolved from an initial proof-of-concept perturbation engine into a hardened, highly reproducible scientific framework capable of executing context-conditional sweeps (e.g., Sugar vs. Johnston's Organ) and analyzing outcomes through rigorous graph-mathematical surrogates (BORA, DVI, path attenuation).

This document serves as the historical record of the repository’s evolution, from early heuristic scripting to the strict, AI-agent-assisted pipeline present in `main` as of August 2026.

---

## Phase 1: Proof-of-Concept and The Perturbation Engine
**Key Period:** Initial Project Start (Commits `0f15f67` – `41a87f4`)

The repository began as a localized suite of scripts to test the hypothesis that specific cell classes could dramatically shift motor outcomes.

* **The Engine (`0f15f67`):** The first perturbation engine successfully ran baseline comparisons and generated results summaries.
* **Early Discoveries (`afd4a75`, `5faa89f`, `66a2603`):** 
  * Confirmed the descending-to-motor circuit functionality (`afd4a75`).
  * A full super-class perturbation sweep (`a759812`) identified significant disinhibition motifs originating in the Lobula (LO).
  * High-quality 30-trial reruns (`66a2603`) later refined the LO result and solidified a critical finding: **Ascending Neurons (ANs) exert significant dynamic leverage**, a result that proved robust to statistical testing (`41a87f4`).

---

## Phase 2: Reproducibility Hardening and Claim Hygiene
**Key Period:** Infrastructure Overhaul (Commits `0e87572` – `5ad0b61`)

As the scientific claims grew more complex, the repository faced data realities: manipulating the massive FlyWire v630 graph introduced risks of silent data corruption, non-deterministic behaviors, and cross-platform hash mismatches (e.g., line-ending/SHA-256 issues).

* **Metadata-First Reproducibility Spine (`0e87572`):** Implemented strict tracking of environment and graph states.
* **Deterministic Contracts & Lesion Scoring (`311f9e9`, `ff2af41`, `424298f`):** Built deterministic synthetic baselines, node/connection lesion scoring contracts, and vulnerability signature matrices to guarantee mathematically identical outputs across runs.
* **Targeted Validation Receipts (`e983d07`, `9bc5952`):** Instituted a "fail-closed" validation schema. Any structural claim had to produce a deterministic targeted validation receipt (`9bc5952`) mathematically tied to declared artifact bytes (`e98bd02`).
* **Input Manifests (`5ad0b61`):** Committed strict input manifests with checksums for all tracked connectome files to resolve SHA-256/line-ending mismatch issues.
* **Operational Protocol (`1766867`):** Documented requirements for independent receipt reverification to ensure any Regeneron STS reviewer or external auditor could trust the computational provenance.

---

## Phase 3: Mathematical Modules and Network Surrogates
**Branch:** `feat/issue-57-58-math-surrogates` (Commits `178e4bc`, `9c96e5c`, `b4e6ad1`)

To explain *why* ANs and other projections possessed such leverage, the project introduced formal graph-theoretic mathematical models.

* **Graph Math Surrogates (`178e4bc`):** Introduced analytical surrogates bypassing raw simulation costs, focusing on **modal controllability**, **path attenuation**, and the **BORA** (Behavioral Opponent Routing Analysis) framework.
* **Disinhibition Motifs & AN Betweenness (`9c96e5c`):** Added specific search tools to isolate disinhibition motifs, deploying path-betweenness centrality controls tailored for Ascending Neurons.
* **Ground-Truth Sweeps (`b4e6ad1`):** Added a Johnston's Organ (JO) 30-trial ground-truth sweep runner to serve as a baseline for the surrogate metrics.

---

## Phase 4: Contextual Perturbation and The BORA Framework
**Branch:** `sts-bora-framework-20260623` (Commits `79f4dff` – `d09d844`)

The core scientific claim matured into testing *context dependency*: does the brain's vulnerability to AN perturbation shift depending on what the fly is doing? 

* **Context Definitions (`31811f7`, `76fba41`, `79f4dff`):** Curated specific feeding (Sugar) and grooming target templates for BORA, mapping distinct behavioral states to FlyWire source IDs.
* **Data Realities - 64-bit ID Parsing (`566ae2b`, `c384a93`):** Addressed a critical infrastructure bug by implementing safe parsing patches for large 64-bit FlyWire IDs in source contexts, preventing overflow and precision-loss errors.
* **Dynamic Vulnerability Index (DVI) (`d672e6b`):** Shipped the DVI module comparing Sugar vs. JO motor context shifts, actively mapping how structural vulnerability changes when the stimulus context changes.
* **Correlation Harness (`f5ed148`):** Developed a Spearman/Pearson correlation harness (`f5ed148`) and instant structural surrogate benchmark (`46fa39d`) to prove the math models aligned with the heavy simulation ground-truth (CEO-071B, `7e135f8`).
* **Pipeline Hardening (`da3040c`):** Resolved deep `Bugbot` findings, completing the migration of the `path_resolver` and fixing edge cases in baseline resolution and degree binning.

---

## Phase 5: Branch Cleanup and August 2026 Consolidation
**Key Period:** Final Integration (Commits `e36130b` – `1c7d0a0`)

After parallel development across multiple agent-assisted feature branches, the work was unified into `main`.

* **Merge and Audit (`d09d844`):** The BORA framework and mathematical surrogate branches were successfully merged into `main`.
* **AI Scaffolding Removal (`0686359`, `1c7d0a0`):** Executed a final infrastructure cleanup campaign, removing residual AI scaffolding, temporary remote tracking branches, and intermediate scratch files, leaving a clean, publication-ready repository.

---

## Current Status & Open Work

As of August 2026, the repository stands as a hardened, reproducible pipeline ready for rigorous peer review. 

### What is Finished
* **Core Pipeline:** The graph perturbation engine, synthetic structural baselines, and deterministic validation protocols are complete and fail-closed.
* **Math Modules:** BORA, path attenuation, modal controllability, and DVI modules are fully integrated.
* **Context Sweeps:** The Sugar and JO comparative contexts have been mapped, swept, and correlated via the surrogate vs. ground-truth harness.
* **Hygiene:** Strict 64-bit ID parsing, checksum verification, and byte-level provenance are enforced.

### Open Work (Future Directions)
* **Expanded Contexts:** Applying the BORA framework to additional sensory contexts (e.g., visual or olfactory paradigms) beyond Sugar and JO.
* **Downstream Motor Mapping:** Further mapping of the specific motor neuron pool responses (e.g., flight vs. walking) affected by the dynamic leverage of Ascending Neurons.
* **Performance Optimization:** While the instant structural surrogate bypasses heavy simulation, running exhaustive non-surrogate 30-trial simulations across all cell classes remains computationally intensive and could benefit from future parallelization or cluster deployment tuning.
