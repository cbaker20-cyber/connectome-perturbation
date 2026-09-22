"""Archive implementation/notes and hash every final pilot artifact for review."""
import argparse
from pathlib import Path
import zipfile

from .common import ROOT, atomic_json, now, provenance, sha256


def freeze(pilot):
    pilot = Path(pilot).resolve()
    prov = provenance()
    extra = [ROOT/"tests/test_pcdr.py", ROOT/"scripts/pcdr_array.sh", ROOT/"scripts/run_degree_matched_nulls.py"]
    extra += sorted((ROOT/"docs/pcdr").glob("*"))
    archive = pilot/"implementation_and_notes.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for path in [*(ROOT/p for p in prov["sources"]), *extra]:
            if path.is_file():
                z.write(path, arcname=path.relative_to(ROOT).as_posix())
    outputs = {p.relative_to(pilot).as_posix(): sha256(p) for p in sorted(pilot.rglob("*"))
               if p.is_file() and p.name != "research_record.json" and not p.name.endswith(".tmp")}
    atomic_json(pilot/"research_record.json", {"created_utc": now(), "provenance": prov,
                "artifacts": outputs, "archive_sha256": sha256(archive),
                "note": "Final review snapshot; individual trial archives record code at each trial's start."})


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--pilot", required=True)
    freeze(p.parse_args().pilot)
