#!/usr/bin/env python3
"""
Simulator sanity audit helper.

This is a lightweight static/dynamic audit entry point before scaling the final
benchmark. It checks the model reset string and creates a no-input run command
for the user to execute locally. It does not rewrite model.py automatically.

Example:
    python tools/simulator_sanity_audit.py
"""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> None:
    model_path = Path("model.py")
    alt_model_path = Path("model.py")
    if not model_path.exists() and alt_model_path.exists():
        model_path = alt_model_path
    if not model_path.exists():
        raise FileNotFoundError("Could not find model.py in repo root or model.py")

    text = model_path.read_text()
    reset_lines = [line.strip() for line in text.splitlines() if "eq_rst" in line or "v = v_rst" in line]
    print(f"Model file: {model_path}")
    print("Reset-related lines:")
    for line in reset_lines:
        print(f"  {line}")

    if "w = 0" in text:
        print("\nWARNING: reset rule appears to include 'w = 0'.")
        print("Recommended audit: change reset to 'v = v_rst; g = 0 * mV' in a controlled commit, then rerun smoke tests.")
    else:
        print("\nPASS: no obvious 'w = 0' reset artifact detected.")

    print("\nNext local smoke commands:")
    print("  .\\.venv\\Scripts\\python baseline.py --force")
    print("  .\\.venv\\Scripts\\python tools\\create_source_contexts.py")
    print("  .\\.venv\\Scripts\\python tools\\context_reachability_audit.py --context-mode matched_size --n-null 25 --max-steps 4")
    print("\nDo not run large perturbation sweeps until the above commands finish cleanly.")


if __name__ == "__main__":
    main()
