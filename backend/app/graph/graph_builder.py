from pathlib import Path
import pandas as pd
import networkx as nx


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"


def build_graph():
    """Build a directed knowledge graph from CSV files.

    Returns:
        G (networkx.DiGraph): graph with node attributes
    """
    g = nx.DiGraph()

    # load nodes from CSVs
    csv_map = {
        "drugs": DATA_DIR / "drugs.csv",
        "enzymes": DATA_DIR / "enzymes.csv",
        "targets": DATA_DIR / "targets.csv",
        "pathways": DATA_DIR / "pathways.csv",
        "side_effects": DATA_DIR / "side_effects.csv",
        "transporters": DATA_DIR / "transporters.csv",
    }

    for ntype, path in csv_map.items():
        if not path.exists():
            continue
        df = pd.read_csv(path)
        for _, row in df.iterrows():
            node_id = row.get("drug_id") or row.get("name") or row.get("id")
            if not node_id:
                continue
            attrs = row.to_dict()
            # map csv section to canonical node type
            type_map = {
                "drugs": "Drug",
                "enzymes": "Enzyme",
                "targets": "Target",
                "pathways": "Pathway",
                "side_effects": "SideEffect",
                "transporters": "Transporter",
            }
            attrs["type"] = type_map.get(ntype, ntype)
            g.add_node(str(node_id), **attrs)

    # load edges
    edges_path = DATA_DIR / "graph_edges.csv"
    if edges_path.exists():
        edf = pd.read_csv(edges_path)
        for _, r in edf.iterrows():
            src = str(r["source"])
            tgt = str(r["target"])
            rel = str(r.get("relation", "INTERACTS_WITH"))
            g.add_node(src) if src not in g else None
            g.add_node(tgt) if tgt not in g else None
            g.add_edge(src, tgt, relation=rel)

    return g


if __name__ == "__main__":
    G = build_graph()
    print(f"Graph nodes: {len(G.nodes())}, edges: {len(G.edges())}")
