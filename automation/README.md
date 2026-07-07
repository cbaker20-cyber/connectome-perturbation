# FLY Automation

This folder contains the local automation plan for running FLY as a controlled research forge.

## Recommended stack

```text
GitHub Issues = task queue
Local Windows PC = worker
9Router = model/provider routing endpoint
OpenCode/Codex/Cline = coding agent
GitHub PRs = output
GitHub Actions = judge
Atlas = research memory
```

## Why local?

9Router runs on your machine and exposes an OpenAI-compatible local endpoint. A cloud workflow cannot automatically reach your local router. Use the PC as the worker and GitHub as the safety boundary.

## Safety rule

The local forge must never push directly to `main`.

It should:

1. pull latest repo;
2. pick one issue;
3. create a branch;
4. run the agent;
5. run tests;
6. commit;
7. push;
8. open a PR;
9. record evidence.

## Files

- `setup_9router_windows.ps1`: installs/starts 9Router.
- `fly_forge_loop.py`: skeleton scheduler loop for local agent execution.
- `fly_forge_config.example.json`: configuration template.
- `github_labels.txt`: recommended labels to create through GitHub CLI.
