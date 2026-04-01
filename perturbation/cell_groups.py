import pandas as pd

ANN_PATH = "flywire_annotations.tsv"
SIM_PATH = "Drosophila_brain_model/2023_03_23_completeness_630_final.csv"

def load_annotated_sim_neurons():
    ann = pd.read_csv(ANN_PATH, sep="	", low_memory=False)
    sim = pd.read_csv(SIM_PATH, index_col=0)
    sim_ids = set(sim.index.values)
    ann = ann[ann["root_id"].isin(sim_ids)]
    return ann

def get_group(cell_class=None, super_class=None, cell_type=None):
    ann = load_annotated_sim_neurons()
    mask = pd.Series([True] * len(ann), index=ann.index)
    if cell_class:
        mask &= ann["cell_class"] == cell_class
    if super_class:
        mask &= ann["super_class"] == super_class
    if cell_type:
        mask &= ann["cell_type"] == cell_type
    return ann.loc[mask, "root_id"].tolist()

def list_groups(by="super_class"):
    ann = load_annotated_sim_neurons()
    return ann.groupby(by)["root_id"].count().sort_values(ascending=False)

if __name__ == "__main__":
    print(list_groups("super_class"))
    print()
    motor = get_group(super_class="motor")
    print(f"Motor neurons in sim: {len(motor)}")
    descending = get_group(super_class="descending")
    print(f"Descending neurons in sim: {len(descending)}")
