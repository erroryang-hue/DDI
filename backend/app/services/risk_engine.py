from pathlib import Path
from typing import Tuple, Dict, Optional
import pandas as pd
import joblib

from ml.gnn_inference import predict_interaction

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
DRUGS_CSV = DATA_DIR / "drugs.csv"
RF_MODEL = ROOT / "models" / "rf_model.pkl"


def _parse(cell):
    if pd.isna(cell) or cell is None:
        return set()
    return set([s.strip() for s in str(cell).split(";") if s.strip()])


def _jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 0.0
    inter = len(a & b)
    uni = len(a | b)
    return inter / uni if uni > 0 else 0.0


def compute_risk(drug1: str, drug2: str, temporal_overlap: float, interaction_score: float) -> Tuple[float, Dict]:
    """Combine rf_score, gnn_score, interaction_score, temporal_overlap into final risk.

    Returns (final_score, details) where details includes components and severity.
    """
    # compute overlaps
    df = pd.read_csv(DRUGS_CSV)
    r1 = df[df["drug_id"] == drug1]
    r2 = df[df["drug_id"] == drug2]
    if r1.empty or r2.empty:
        # fallback: use available scores
        gnn_score = predict_interaction(drug1, drug2) or 0.0
        rf_score = None
    else:
        r1 = r1.iloc[0]
        r2 = r2.iloc[0]
        enzymes1 = _parse(r1.get("enzymes", ""))
        enzymes2 = _parse(r2.get("enzymes", ""))
        targets1 = _parse(r1.get("targets", ""))
        targets2 = _parse(r2.get("targets", ""))
        pathways1 = _parse(r1.get("pathways", ""))
        pathways2 = _parse(r2.get("pathways", ""))
        transport1 = _parse(r1.get("transporters", ""))
        transport2 = _parse(r2.get("transporters", ""))
        se1 = _parse(r1.get("side_effects", ""))
        se2 = _parse(r2.get("side_effects", ""))

        features = {
            "enzyme_overlap": _jaccard(enzymes1, enzymes2),
            "target_overlap": _jaccard(targets1, targets2),
            "pathway_overlap": _jaccard(pathways1, pathways2),
            "transporter_overlap": _jaccard(transport1, transport2),
            "side_effect_overlap": _jaccard(se1, se2),
        }

        # RF model
        rf_score = None
        if RF_MODEL.exists():
            try:
                model = joblib.load(RF_MODEL)
                # order expected by training
                X = [[
                    features["enzyme_overlap"],
                    features["target_overlap"],
                    features["pathway_overlap"],
                    features["transporter_overlap"],
                    features["side_effect_overlap"],
                ]]
                if hasattr(model, "predict_proba"):
                    rf_score = float(model.predict_proba(X)[0][1])
                else:
                    rf_score = float(model.predict(X)[0])
            except Exception:
                rf_score = None

        gnn_score = predict_interaction(drug1, drug2) or 0.0

    # assemble components; for missing rf_score we treat as 0 but will normalize weights
    components = {
        "rf_score": rf_score,
        "gnn_score": gnn_score,
        "interaction_score": float(interaction_score or 0.0),
        "temporal_overlap": float(temporal_overlap or 0.0),
    }

    # weights
    w = {"rf_score": 0.40, "gnn_score": 0.25, "interaction_score": 0.20, "temporal_overlap": 0.15}
    # determine available components
    avail = {k: v for k, v in components.items() if v is not None}
    total_w = sum(w[k] for k in avail.keys())
    if total_w <= 0:
        final = 0.0
    else:
        final = sum(avail[k] * w[k] for k in avail.keys()) / total_w

    # severity mapping
    if final < 0.33:
        severity = "LOW"
    elif final < 0.66:
        severity = "MEDIUM"
    elif final < 0.9:
        severity = "HIGH"
    else:
        severity = "CRITICAL"

    details = {"components": components, "weights": w, "severity": severity}
    return float(final), details
from pathlib import Path
import joblib
from ml.gnn_inference import predict_interaction

ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = ROOT / "ddi_model.pkl"

try:
    ml_model = joblib.load(MODEL_PATH)
except Exception:
    ml_model = None


def compute_final_risk(interaction_score: float, temporal_overlap: float, drug1, drug2) -> (float, dict):
    # ml score
    ml_score = None
    if ml_model is not None:
        try:
            # placeholder features — in production build proper feature vector
            ml_score = float(ml_model.predict([[0]])[0])
        except Exception:
            ml_score = None

    # gnn score
    gnn_score = predict_interaction(drug1, drug2)

    # default missing scores to 0
    ml_val = ml_score if ml_score is not None else 0.0
    gnn_val = gnn_score if gnn_score is not None else 0.0

    final = (
        0.35 * float(interaction_score)
        + 0.20 * float(temporal_overlap)
        + 0.20 * float(ml_val)
        + 0.25 * float(gnn_val)
    )

    # severity mapping
    sev = "LOW"
    if final >= 0.85:
        sev = "CRITICAL"
    elif final >= 0.7:
        sev = "HIGH"
    elif final >= 0.4:
        sev = "MEDIUM"

    details = {"ml_score": ml_score, "gnn_score": gnn_score}
    return float(final), {"severity": sev, **details}


if __name__ == "__main__":
    print(compute_final_risk(0.5, 0.5, "DrugA", "DrugB"))
