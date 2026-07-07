from typing import List, Dict
from pathlib import Path
import re
import pandas as pd
from app.services.drug_meta import load_drug_catalog, _find_drug_rows
from app.services.interaction_engine import score_interaction

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"


def _parse(cell):
    if pd.isna(cell) or cell is None:
        return []
    return [s.strip() for s in re.split(r"[;,]", str(cell)) if s.strip()]


def _jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 0.0
    inter = len(a & b)
    uni = len(a | b)
    return inter / uni if uni > 0 else 0.0


def find_alternatives(drug_id: str, top_k: int = 5) -> List[Dict]:
    """Find alternative drugs similar by ATC class, targets, and pathways.

    Exclude the same drug and drugs that have a detected interaction (interaction_score > 0).
    Returns list of dicts: {drug_id, score}
    """
    df = load_drug_catalog()

    # determine identifier column
    id_col = None
    if "drug_id" in df.columns:
        id_col = "drug_id"
    elif "canonical_id" in df.columns:
        id_col = "canonical_id"

    row = _find_drug_rows(drug_id, df)
    if row.empty:
        return []
        # fallback: match by drug_name or canonical_name
        if "drug_name" in df.columns:
            row = df[df["drug_name"].astype(str).str.lower() == str(drug_id).lower()]
        elif "canonical_name" in df.columns:
            row = df[df["canonical_name"].astype(str).str.lower() == str(drug_id).lower()]
        else:
            row = pd.DataFrame()

    if row.empty:
        return []
    r = row.iloc[0]
    atc = str(r.get("atc_class", "")).strip()
    targets = set(_parse(r.get("targets", "")))
    pathways = set(_parse(r.get("pathways", "")))
    side_effects = set(_parse(r.get("side_effects", "")))

    candidates = []
    for _, c in df.iterrows():
        if id_col:
            cid = c.get(id_col)
        else:
            cid = c.get("drug_name") or c.get("canonical_name")
        if str(cid).lower() == str(drug_id).lower():
            continue

        # exclude interacting drugs
        try:
            inter_score, _ = score_interaction(drug_id, cid)
        except Exception:
            inter_score = 0.0
        if inter_score > 0:
            continue

        cat_score = 1.0 if atc and str(c.get("atc_class", "")).strip() == atc else 0.0
        tset = set(_parse(c.get("targets", "")))
        pset = set(_parse(c.get("pathways", "")))
        sset = set(_parse(c.get("side_effects", "")))

        target_sim = _jaccard(targets, tset)
        pathway_sim = _jaccard(pathways, pset)
        se_sim = _jaccard(side_effects, sset)

        # weighted similarity
        score = 0.5 * cat_score + 0.3 * target_sim + 0.1 * pathway_sim + 0.1 * se_sim
        candidates.append((cid, float(score)))

    candidates.sort(key=lambda x: x[1], reverse=True)
    out = []
    for cid, sc in candidates[:top_k]:
        out.append({"drug_id": cid, "score": round(sc, 3)})
    return out
