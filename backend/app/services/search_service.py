from typing import Dict, List
from app.graph.graph_builder import build_graph


def _resolve_node(G, inp: str):
    if inp in G:
        return inp
    for n, data in G.nodes(data=True):
        if str(data.get("drug_id", "")).lower() == inp.lower() or str(data.get("name", "")).lower() == inp.lower():
            return n
    return None


def search_drug(drug: str) -> Dict[str, List[Dict]]:
    G = build_graph()
    nid = _resolve_node(G, drug)
    if not nid:
        return {}

    neighbors = list(G.neighbors(nid)) + list(G.predecessors(nid))
    # dedupe
    neighbors = list(dict.fromkeys(neighbors))

    grouped = {}
    nodes = []
    edges = []
    # include the central node
    data = G.nodes[nid]
    nodes.append({"id": nid, "type": data.get("type"), "attrs": {k: v for k, v in data.items() if k != "type"}})

    for nb in neighbors:
        nd = G.nodes[nb]
        nodes.append({"id": nb, "type": nd.get("type"), "attrs": {k: v for k, v in nd.items() if k != "type"}})
        # edges between nid and neighbor
        if G.has_edge(nid, nb):
            edges.append({"source": nid, "target": nb, "relation": G.get_edge_data(nid, nb).get("relation")})
        if G.has_edge(nb, nid):
            edges.append({"source": nb, "target": nid, "relation": G.get_edge_data(nb, nid).get("relation")})

    # group nodes by type
    for n in nodes:
        t = n.get("type") or "Unknown"
        grouped.setdefault(t, []).append(n)

    return {"center": nid, "groups": grouped, "nodes": nodes, "edges": edges}
