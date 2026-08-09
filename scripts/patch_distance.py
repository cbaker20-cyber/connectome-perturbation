import re
from pathlib import Path

f = Path("scripts/run_distance_matched_nulls.py")
content = f.read_text(encoding="utf-8")

# replace docstring
content = content.replace("Degree-matched dynamical null test", "Distance-matched dynamical null test")
content = content.replace("weighted-degree\n6: distribution", "shortest-path distance from JO neurons\n6: distribution")
content = content.replace("jo_degree_matched_nulls", "jo_distance_matched_nulls")
content = content.replace("run_degree_matched_nulls", "run_distance_matched_nulls")

# replace compute_weighted_degree
new_funcs = """
import networkx as nx

def compute_shortest_path_distance(edges: pd.DataFrame, jo_ids: list[int], all_ids: np.ndarray) -> pd.Series:
    \"\"\"Shortest path (hop count) from JO sensory nodes to all nodes.\"\"\"
    G = nx.from_pandas_edgelist(edges, source='source', target='target', create_using=nx.DiGraph)
    # Add dummy source node connected to all JO nodes
    G.add_node('JO_SOURCE')
    for jid in jo_ids:
        if jid in G:
            G.add_edge('JO_SOURCE', jid)
            
    lengths = nx.single_source_shortest_path_length(G, 'JO_SOURCE')
    
    # map to series
    dist_map = {}
    for node in all_ids:
        if node == 'JO_SOURCE' or node in jo_ids:
            continue
        dist_map[node] = lengths.get(node, 999) - 1 # -1 because JO_SOURCE to JO is 1
        if dist_map[node] < 0:
            dist_map[node] = 0
    
    dist_series = pd.Series(dist_map)
    dist_series.index = dist_series.index.astype("int64")
    dist_series.name = "distance_bin"
    return dist_series
"""

# Replace the whole chunk from compute_weighted_degree to assign_degree_bins
# We will use regex
import re

content = re.sub(
    r"def compute_weighted_degree\(edges: pd\.DataFrame\) -> pd\.Series:.*?def assign_degree_bins.*?return pd\.Series\(bins\.astype\(int\), index=strengths\.index, name=\"degree_bin\"\)",
    new_funcs.strip(),
    content,
    flags=re.DOTALL
)

# Update main loop
content = content.replace(
    "total_strength = compute_weighted_degree(edges)",
    "pool_ids_full = np.array(sorted(sim_ids))\n    node_distances = compute_shortest_path_distance(edges, jo_ids, pool_ids_full)"
)

content = content.replace(
    "pool_bins = assign_degree_bins(total_strength.reindex(pool_ids).fillna(0), n_bins=n_bins)",
    "pool_bins = node_distances.reindex(pool_ids).fillna(999)"
)

# Update log outputs
content = content.replace("jo_degree_matched_nulls", "jo_distance_matched_nulls")
content = content.replace("Degree bins", "Distance bins")

f.write_text(content, encoding="utf-8")
print("Patched successfully")
