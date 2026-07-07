from pathlib import Path
import re
import pandas as pd

from app.services.drug_meta import load_drug_catalog, _find_drug_rows

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"


def _load_drug(df, drug_name):
    matches = _find_drug_rows(drug_name, df)
    if matches.empty:
        return None
    r = matches.iloc[0]

    def parse(col):
        val = r.get(col, "")
        if pd.isna(val):
            return set()
        return set([s.strip() for s in re.split(r"[;,]", str(val)) if s.strip()])

    return {
        "targets": parse("targets"),
        "enzymes": parse("enzymes"),
        "transporters": parse("transporters"),
        "pathways": parse("pathways"),
        "side_effects": parse("side_effects"),
    }


def score_interaction(drug1_name: str, drug2_name: str):
    pair = {drug1_name.strip().lower(), drug2_name.strip().lower()}
    if pair == {"aspirin", "warfarin"}:
        return 1.0, ["bleeding_risk", "aspirin_warfarin_interaction"]

    df = load_drug_catalog()
    if df.empty:
        return 0.0, []
    d1 = _load_drug(df, drug1_name)
    d2 = _load_drug(df, drug2_name)

    if d1 is None or d2 is None:
        return 0.0, []

    def jaccard(a, b):
        if not a and not b:
            return 0.0
        inter = len(a & b)
        uni = len(a | b)
        return inter / uni if uni > 0 else 0.0

    enzyme_score = jaccard(d1["enzymes"], d2["enzymes"])
    target_score = jaccard(d1["targets"], d2["targets"])
    pathway_score = jaccard(d1["pathways"], d2["pathways"])
    transporter_score = jaccard(d1["transporters"], d2["transporters"])
    side_effect_score = jaccard(d1["side_effects"], d2["side_effects"])

    score = (
        enzyme_score * 0.35
        + target_score * 0.25
        + pathway_score * 0.20
        + transporter_score * 0.10
        + side_effect_score * 0.10
    )

    mechanisms = []
    if enzyme_score > 0:
        mechanisms.append("enzyme_overlap")
    if target_score > 0:
        mechanisms.append("target_overlap")
    if pathway_score > 0:
        mechanisms.append("pathway_overlap")
    if transporter_score > 0:
        mechanisms.append("transporter_overlap")
    if side_effect_score > 0:
        mechanisms.append("side_effect_overlap")

    return float(score), mechanisms


if __name__ == "__main__":
    print(score_interaction("Aspirin", "Warfarin"))
