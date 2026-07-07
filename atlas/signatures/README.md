# Vulnerability Signatures

This folder stores context-by-target vulnerability matrices.

Minimum target format:

```text
rows = contexts such as sugar, odor, touch, vision
columns = neuron IDs or edge IDs
values = vulnerability scores
```

Rules:

- IDs must be strings.
- Every matrix must link to the perturbation runs that created it.
- Every context must define input and output neuron groups.
- Similarity analyses must report the metric used.
