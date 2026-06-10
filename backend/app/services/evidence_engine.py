from typing import List, Tuple
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
DRUGS_CSV = DATA_DIR / "drugs.csv"


def _parse(cell):
    if pd.isna(cell) or cell is None:
        return set()
    return set([s.strip() for s in str(cell).split(";") if s.strip()])


def evidence_and_confidence(
    graph_paths: List[str],
    shared_enzymes: List[str],
    shared_targets: List[str],
    shared_pathways: List[str],
    shared_side_effects: List[str],
) -> Tuple[int, float]:
    """Compute evidence count and confidence score between 0 and 1.

    Confidence increases with more graph paths and more overlapping mechanisms.
    """
    # counts
    gp = len(graph_paths or [])
    e_cnt = len(shared_enzymes or [])
    t_cnt = len(shared_targets or [])
    p_cnt = len(shared_pathways or [])
    s_cnt = len(shared_side_effects or [])

    evidence_count = gp + e_cnt + t_cnt + p_cnt + s_cnt

    # graph contribution (cap at 5)
    graph_score = min(gp, 5) / 5.0

    # overlap contribution: normalize each category to [0,1] cap at 5
    overlap_score = (
        min(e_cnt, 5) / 5.0
        + min(t_cnt, 5) / 5.0
        + min(p_cnt, 5) / 5.0
        + min(s_cnt, 5) / 5.0
    ) / 4.0

    # combine: give more weight to graph evidence
    confidence = 0.6 * graph_score + 0.4 * overlap_score
    # small boost for larger evidence_count
    if evidence_count >= 8:
        confidence = min(1.0, confidence + 0.05)

    return evidence_count, float(round(confidence, 4))


def infer_interaction_type(
    shared_side_effects: List[str],
    shared_pathways: List[str],
    shared_targets: List[str],
    shared_enzymes: List[str],
) -> str:
    """Infer most likely interaction type from shared mechanisms.

    Returns one of the defined classes or 'UNKNOWN'.
    """
    # lowercase sets for matching
    ss = set([s.lower() for s in (shared_side_effects or [])])
    sp = set([s.lower() for s in (shared_pathways or [])])
    st = set([s.lower() for s in (shared_targets or [])])
    se = set([s.lower() for s in (shared_enzymes or [])])

    scores = {"BLEEDING": 0, "QT_PROLONGATION": 0, "HEPATOTOXICITY": 0, "NEPHROTOXICITY": 0, "SEDATION": 0, "HYPOTENSION": 0, "METABOLIC": 0}

    # side effect signals
    for s in ss:
        if "bleed" in s or "hemorr" in s:
            scores["BLEEDING"] += 2
        if "qt" in s or "prolongation" in s:
            scores["QT_PROLONGATION"] += 3
        if "hepato" in s or "liver" in s:
            scores["HEPATOTOXICITY"] += 3
        if "renal" in s or "nephro" in s:
            scores["NEPHROTOXICITY"] += 3
        if "sedat" in s or "drows" in s:
            scores["SEDATION"] += 2
        if "hypot" in s or "low blood" in s:
            scores["HYPOTENSION"] += 2
        if "metab" in s or "glucose" in s:
            scores["METABOLIC"] += 2

    # pathway signals
    for p in sp:
        if "coag" in p or "coagulation" in p:
            scores["BLEEDING"] += 2
        if "cardiac" in p or "ion channel" in p or "qt" in p:
            scores["QT_PROLONGATION"] += 2
        if "liver" in p or "hepatic" in p:
            scores["HEPATOTOXICITY"] += 2
        if "renal" in p:
            scores["NEPHROTOXICITY"] += 2

    # enzyme/target signals (common CYP interactions -> hepatotoxicity or metabolic)
    for en in se:
        if en.startswith("cyp"):
            scores["HEPATOTOXICITY"] += 1
            scores["METABOLIC"] += 1

    for t in st:
        if "h1" in t.lower() or "adrenergic" in t.lower():
            scores["HYPOTENSION"] += 1
        if "ion" in t.lower() or "kcn" in t.lower():
            scores["QT_PROLONGATION"] += 1

    # select highest
    best = max(scores.items(), key=lambda kv: kv[1])
    if best[1] == 0:
        return "UNKNOWN"
    return best[0]
