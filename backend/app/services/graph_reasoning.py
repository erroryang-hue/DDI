from pathlib import Path
import networkx as nx
from typing import List, Tuple
from app.graph.graph_builder import build_graph


def find_reasoning_paths(drug1: str, drug2: str, max_length: int = 6) -> Tuple[List[str], List[str]]:
    """Return shortest reasoning paths between two drugs and inferred mechanisms.

    Returns (graph_paths, mechanisms)
    """
    G = build_graph()
    graph_paths = []
    mechanisms = set()
    if drug1 not in G or drug2 not in G:
        return graph_paths, []

    try:
        # find k-shortest simple paths by increasing length
        for p in nx.all_simple_paths(G, source=drug1, target=drug2, cutoff=max_length):
            segs = []
            for a, b in zip(p[:-1], p[1:]):
                rel = G.get_edge_data(a, b, {}).get("relation", "INTERACTS_WITH")
                segs.append(f"{a} -> {rel} -> {b}")
                # infer mechanisms from node types and relations
                atype = G.nodes[a].get("type")
                btype = G.nodes[b].get("type")
                # normalized types are: Drug, Enzyme, Pathway, SideEffect, Target, Transporter
                if atype == "Enzyme" or btype == "Enzyme":
                    mechanisms.add("enzyme_interaction")
                if atype == "Pathway" or btype == "Pathway":
                    mechanisms.add("shared_pathway")
                if atype == "SideEffect" or btype == "SideEffect":
                    mechanisms.add("side_effect_overlap")
                if atype == "Transporter" or btype == "Transporter":
                    mechanisms.add("transporter_interaction")
                # relation-based inference
                rlow = str(rel).lower()
                if "inhib" in rlow or "induc" in rlow or "metabol" in rlow:
                    mechanisms.add("enzyme_interaction")
            graph_paths.append("; ".join(segs))
    except Exception:
        return [], []

    return graph_paths, sorted(list(mechanisms))


if __name__ == "__main__":
    print(find_reasoning_paths("DrugA", "DrugB"))
