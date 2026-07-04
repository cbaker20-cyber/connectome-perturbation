# GitHub Student Pack and Automation Review

## Goal

Use free or student-accessible tooling to reduce the slow parts of a serious computational-neuroscience project: reproducibility checks, run documentation, safe sharing, and lightweight review.

The goal is not to throw every tool at the project. The goal is to automate the boring failure modes before they waste weeks.

## Highest-value automation for this repository

1. GitHub Actions safety gates
   - Check for unsafe FlyWire/root-ID parsing.
   - Block generated outputs, caches, virtual environments, secrets, and unapproved large data.
   - Validate the living research documentation files.

2. Pull request and issue templates
   - Force each analysis change to state what changed, what evidence exists, and whether a claim is preliminary or validated.
   - Keep Lab Notebook Update Sync tied to code and data-analysis changes.

3. Run manifest templates
   - Make every interpretable result record inputs, checksums, command, commit, environment, random seed, trial count, output paths, and validation checks.

4. GitHub Pages later
   - Host a clean professor-facing project summary.
   - Do not publish raw data, private notes, or unapproved results.

5. Codespaces or devcontainer later
   - Give the project a reproducible browser-based environment for documentation checks and small smoke tests.
   - Do not expect Codespaces to run the full connectome model unless data access and compute limits are solved.

## Student Pack tools worth using

### GitHub Actions

Use immediately. This is the backbone of the automation pack.

### GitHub Pages

Use after the professor-facing summary is cleaned. This can become a public-facing page with the cautious result, technical correction, limitations, and next steps.

### Codespaces

Useful for reproducible editing and lightweight checks. It should not be the first place to run heavy Brian2 simulations.

### Camber or other scientific-compute credits

Potentially useful for heavier reruns later. Do not upload raw or license-unclear data until provenance and permissions are documented.

### Deepnote

Useful for small notebook summaries and sanitized figures. Good for sharing views of results without asking someone to run the whole repo.

### JetBrains / VS Code tools / GitLens / GitKraken

Useful for local development, branch review, and tracing which commit produced which result.

### CodeScene or code-quality tools

Useful once the repository has stable workflows. Not the first priority.

### Secrets tools such as Doppler or 1Password

Useful only if the project starts using APIs or cloud credentials. For now, the best secret policy is simpler: do not commit secrets at all.

## What not to automate yet

- Full Brian2 production runs in GitHub Actions.
- Uploading raw FlyWire-derived data to external cloud tools.
- Automatic biological interpretation.
- Automatic professor emails.

The project still needs human judgment for biological claims.

## Practical sequence

1. Merge the safety workflows and templates.
2. Pull the branch locally.
3. Run the dependency-free checks.
4. Fix any policy failures.
5. Add one clean high-trial rerun manifest.
6. Only then build a public-facing GitHub Pages summary.
