# 12 Literature and Source Notes

This file tracks external sources and how they support project methods. Use exact paper citations in the final manuscript.

## Core model

**Shiu et al., 2024, Nature — computational Drosophila brain model**  
Supports: whole-brain leaky integrate-and-fire simulation framework based on FlyWire connectivity and neurotransmitter identity; feeding and grooming sensory stimulation framing.

## Connectome

**Dorkenwald et al., 2024, Nature — adult Drosophila brain wiring diagram**  
Supports: adult fly brain connectome scale, approximately 139k neurons and more than 50 million synapses.

## Cell annotations

**Schlegel et al., 2024, Nature — whole-brain annotation and multi-connectome cell typing**  
Supports: hierarchical FlyWire cell annotations such as classes and cell types.

## Neurotransmitter identity/sign

**Eckstein et al., 2024, Cell — neurotransmitter classification from EM images**  
Supports: neurotransmitter identity predictions used to infer excitatory/inhibitory synaptic sign in the model.

## Local project sources

- `source_material/raw_lab_notebook_pasted_text.txt`: original attached journal entries.
- `model.py`: upstream/working model code used here.
- `baseline.py`, `perturb.py`, `cell_groups.py`, `motor_analysis.py`, `statistics.py`, `path_analysis.py`, `analyze_graph_outputs.py`: local project scripts.
