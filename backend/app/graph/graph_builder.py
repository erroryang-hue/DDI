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
            # allow optional generated drugs file for drugs list
            if ntype == "drugs":
                gen_path = DATA_DIR / "drugs_generated.csv"
                if not gen_path.exists():
                    continue
                df = pd.read_csv(gen_path)
            else:
                continue
        else:
            df = pd.read_csv(path)

        # if drugs, include generated drugs as well
        if ntype == "drugs":
            gen_path = DATA_DIR / "drugs_generated.csv"
            if gen_path.exists():
                try:
                    df_gen = pd.read_csv(gen_path)
                    df = pd.concat([df, df_gen], ignore_index=True)
                    # prefer explicit drug_name and drop duplicates
                    if "drug_name" in df.columns:
                        df = df.drop_duplicates(subset=["drug_name"])
                except Exception:
                    pass
            # also append any workspace-root synthetic files (50/500 etc.)
            cur = ROOT
            for _ in range(4):
                for candidate in cur.glob("synthetic_*_with_half_life.csv"):
                    try:
                        df_synth = pd.read_csv(candidate)
                        df = pd.concat([df, df_synth], ignore_index=True)
                        if "drug_name" in df.columns:
                            df = df.drop_duplicates(subset=["drug_name"])
                    except Exception:
                        continue
                cur = cur.parent

        for _, row in df.iterrows():
            # For drugs.csv, use drug_name; for others use id or name
            if ntype == "drugs":
                node_id = row.get("drug_name")
            else:
                node_id = row.get("id") or row.get("name")
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

    # add nodes from processed drug lookup to support canonical IDs
    processed_path = DATA_DIR / "drugs_processed.csv"
    if processed_path.exists():
        try:
            pdf = pd.read_csv(processed_path)
            for _, row in pdf.iterrows():
                canonical_name = row.get("canonical_name")
                if not canonical_name or str(canonical_name).strip() == "":
                    continue
                node_id = str(canonical_name)
                if node_id not in g:
                    attrs = row.to_dict()
                    attrs["type"] = "Drug"
                    g.add_node(node_id, **attrs)
        except Exception:
            pass

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
