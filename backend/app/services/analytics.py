from pathlib import Path
import pandas as pd
from collections import Counter
from app.graph.graph_builder import build_graph
from app.services.drug_meta import load_drug_catalog

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"


def _normalize_type(raw: str | None) -> str | None:
    if not raw:
        return None
    r = str(raw).lower()
    if r in ("drugs", "drug", "drug_id"):
        return "Drug"
    if r in ("enzymes", "enzyme"):
        return "Enzyme"
    if r in ("pathways", "pathway"):
        return "Pathway"
    if r in ("side_effects", "sideeffect", "side-effects", "side_effect"):
        return "SideEffect"
    if r in ("targets", "target"):
        return "Target"
    if r in ("transporters", "transporter"):
        return "Transporter"
    return None


def _count_rows(csv_path: Path) -> int:
    if not csv_path.exists():
        return 0
    try:
        df = pd.read_csv(csv_path)
        return len(df)
    except Exception:
        return 0


def top_entities(n: int = 5):
    """Return top connected entities and totals filtered by node type.

    Returns the structure requested by the API consumer with totals and
    top-N lists restricted to the appropriate node 'type'.
    """
    # totals: use the combined drug catalog so analytics reflect all discovered drug sources
    df = load_drug_catalog()
    total_drugs = df['drug_name'].nunique() if not df.empty and 'drug_name' in df.columns else 0

    # retain existing fallback behavior for the other entity counts
    repo_root = ROOT
    synth_count = 0
    cur = repo_root
    for _ in range(4):
        for candidate in cur.glob("synthetic_*_with_half_life.csv"):
            synth_count += _count_rows(candidate)
        cur = cur.parent

    # leave these as file-based counts for now, since analytics still uses CSV-backed entity sets
    total_enzymes = _count_rows(DATA_DIR / "enzymes.csv")
    total_pathways = _count_rows(DATA_DIR / "pathways.csv")
    total_side_effects = _count_rows(DATA_DIR / "side_effects.csv")

    # build graph and compute degree only among nodes of matching normalized type
    G = build_graph()

    # collect degree lists by normalized type
    deg_by_type: dict[str, list[tuple[str, int]]] = {
        "Drug": [],
        "Enzyme": [],
        "Pathway": [],
        "SideEffect": [],
        "Target": [],
        "Transporter": [],
    }

    for node, data in G.nodes(data=True):
        ntype = _normalize_type(data.get("type"))
        if ntype:
            deg_by_type.setdefault(ntype, []).append((node, G.degree(node)))

    def top_from_list(lst: list[tuple[str, int]]) -> list[str]:
        return [node for node, _ in sorted(lst, key=lambda kv: kv[1], reverse=True)[:n]]

    top_drugs = top_from_list(deg_by_type.get("Drug", []))
    top_enzymes = top_from_list(deg_by_type.get("Enzyme", []))
    top_pathways = top_from_list(deg_by_type.get("Pathway", []))
    top_side_effects = top_from_list(deg_by_type.get("SideEffect", []))

    # if CSVs were not present, fall back to counting nodes of that type in graph
    if total_drugs == 0:
        total_drugs = len(deg_by_type.get("Drug", []))
    if total_enzymes == 0:
        total_enzymes = len(deg_by_type.get("Enzyme", []))
    if total_pathways == 0:
        total_pathways = len(deg_by_type.get("Pathway", []))
    if total_side_effects == 0:
        total_side_effects = len(deg_by_type.get("SideEffect", []))

    return {
        "total_drugs": total_drugs,
        "total_enzymes": total_enzymes,
        "total_pathways": total_pathways,
        "total_side_effects": total_side_effects,
        "top_drugs": top_drugs,
        "top_enzymes": top_enzymes,
        "top_pathways": top_pathways,
        "top_side_effects": top_side_effects,
    }
