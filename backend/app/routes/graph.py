from fastapi import APIRouter, HTTPException
import logging
import re
from pathlib import Path
from typing import Optional

import networkx as nx
import pandas as pd
from app.graph.graph_builder import build_graph
from app.db import get_session
from neo4j import GraphDatabase

logger = logging.getLogger(__name__)
router = APIRouter()
ROOT = Path(__file__).resolve().parents[2]


def load_processed_data() -> Optional[pd.DataFrame]:
    processed_path = ROOT / "data" / "drugs_processed.csv"
    if processed_path.exists():
        try:
            return pd.read_csv(processed_path)
        except Exception:
            logger.exception("Failed to read processed drugs file")
    return None


def normalize_identifier(value: object) -> str:
    return str(value or "").strip().lower()


def split_aliases(value: str) -> list[str]:
    parts = re.split(r"[;,]", value)
    return [part.strip() for part in parts if part.strip()]


def match_value(val: object, target: str) -> bool:
    if val is None:
        return False
    val_str = normalize_identifier(val)
    if val_str == target:
        return True
    for part in split_aliases(val_str):
        if part == target:
            return True
    return False


def resolve_node(inp: str, G: nx.DiGraph) -> Optional[str]:
    if not inp:
        return None

    lookup = normalize_identifier(inp)
    if lookup == "":
        return None

    # direct node id match, case-insensitive
    for n in G.nodes:
        if normalize_identifier(n) == lookup:
            logger.debug("Resolved input %s to node %s by direct node id", inp, n)
            return n

    id_keys = ["drug_id", "canonical_id", "canonical_name", "drug_name", "generic_name", "name", "brand_names"]
    for n, data in G.nodes(data=True):
        for key in id_keys:
            if match_value(data.get(key), lookup):
                logger.debug("Resolved input %s to node %s via attr %s", inp, n, key)
                return n

    processed = load_processed_data()
    if processed is not None and "canonical_id" in processed.columns:
        match = processed[processed["canonical_id"].astype(str).str.lower() == lookup]
        if not match.empty:
            canonical_name = normalize_identifier(match.iloc[0].get("canonical_name", ""))
            generic_name = normalize_identifier(match.iloc[0].get("generic_name", ""))
            brand_names = normalize_identifier(match.iloc[0].get("brand_names", ""))
            for n, data in G.nodes(data=True):
                if canonical_name and match_value(data.get("drug_name"), canonical_name):
                    logger.debug("Resolved canonical id %s to node %s", inp, n)
                    return n
                if canonical_name and match_value(data.get("canonical_name"), canonical_name):
                    logger.debug("Resolved canonical id %s to node %s", inp, n)
                    return n
                if generic_name and match_value(data.get("generic_name"), generic_name):
                    logger.debug("Resolved canonical id %s to node %s via generic_name", inp, n)
                    return n
                if brand_names and match_value(data.get("brand_names"), brand_names):
                    logger.debug("Resolved canonical id %s to node %s via brand_names", inp, n)
                    return n

    logger.debug("No node resolved for %s", inp)
    return None


def serialize_subgraph(sub: nx.DiGraph):
    nodes_out = []
    for n, data in sub.nodes(data=True):
        nodes_out.append({"id": n, "type": data.get("type"), "attrs": {k: v for k, v in data.items() if k != "type"}})

    edges_out = []
    for u, v, data in sub.edges(data=True):
        edges_out.append({"source": u, "target": v, "relation": data.get("relation")})

    return nodes_out, edges_out


@router.get("/graph/neighborhood/{drug_id}")
def get_neighborhood(drug_id: str, depth: int = 2):
    """Return neighborhood subgraph around a drug limited to `depth` hops (default 2)."""
    # Prefer Neo4j-backed neighborhood queries for performance. Fall back to CSV/networkx builder.
    try:
        session = get_session()
        # Try to find the start node by name (case-insensitive) or by canonical id
        lookup = str(drug_id).strip()
        res = session.run(
            "MATCH (n) WHERE toLower(coalesce(n.name, n.drug_name, '')) = toLower($name) OR toLower(coalesce(n.canonical_id, '')) = toLower($name) RETURN id(n) as nid, n LIMIT 1",
            name=lookup,
        )
        record = res.single()
        if not record:
            raise Exception("neo4j_node_not_found")

        nid = record["nid"]

        # collect paths up to depth hops
        q = """
        MATCH p=(start)-[*1..$depth]-(m)
        WHERE id(start) = $nid
        RETURN p LIMIT 200
        """
        res = session.run(q, nid=nid, depth=depth)

        nodes_map = {}
        edges = []
        for r in res:
            path = r["p"]
            # path.nodes and path.relationships behave like sequences
            for node in path.nodes:
                props = dict(node._properties)
                nid_str = props.get("name") or props.get("drug_name") or props.get("drug_id") or str(node.id)
                if nid_str not in nodes_map:
                    nodes_map[nid_str] = {"id": nid_str, "type": props.get("type") or props.get("_type") or props.get("label"), "attrs": props}
            for rel in path.relationships:
                start_node = rel.start_node
                end_node = rel.end_node
                sprops = dict(start_node._properties)
                eprops = dict(end_node._properties)
                s_id = sprops.get("name") or sprops.get("drug_name") or sprops.get("drug_id") or str(start_node.id)
                e_id = eprops.get("name") or eprops.get("drug_name") or eprops.get("drug_id") or str(end_node.id)
                edges.append({"source": s_id, "target": e_id, "relation": rel.type})

        return {"nodes": list(nodes_map.values()), "edges": edges}
    except Exception:
        logger.exception("Neo4j neighborhood query failed, falling back to file-based graph")
        # fallback to existing networkx CSV-based implementation
        try:
            G = build_graph()
        except Exception as e:
            logger.exception("Failed to load graph: %s", e)
            raise HTTPException(status_code=500, detail={"error": "graph_load_failed"})

        nid = resolve_node(drug_id, G)
        if not nid or (isinstance(nid, str) and nid.startswith("canonical:")):
            raise HTTPException(status_code=404, detail={"error": "drug_not_found"})

        try:
            lengths = nx.single_source_shortest_path_length(G.to_undirected(), nid, cutoff=depth)
            nodes_in = [n for n, l in lengths.items() if l <= depth]
        except Exception:
            nodes_in = [nid]

        sub = G.subgraph(nodes_in).copy()
        nodes_out, edges_out = serialize_subgraph(sub)
        return {"nodes": nodes_out, "edges": edges_out}


@router.get("/graph/{drug1}/{drug2}")
def get_graph(drug1: str, drug2: str):
    logger.debug("Graph request: drug1=%s, drug2=%s", drug1, drug2)
    # FastAPI path parameter routes can collide: /graph/neighborhood/{id} may
    # be captured by this route as drug1='neighborhood'. If that happens,
    # forward the call to the neighborhood handler so the static route is
    # respected and we return the expected response instead of a 404.
    if str(drug1).strip().lower() == "neighborhood":
        return get_neighborhood(drug2)
    # Prefer Neo4j shortest-path queries for pair graphs for performance
    try:
        session = get_session()
        # resolve nodes in Neo4j by name/canonical id
        def resolve_nid(name: str):
            r = session.run(
                "MATCH (n) WHERE toLower(coalesce(n.name, n.drug_name, '')) = toLower($name) OR toLower(coalesce(n.canonical_id, '')) = toLower($name) RETURN id(n) as nid, n LIMIT 1",
                name=str(name).strip(),
            )
            return r.single()

        r1 = resolve_nid(drug1)
        r2 = resolve_nid(drug2)
        if not r1 or not r2:
            logger.info("Drug not directly found in neo4j: drug1_found=%s, drug2_found=%s", bool(r1), bool(r2))
            raise Exception("neo4j_node_resolution_failed")

        nid1 = r1["nid"]
        nid2 = r2["nid"]

        # find shortest path(s) between nodes
        q = """
        MATCH p=shortestPath((a)-[*]-(b))
        WHERE id(a) = $nid1 AND id(b) = $nid2
        RETURN p
        """
        res = session.run(q, nid1=nid1, nid2=nid2)
        records = list(res)
        if not records:
            raise Exception("neo4j_no_path_found")

        nodes_map = {}
        edges = []
        path_count = 0
        for rec in records:
            path = rec["p"]
            path_count += 1
            for node in path.nodes:
                props = dict(node._properties)
                nid_str = props.get("name") or props.get("drug_name") or props.get("drug_id") or str(node.id)
                if nid_str not in nodes_map:
                    nodes_map[nid_str] = {"id": nid_str, "type": props.get("type") or props.get("_type") or props.get("label"), "attrs": props}
            for rel in path.relationships:
                start_node = rel.start_node
                end_node = rel.end_node
                sprops = dict(start_node._properties)
                eprops = dict(end_node._properties)
                s_id = sprops.get("name") or sprops.get("drug_name") or sprops.get("drug_id") or str(start_node.id)
                e_id = eprops.get("name") or eprops.get("drug_name") or eprops.get("drug_id") or str(end_node.id)
                edges.append({"source": s_id, "target": e_id, "relation": rel.type})

        # also include direct neighbors of path nodes for more context
        neighbor_edges = session.run(
            "UNWIND $names AS nm MATCH (n) WHERE toLower(coalesce(n.name,'') ) = toLower(nm) MATCH (n)-[r]-(m) RETURN n, r, m LIMIT 500",
            names=list(nodes_map.keys()),
        )
        for rec in neighbor_edges:
            n = rec["n"]
            m = rec["m"]
            r = rec["r"]
            nprops = dict(n._properties)
            mprops = dict(m._properties)
            n_id = nprops.get("name") or nprops.get("drug_name") or nprops.get("drug_id") or str(n.id)
            m_id = mprops.get("name") or mprops.get("drug_name") or mprops.get("drug_id") or str(m.id)
            if n_id not in nodes_map:
                nodes_map[n_id] = {"id": n_id, "type": nprops.get("type"), "attrs": nprops}
            if m_id not in nodes_map:
                nodes_map[m_id] = {"id": m_id, "type": mprops.get("type"), "attrs": mprops}
            edges.append({"source": n_id, "target": m_id, "relation": r.type})

        return {"nodes": list(nodes_map.values()), "edges": edges, "debug": {"resolved_drug1": drug1, "resolved_drug2": drug2, "path_count": path_count}}
    except HTTPException:
        raise
    except Exception:
        logger.exception("Neo4j pair query failed, falling back to file-based graph")
        # fallback to original implementation
        try:
            G = build_graph()
        except Exception as e:
            logger.exception("Failed to load graph: %s", e)
            raise HTTPException(status_code=500, detail={"error": "graph_load_failed"})

        n1 = resolve_node(drug1, G)
        n2 = resolve_node(drug2, G)

        if not n1 or not n2:
            logger.info("Drug not directly found: drug1_found=%s, drug2_found=%s", bool(n1), bool(n2))
            raise HTTPException(status_code=404, detail={"error": "drug_not_found"})

        undirected = G.to_undirected()
        try:
            has_path = nx.has_path(undirected, n1, n2)
        except nx.NetworkXError:
            has_path = False

        if not has_path:
            raise HTTPException(status_code=404, detail={"error": "no_relationship_found"})

        try:
            paths = list(nx.all_shortest_paths(undirected, source=n1, target=n2))
        except Exception:
            paths = []

        path_nodes = set()
        for p in paths:
            path_nodes.update(p)

        for pn in list(path_nodes):
            path_nodes.update(set(G.predecessors(pn)))
            path_nodes.update(set(G.successors(pn)))

        sub = G.subgraph(list(path_nodes)).copy()
        nodes_out, edges_out = serialize_subgraph(sub)
        debug = {"resolved_drug1": n1, "resolved_drug2": n2, "path_count": len(paths)}

        return {"nodes": nodes_out, "edges": edges_out, "debug": debug}
