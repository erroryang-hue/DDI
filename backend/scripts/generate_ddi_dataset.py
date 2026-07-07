"""Generate improved DDI dataset with realistic interaction labels and balanced classes.

Produces: data/ddi_dataset.csv
"""
from pathlib import Path
import random
import pandas as pd
from itertools import combinations
from app.services.ddi_service import enzyme_inhibition, enzyme_induction, additive_toxicity

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DRUGS_CSV = DATA_DIR / "drugs.csv"
GENERATED_CSV = DATA_DIR / "drugs_generated.csv"
OUT_CSV = DATA_DIR / "ddi_dataset.csv"


def _parse(cell):
    if pd.isna(cell) or cell is None:
        return set()
    return set([s.strip() for s in str(cell).split(";") if s.strip()])


def generate_dataset(balance: bool = True):
    # Load official drugs and optionally include generated synthetic drugs
    df_list = []
    if DRUGS_CSV.exists():
        df_list.append(pd.read_csv(DRUGS_CSV))
    if GENERATED_CSV.exists():
        df_list.append(pd.read_csv(GENERATED_CSV))
    if not df_list:
        raise FileNotFoundError("No drugs CSV found in data directory")
    df = pd.concat(df_list, ignore_index=True)
    # ensure a consistent drug_id column exists
    if "drug_id" not in df.columns:
        # create drug_id from drug_name by uppercasing and replacing non-alphanum
        def make_id(name, idx):
            if pd.isna(name) or str(name).strip() == "":
                return f"UNK{idx:04d}"
            base = str(name).strip().upper()
            base = "".join([c if c.isalnum() else "_" for c in base])
            return base

        df = df.reset_index(drop=True)
        df["drug_id"] = [make_id(r.get("drug_name", ""), i) for i, r in df.iterrows()]

    df = df.drop_duplicates(subset=["drug_id"])
    pairs = list(combinations(df["drug_id"].tolist(), 2))
    rows = []
    # build a mapping for fast, reliable lookups
    df = df.reset_index(drop=True)
    records = {r["drug_id"]: r for r in df.to_dict(orient="records")}
    for d1, d2 in pairs:
        if d1 not in records or d2 not in records:
            # skip malformed or missing entries
            continue
        r1 = records[d1]
        r2 = records[d2]

        enzymes1 = _parse(r1.get("enzymes", ""))
        enzymes2 = _parse(r2.get("enzymes", ""))
        targets1 = _parse(r1.get("targets", ""))
        targets2 = _parse(r2.get("targets", ""))
        pathways1 = _parse(r1.get("pathways", ""))
        pathways2 = _parse(r2.get("pathways", ""))
        trans1 = _parse(r1.get("transporters", ""))
        trans2 = _parse(r2.get("transporters", ""))
        se1 = _parse(r1.get("side_effects", ""))
        se2 = _parse(r2.get("side_effects", ""))

        def jacc(a, b):
            if not a and not b:
                return 0.0
            inter = len(a & b)
            uni = len(a | b)
            return inter / uni if uni > 0 else 0.0

        enzyme_overlap = jacc(enzymes1, enzymes2)
        target_overlap = jacc(targets1, targets2)
        pathway_overlap = jacc(pathways1, pathways2)
        transporter_overlap = jacc(trans1, trans2)
        side_effect_overlap = jacc(se1, se2)

        # rules-based signals from graph edges
        inhib = enzyme_inhibition(d1, d2)
        induc = enzyme_induction(d1, d2)
        tox = additive_toxicity(d1, d2)

        inhib_flag = 1 if inhib else 0
        induc_flag = 1 if induc else 0
        tox_flag = 1 if tox else 0

        # base risk as weighted sum
        risk = (
            0.30 * enzyme_overlap
            + 0.25 * target_overlap
            + 0.15 * pathway_overlap
            + 0.10 * transporter_overlap
            + 0.10 * side_effect_overlap
            + 0.05 * inhib_flag
            + 0.03 * induc_flag
            + 0.02 * tox_flag
        )

        # add small randomness and clamp
        risk = max(0.0, min(1.0, risk + random.uniform(-0.05, 0.05)))

        # derive label: threshold based on risk
        label = 1 if risk >= 0.5 else 0

        rows.append({
            "drug1": d1,
            "drug2": d2,
            "enzyme_overlap": enzyme_overlap,
            "target_overlap": target_overlap,
            "pathway_overlap": pathway_overlap,
            "transporter_overlap": transporter_overlap,
            "side_effect_overlap": side_effect_overlap,
            "inhibition": inhib_flag,
            "induction": induc_flag,
            "additive_toxicity": tox_flag,
            "risk_score": round(risk, 4),
            "interaction": label,
        })

    df_out = pd.DataFrame(rows)

    if balance:
        pos = df_out[df_out["interaction"] == 1]
        neg = df_out[df_out["interaction"] == 0]
        if len(pos) == 0 or len(neg) == 0:
            df_out.to_csv(OUT_CSV, index=False)
            print("Dataset saved (unbalanced):", OUT_CSV)
            return
        # undersample majority to balance
        if len(pos) > len(neg):
            pos = pos.sample(len(neg), random_state=42)
        else:
            neg = neg.sample(len(pos), random_state=42)
        df_bal = pd.concat([pos, neg]).sample(frac=1.0, random_state=42).reset_index(drop=True)
        df_bal.to_csv(OUT_CSV, index=False)
        print("Balanced dataset saved:", OUT_CSV)
    else:
        df_out.to_csv(OUT_CSV, index=False)
        print("Dataset saved:", OUT_CSV)


if __name__ == "__main__":
    generate_dataset()
