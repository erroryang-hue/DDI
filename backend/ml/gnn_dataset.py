from pathlib import Path

import pandas as pd
import torch
from torch_geometric.data import Data

ROOT_DIR = Path(__file__).resolve().parents[1]
GRAPH_CSV_PATH = ROOT_DIR / "data" / "graph_edges.csv"
DRUGS_PROCESSED = ROOT_DIR / "data" / "drugs_processed.parquet"
DRUGS_PROCESSED_CSV = ROOT_DIR / "data" / "drugs_processed.csv"


def _parse_edges(df):
    edges = []
    edge_types = []
    rel_map = {}
    rel_counter = 0
    for _, r in df.iterrows():
        src = r["source"]
        dst = r["target"]
        rel = r.get("relation", "related_to")
        
        # Skip if source or target is NaN or None
        if pd.isna(src) or pd.isna(dst) or src is None or dst is None:
            continue
        
        # Convert to string to ensure valid node names
        src = str(src).strip()
        dst = str(dst).strip()
        
        if not src or not dst:
            continue
            
        if rel not in rel_map:
            rel_map[rel] = rel_counter
            rel_counter += 1
        edges.append((src, dst))
        edge_types.append(rel_map[rel])
    return edges, edge_types, rel_map


def build_graph():
    df = pd.read_csv(GRAPH_CSV_PATH)

    # parse existing edges
    edges, edge_types, rel_map = _parse_edges(df)

    # load processed drugs if available to add node features and extra edges
    drugs_lookup = {}
    if DRUGS_PROCESSED.exists():
        ddf = pd.read_parquet(DRUGS_PROCESSED)
    elif DRUGS_PROCESSED_CSV.exists():
        ddf = pd.read_csv(DRUGS_PROCESSED_CSV)
        for _, r in ddf.iterrows():
            name = r.get("canonical_name")
            if pd.isna(name):
                continue
            drugs_lookup[name] = {
                "id": r.get("canonical_id"),
                "half_life": float(r.get("half_life") or 0.0),
                "targets": set(r.get("targets_list") or []),
                "enzymes": set(r.get("enzymes_list") or []),
                "transporters": set(r.get("transporters_list") or []),
                "pathways": set(r.get("pathways_list") or []),
                "side_effects": set(r.get("side_effects_list") or []),
                "target_count": int(r.get("target_count") or 0),
                "enzyme_count": int(r.get("enzyme_count") or 0),
                "transporter_count": int(r.get("transporter_count") or 0),
                "pathway_count": int(r.get("pathway_count") or 0),
                "side_effect_count": int(r.get("side_effect_count") or 0),
            }

    # build nodes as union of all node names seen
    node_names = set()
    for s, t in edges:
        # Already filtered in _parse_edges, but ensure strings
        s = str(s).strip() if s is not None else None
        t = str(t).strip() if t is not None else None
        if s and t:
            node_names.add(s)
            node_names.add(t)

    # also add enzyme/target/pathway nodes from drugs lookup
    for dname, meta in drugs_lookup.items():
        dname = str(dname).strip() if dname else None
        if dname:
            node_names.add(dname)
        for entity_list in [meta.get("enzymes", []), meta.get("targets", []), 
                            meta.get("pathways", []), meta.get("side_effects", [])]:
            for entity in entity_list:
                entity = str(entity).strip() if entity else None
                if entity and entity != "nan":
                    node_names.add(entity)

    # convert all node names to strings and sort
    nodes = sorted([n for n in node_names if n and n != "nan"])
    node_map = {node: idx for idx, node in enumerate(nodes)}

    # add explicit drug->entity edges from drugs lookup
    for dname, meta in drugs_lookup.items():
        for enz in meta.get("enzymes", []):
            edges.append((dname, enz))
            edge_types.append(rel_map.setdefault("metabolized_by", len(rel_map)))
        for tgt in meta.get("targets", []):
            edges.append((dname, tgt))
            edge_types.append(rel_map.setdefault("binds_to", len(rel_map)))
        for pw in meta.get("pathways", []):
            edges.append((dname, pw))
            edge_types.append(rel_map.setdefault("participates_in", len(rel_map)))
        for se in meta.get("side_effects", []):
            edges.append((dname, se))
            edge_types.append(rel_map.setdefault("causes", len(rel_map)))

    # Filter edges and edge_types to only include valid node pairs
    valid_edges = []
    valid_edge_types = []
    for (src, dst), etype in zip(edges, edge_types):
        if src in node_map and dst in node_map:
            valid_edges.append([node_map[src], node_map[dst]])
            valid_edge_types.append(etype)
    
    edge_index = torch.tensor(valid_edges, dtype=torch.long).t().contiguous() if valid_edges else torch.zeros((2, 0), dtype=torch.long)

    edge_attr = torch.tensor(valid_edge_types, dtype=torch.long) if valid_edge_types else None

    # Node features: for drug nodes use counts + half_life; else use small one-hot type features
    x_list = []
    for n in nodes:
        meta = drugs_lookup.get(n)
        if meta:
            feats = [
                float(meta.get("enzyme_count", 0)),
                float(meta.get("target_count", 0)),
                float(meta.get("pathway_count", 0)),
                float(meta.get("transporter_count", 0)),
                float(meta.get("side_effect_count", 0)),
                float(meta.get("half_life", 0.0)),
            ]
        else:
            # non-drug node: simple one-hot type buckets (enzyme,target,pathway,side_effect,other)
            if n in (df.get("source").tolist() + df.get("target").tolist()):
                # attempt to infer type from presence in original CSV
                # default to zeros + small value
                feats = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
            else:
                feats = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        x_list.append(feats)

    x = torch.tensor(x_list, dtype=torch.float)

    data = Data(x=x, edge_index=edge_index)
    if edge_attr is not None:
        data.edge_attr = edge_attr

    return data, node_map