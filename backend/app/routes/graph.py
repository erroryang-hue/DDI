from fastapi import APIRouter, HTTPException
import logging
from app.graph.graph_builder import build_graph
from app.services import interaction_engine
import pandas as pd

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/graph/{drug1}/{drug2}")
def get_graph(drug1: str, drug2: str):
    logger.debug("Graph request: drug1=%s, drug2=%s", drug1, drug2)
    try:
        G = build_graph()
    except Exception as e:
        logger.exception("Failed to load graph: %s", e)
        raise HTTPException(status_code=500, detail={"error": "graph_load_failed"})

    # helper to resolve input to node id used in graph
    def resolve_node(inp: str):
        if inp in G:
            logger.debug("Direct node match for %s", inp)
            return inp
        # try matching by attribute 'drug_id' or 'name'
        for n, data in G.nodes(data=True):
            if str(data.get("drug_id", "")).lower() == inp.lower() or str(data.get("name", "")).lower() == inp.lower():
                logger.debug("Resolved input %s to node %s via attrs", inp, n)
                return n
        logger.debug("No node resolved for %s", inp)
        return None

    n1 = resolve_node(drug1)
    n2 = resolve_node(drug2)

    # If either drug not found, return standardized JSON
    if not n1 or not n2:
        logger.info("Drug not found: drug1_found=%s, drug2_found=%s", bool(n1), bool(n2))
        raise HTTPException(status_code=404, detail={"error": "drug_not_found"})

    logger.debug("Node existence: %s -> %s ; %s -> %s", drug1, n1 in G, drug2, n2 in G)

    # check for path existence
    try:
        import networkx as nx

        has_path = nx.has_path(G, n1, n2)
    except Exception:
        has_path = False

    logger.debug("Path existence between %s and %s: %s", n1, n2, has_path)
    if not has_path:
        # still may want to return neighborhood, but per spec return error
        raise HTTPException(status_code=404, detail={"error": "no_relationship_found"})

    # find relevant nodes: include nodes along shortest path(s)
    try:
        paths = list(nx.all_shortest_paths(G, source=n1, target=n2))
    except Exception:
        paths = []

    path_nodes = set()
    for p in paths:
        path_nodes.update(p)

    # include direct neighbors of path nodes for context
    for pn in list(path_nodes):
        path_nodes.update(set(G.predecessors(pn)))
        path_nodes.update(set(G.successors(pn)))

    sub = G.subgraph(list(path_nodes)).copy()

    # serialize nodes and edges
    nodes_out = []
    for n, data in sub.nodes(data=True):
        nodes_out.append({"id": n, "type": data.get("type"), "attrs": {k: v for k, v in data.items() if k != "type"}})

    edges_out = []
    for u, v, data in sub.edges(data=True):
        edges_out.append({"source": u, "target": v, "relation": data.get("relation")})

    debug = {"resolved_drug1": n1, "resolved_drug2": n2, "path_count": len(paths)}

    return {"nodes": nodes_out, "edges": edges_out, "debug": debug}


@router.get("/graph/neighborhood/{drug_id}")
def get_neighborhood(drug_id: str, depth: int = 2):
    """Return neighborhood subgraph around a drug limited to `depth` hops (default 2)."""
    try:
        G = build_graph()
    except Exception as e:
        logger.exception("Failed to load graph: %s", e)
        raise HTTPException(status_code=500, detail={"error": "graph_load_failed"})

    # resolve node
    def resolve_node(inp: str):
        if inp in G:
            return inp
        for n, data in G.nodes(data=True):
            if str(data.get("drug_id", "")).lower() == inp.lower() or str(data.get("name", "")).lower() == inp.lower():
                return n
        return None

    nid = resolve_node(drug_id)
    if not nid:
        raise HTTPException(status_code=404, detail={"error": "drug_not_found"})

    try:
        import networkx as nx

        lengths = nx.single_source_shortest_path_length(G.to_undirected(), nid, cutoff=depth)
        nodes_in = [n for n, l in lengths.items() if l <= depth]
    except Exception:
        nodes_in = [nid]

    sub = G.subgraph(nodes_in).copy()

    nodes_out = []
    for n, data in sub.nodes(data=True):
        nodes_out.append({"id": n, "type": data.get("type"), "attrs": {k: v for k, v in data.items() if k != "type"}})

    edges_out = []
    for u, v, data in sub.edges(data=True):
        edges_out.append({"source": u, "target": v, "relation": data.get("relation")})

    return {"nodes": nodes_out, "edges": edges_out}
