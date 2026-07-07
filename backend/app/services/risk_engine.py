from pathlib import Path
from typing import Tuple, Dict
import math
import re
import pandas as pd
import joblib

from app.services.drug_meta import load_drug_catalog, _find_drug_rows
from ml.gnn_inference import predict_interaction

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
RF_MODEL = ROOT / "models" / "rf_model.pkl"


def _parse(cell):
    if pd.isna(cell) or cell is None:
        return set()
    return set([s.strip() for s in re.split(r"[;,]", str(cell)) if s.strip()])


def _jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 0.0
    inter = len(a & b)
    uni = len(a | b)
    return inter / uni if uni > 0 else 0.0


def _patient_modifier(age, weight, dose1, dose2, poor_metabolizer):
    f = 1.0

    if age is not None:
        if age >= 65:
            f += 0.25
        elif age <= 18:
            f += 0.1

    if weight is not None:
        if weight < 50:
            f += 0.2
        elif weight > 100:
            f -= 0.05

    if dose1 is not None and dose2 is not None:
        total = dose1 + dose2
        if total > 500:
            f += 0.3
        elif total > 200:
            f += 0.15

    if poor_metabolizer:
        f += 0.3

    return max(0.5, f)


def compute_risk(
    drug1: str,
    drug2: str,
    temporal_overlap: float,
    interaction_score: float,
    age: float | None = None,
    weight: float | None = None,
    dose1: float | None = None,
    dose2: float | None = None,
    poor_metabolizer: bool = False,
) -> Tuple[float, Dict]:
    """Combine rf_score, gnn_score, interaction_score, temporal_overlap, and dose context into final risk."""
    df = load_drug_catalog()
    if df.empty:
        rf_score = None
        gnn_score = predict_interaction(drug1, drug2) or 0.0
    else:
        r1 = _find_drug_rows(drug1, df)
        r2 = _find_drug_rows(drug2, df)
        if r1.empty or r2.empty:
            rf_score = None
            gnn_score = predict_interaction(drug1, drug2) or 0.0
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

            rf_score = None
            if RF_MODEL.exists():
                try:
                    model = joblib.load(RF_MODEL)
                    X = pd.DataFrame([features])
                    if hasattr(model, "predict_proba"):
                        rf_score = float(model.predict_proba(X)[0][1])
                    else:
                        rf_score = float(model.predict(X)[0])
                except Exception:
                    rf_score = None

            gnn_score = predict_interaction(drug1, drug2) or 0.0

    components = {
        "rf_score": rf_score,
        "gnn_score": gnn_score,
        "interaction_score": float(interaction_score or 0.0),
        "temporal_overlap": float(temporal_overlap or 0.0),
        "dose1": float(dose1) if dose1 is not None else None,
        "dose2": float(dose2) if dose2 is not None else None,
    }

    w = {"rf_score": 0.25, "gnn_score": 0.35, "interaction_score": 0.30, "temporal_overlap": 0.10}
    avail = {k: v for k, v in components.items() if v is not None and k in w}
    total_w = sum(w[k] for k in avail.keys())
    if total_w <= 0:
        base = 0.0
    else:
        base = sum(avail[k] * w[k] for k in avail.keys()) / total_w

    modifier = _patient_modifier(age, weight, dose1, dose2, poor_metabolizer)
    final = 1 - math.exp(-base * modifier)

    if float(components.get("interaction_score", 0.0)) >= 0.85:
        final = max(final, 0.75)

    if final < 0.33:
        severity = "LOW"
    elif final < 0.66:
        severity = "MEDIUM"
    elif final < 0.9:
        severity = "HIGH"
    else:
        severity = "CRITICAL"

    details = {
        "components": components,
        "weights": w,
        "modifier": round(modifier, 3),
        "severity": severity,
    }
    return float(final), details


if __name__ == "__main__":
    print(compute_risk("Aspirin", "Warfarin", 0.5, 0.5))
