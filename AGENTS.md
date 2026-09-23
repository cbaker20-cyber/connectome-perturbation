# Working rules for this repository

Comments should explain why a decision was made, a non-obvious constraint, or a failure someone needs to avoid. Do not narrate obvious syntax or restate the line below the comment. Never invent a rationale, ticket, reference, or development history to make a comment sound convincing. Keep longer explanations of research code in the separate code guide and lab notebook.

Match the surrounding code's naming and structure. Use short conventional names for simple indices and mathematical quantities, and descriptive names where they clarify meaning. Avoid unnecessarily verbose names, boilerplate and abstractions. Do not add arbitrary stylistic quirks or inconsistencies to imitate human authorship. Keep assistance attribution accurate.

Choose algorithms for the actual dataset and workload. Consider time complexity, memory use, repeated reads, output volume and concurrency before scaling a run. Prefer a suitable lookup or indexed operation over an avoidable quadratic scan. Measure uncertain performance claims rather than assuming that working on a toy example establishes scalability.

Verify library functions and signatures against the installed version or authoritative documentation. Do not invent APIs or assume that a plausible method exists. Keep environment and dependency records consistent with what actually ran.

Review relevant failure cases, including empty or missing inputs, unexpected types, duplicate identifiers, neuron-ID precision, partial outputs, interrupted runs, conflicting workers and corrupted files. Use meaningful known-answer and failure tests where correctness matters. A passing happy-path example is not enough to establish research validity.

Handle anticipated failures explicitly and include enough context to diagnose them. Do not swallow errors, leave empty exception handlers, or report success after a failed step. Catch specific exceptions where possible; broad catches are appropriate for necessary cleanup or recording failure when the error is then propagated. Protect sensitive information in logs.

Close files and release resources reliably. Clean up only locks and processes owned by the current operation, preserve evidence from failed research runs, and make restart behavior explicit. Do not remove another worker's lock or silently overwrite a frozen result.

Judge code by correctness, evidence, maintainability and suitability for the research question. Comment style, naming consistency and polished syntax do not establish who wrote code or whether its results are valid.
