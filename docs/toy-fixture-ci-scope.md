# Toy fixture CI scope

The deterministic toy graph artifact is synthetic test infrastructure. It is included in the reproducibility workflow so regressions in exact string identifiers, deterministic JSON output, graph metrics, and repository-boundary-safe output handling are detected by GitHub Actions.

Passing these checks does not validate FlyWire data, neuron identity, lesion effects, biological interpretation, or any neuroscience conclusion. The fixture exists only to prove that the repository's graph/provenance plumbing behaves as specified on known synthetic inputs.
