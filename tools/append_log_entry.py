#!/usr/bin/env python3
"""Append a timestamped skeleton entry to 01_LIVING_RESEARCH_LOG.md."""
from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

TEMPLATE = """
---

## Entry {entry_id} — {title}

**Date:** {date}  
**Status:** {status}  
**Type:** {entry_type}

### Goal


### Files changed

| File | Change | Why it matters |
|---|---|---|
| | | |

### Data / parameters

- Completeness file:
- Connectivity file:
- Annotation file:
- Stimulus neurons:
- Perturbation target:
- Target/readout neurons:
- Trial count:
- Trial duration:
- Random seed:
- Script/command:
- Git commit hash:

### Results


### Interpretation


### Caveats


### Next action


"""

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("entry_id", help="Example: 009")
    parser.add_argument("title")
    parser.add_argument("--status", default="planned")
    parser.add_argument("--type", default="analysis", dest="entry_type")
    parser.add_argument("--log", default="01_LIVING_RESEARCH_LOG.md")
    args = parser.parse_args()

    log_path = Path(args.log)
    text = TEMPLATE.format(
        entry_id=args.entry_id,
        title=args.title,
        date=date.today().isoformat(),
        status=args.status,
        entry_type=args.entry_type,
    )
    with log_path.open("a", encoding="utf-8") as f:
        f.write(text)
    print(f"Appended entry {args.entry_id} to {log_path}")

if __name__ == "__main__":
    main()
