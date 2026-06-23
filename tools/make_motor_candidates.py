from pathlib import Path

import pandas as pd


def main() -> None:
    Path("metadata").mkdir(exist_ok=True)

    ann_path = Path("flywire_annotations.tsv")
    if not ann_path.exists():
        raise FileNotFoundError("Could not find flywire_annotations.tsv in the repository root.")

    ann = pd.read_csv(ann_path, sep="\t", low_memory=False)
    if "super_class" not in ann.columns or "root_id" not in ann.columns:
        raise ValueError("Expected flywire_annotations.tsv to contain root_id and super_class columns.")

    candidate_cols = [
        "root_id",
        "super_class",
        "cell_class",
        "cell_type",
        "hemibrain_type",
        "ito_lee_hemilineage",
        "hartenstein_hemilineage",
        "top_nt",
        "side",
        "nerve",
        "flow",
        "status",
        "synonyms",
    ]
    cols = [c for c in candidate_cols if c in ann.columns]

    motor = ann[ann["super_class"].astype(str).str.lower().eq("motor")].copy()
    motor_out = motor[cols].drop_duplicates("root_id")
    motor_out.to_csv("metadata/all_motor_annotation_candidates.csv", index=False)

    text_cols = [c for c in cols if c != "root_id"]
    text = motor[text_cols].astype(str).agg(" ".join, axis=1).str.lower()

    feeding_pat = r"feed|feeding|probosc|pharyn|cibari|labell|ingest|mouth|sugar|taste"
    grooming_pat = r"groom|grooming|leg|tars|brush|clean|wing|eye|bristle"

    feeding_hits = motor.loc[text.str.contains(feeding_pat, regex=True, na=False), cols].drop_duplicates("root_id")
    grooming_hits = motor.loc[text.str.contains(grooming_pat, regex=True, na=False), cols].drop_duplicates("root_id")

    feeding_hits.to_csv("metadata/feeding_motor_annotation_hits.csv", index=False)
    grooming_hits.to_csv("metadata/grooming_motor_annotation_hits.csv", index=False)

    print("All motor candidates:", motor_out["root_id"].nunique())
    print("Feeding text hits:", len(feeding_hits))
    print("Grooming text hits:", len(grooming_hits))
    print("Wrote:")
    print("  metadata/all_motor_annotation_candidates.csv")
    print("  metadata/feeding_motor_annotation_hits.csv")
    print("  metadata/grooming_motor_annotation_hits.csv")


if __name__ == "__main__":
    main()
