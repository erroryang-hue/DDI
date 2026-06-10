from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
DRUGS_CSV = DATA_DIR / "drugs.csv"


def _load_drug(df, drug_id):
    row = df[df["drug_id"] == drug_id]
    if row.empty:
        return None
    r = row.iloc[0]
    def parse(col):
        val = r.get(col, "")
        if pd.isna(val):
            return set()
        return set([s.strip() for s in str(val).split(";") if s.strip()])
    return {
        "targets": parse("targets"),
        "enzymes": parse("enzymes"),
        "transporters": parse("transporters"),
        "pathways": parse("pathways"),
        "side_effects": parse("side_effects"),
    }


def score_interaction(drug1_id: str, drug2_id: str):
    df = pd.read_csv(DRUGS_CSV)
    d1 = _load_drug(df, drug1_id)
    d2 = _load_drug(df, drug2_id)

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
    print(score_interaction("DB001", "DB002"))
