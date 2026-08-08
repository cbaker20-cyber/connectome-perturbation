import sys
from pathlib import Path
import pandas as pd

# Add the parent directory to the path so we can import from connectome_analysis
sys.path.append(str(Path(__file__).parent.parent))

from connectome_analysis.an_betweenness import (
    resolve_analysis_path,
    load_annotations,
    load_unsigned_edges,
    build_digraph,
    select_ids,
    compute_strength_metrics,
    compute_source_target_betweenness,
    run_degree_matched_fdr_control,
    DEFAULT_SUGAR_IDS
)

def run_group_betweenness(
    group_name: str,
    focus_ids: set[int],
    graph,
    annotations: pd.DataFrame,
    sources: list[int],
    targets: list[int],
    n_permutations: int = 200,
    seed: int = 7,
    null_pool_super_class: str = "central",
    alpha: float = 0.05,
    metrics=None,
    betweenness=None,
):
    print(f"Running control for {group_name} (N={len(focus_ids)} nodes in graph)...")
    if not focus_ids:
        print(f"Skipping {group_name}: no valid focus ids.")
        return None

    null_ids = {n for n in select_ids(annotations, super_class=null_pool_super_class) if n in graph}
    
    control = run_degree_matched_fdr_control(
        metrics,
        focus_ids=focus_ids,
        null_pool_ids=null_ids,
        n_permutations=n_permutations,
        seed=seed,
        alpha=alpha,
    )
    
    if not control.empty:
        control["focus_group"] = group_name
        control.insert(1, "n_sources", len(sources))
        control.insert(2, "n_targets", len(targets))
        control.insert(3, "n_focus_in_graph", len(focus_ids))
        
    return control

def main():
    connectivity_id = "2023_03_23_connectivity_630_final.parquet"
    annotations_id = "flywire_annotations.tsv"
    manifest_path = "data/input_manifest.json"
    
    con_path = resolve_analysis_path(connectivity_id, manifest_path=manifest_path)
    ann_path = resolve_analysis_path(annotations_id, manifest_path=manifest_path)
    
    print("Loading data...")
    annotations = load_annotations(ann_path)
    edges = load_unsigned_edges(con_path)
    graph = build_digraph(edges)
    
    sources = list(DEFAULT_SUGAR_IDS)
    targets = sorted(select_ids(annotations, super_class="motor"))
    sources_in_graph = [int(n) for n in sources if n in graph]
    targets_in_graph = [int(n) for n in targets if n in graph]
    
    print("Computing baseline metrics...")
    betweenness = compute_source_target_betweenness(
        graph, sources_in_graph, targets_in_graph, weight="distance", normalized=True
    )
    metrics = compute_strength_metrics(graph)
    metrics["source_target_betweenness"] = metrics["neuron_id"].map(betweenness).fillna(0.0)

    groups_to_test = {
        "Descending": {n for n in select_ids(annotations, super_class="descending") if n in graph},
        "LO": {n for n in select_ids(annotations, cell_class="LO") if n in graph},
        "Kenyon_Cell": {n for n in select_ids(annotations, cell_class="Kenyon_Cell") if n in graph},
        "Motor": {n for n in select_ids(annotations, super_class="motor") if n in graph},
    }

    all_results = []
    for group_name, focus_ids in groups_to_test.items():
        res = run_group_betweenness(
            group_name,
            focus_ids,
            graph,
            annotations,
            sources_in_graph,
            targets_in_graph,
            metrics=metrics,
            betweenness=betweenness
        )
        if res is not None and not res.empty:
            all_results.append(res)
            
    if all_results:
        final_df = pd.concat(all_results, ignore_index=True)
        out_path = Path("results/other_groups_betweenness_control.csv")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        final_df.to_csv(out_path, index=False)
        print(f"\nSaved all results to {out_path}")
        
        cols = [
            c for c in [
                "focus_group", "metric", "statistic", "actual_value",
                "null_mean", "z_score", "q_two_sided_bh", "significant_two_sided_bh"
            ] if c in final_df.columns
        ]
        print("\nSummary:")
        print(final_df[cols].to_string(index=False))

if __name__ == "__main__":
    main()
