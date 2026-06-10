import math
from pathlib import Path

import joblib
import pandas as pd
from ml.gnn_inference import predict_interaction

ROOT_DIR = Path(__file__).resolve().parents[2]
GRAPH_CSV_PATH = ROOT_DIR / "data" / "graph_edges.csv"
MODEL_PATH = ROOT_DIR / "ddi_model.pkl"

try:
    model = joblib.load(MODEL_PATH)
except Exception:
    model = None

_graph_df = pd.read_csv(GRAPH_CSV_PATH)


# ---------------- RULES ---------------- #

def enzyme_inhibition(d1, d2):
    inhib = _graph_df[( _graph_df["source"] == d1) & (_graph_df["relation"] == "INHIBITS")]
    metab = _graph_df[( _graph_df["source"] == d2) & (_graph_df["relation"] == "METABOLIZED_BY")]
    shared = set(inhib["target"]) & set(metab["target"])
    return [{"enzyme": enzyme} for enzyme in sorted(shared)]


def enzyme_induction(d1, d2):
    induc = _graph_df[( _graph_df["source"] == d1) & (_graph_df["relation"] == "INDUCES")]
    metab = _graph_df[( _graph_df["source"] == d2) & (_graph_df["relation"] == "METABOLIZED_BY")]
    shared = set(induc["target"]) & set(metab["target"])
    return [{"enzyme": enzyme} for enzyme in sorted(shared)]


def additive_toxicity(d1, d2):
    tox1 = _graph_df[( _graph_df["source"] == d1) & (_graph_df["relation"] == "CAUSES")]
    tox2 = _graph_df[( _graph_df["source"] == d2) & (_graph_df["relation"] == "CAUSES")]
    shared = set(tox1["target"]) & set(tox2["target"])
    return [{"effect": effect} for effect in sorted(shared)]


# ---------------- TEMPORAL MODEL ---------------- #

def elimination_rate(half_life):
    return math.log(2) / half_life


def exposure(t, k):
    return math.exp(-k * t)


def temporal_overlap(start1, start2, k1, k2, horizon=48, step=0.5):
    t = 0
    overlap = 0
    total = 0

    while t <= horizon:
        c1 = exposure(max(0, t - start1), k1) if t >= start1 else 0
        c2 = exposure(max(0, t - start2), k2) if t >= start2 else 0

        overlap += min(c1, c2) * step
        total += max(c1, c2) * step

        t += step

    return overlap / total if total > 0 else 0


# ---------------- PATIENT CONTEXT ---------------- #

def patient_modifier(age, weight, dose1, dose2, poor_metabolizer):
    f = 1.0

    if age >= 65:
        f += 0.25
    elif age <= 18:
        f += 0.1

    if weight < 50:
        f += 0.2
    elif weight > 100:
        f -= 0.05

    total = dose1 + dose2
    if total > 500:
        f += 0.3
    elif total > 200:
        f += 0.15

    if poor_metabolizer:
        f += 0.3

    return f


# ---------------- DOSE SCHEDULING ---------------- #

def schedule_factor(start1, start2, interval1, interval2):
    phase = abs(start1 - start2)
    base = max(interval1, interval2)

    if base == 0:
        return 1.0

    phi = (phase % base) / base

    if phi < 0.2:
        return 1.2
    elif phi < 0.5:
        return 1.0
    else:
        return 0.8


# ---------------- SCORING ---------------- #

def compute_risk(req, results):
    base_score = 0
    mechanisms = []
    evidence = []

    if results["inhibition"]:
        base_score += 0.5
        mechanisms.append("enzyme_inhibition")
        evidence += [{"type": "enzyme", "value": r["enzyme"]} for r in results["inhibition"]]

    if results["induction"]:
        base_score += 0.3
        mechanisms.append("enzyme_induction")

    if results["toxicity"]:
        base_score += 0.4
        mechanisms.append("additive_toxicity")
        evidence += [{"type": "side_effect", "value": r["effect"]} for r in results["toxicity"]]

    # Temporal
    k1 = elimination_rate(req.half_life1)
    k2 = elimination_rate(req.half_life2)

    overlap = temporal_overlap(req.start1, req.start2, k1, k2)
    sched = schedule_factor(req.start1, req.start2, req.interval1, req.interval2)

    # Patient
    pmod = patient_modifier(
        req.age, req.weight, req.dose1, req.dose2, req.poor_metabolizer
    )

    # Final risk
    raw = base_score * (0.5 + 0.5 * overlap) * sched * pmod
    final_score = 1 - math.exp(-raw)

    return final_score, mechanisms, evidence, overlap, sched, pmod


# ---------------- MAIN PIPELINE ---------------- #

def analyze_ddi(req):
    results = {
        "inhibition": enzyme_inhibition(req.drug1, req.drug2),
        "induction": enzyme_induction(req.drug1, req.drug2),
        "toxicity": additive_toxicity(req.drug1, req.drug2)
    }

    rule_score, mechanisms, evidence, overlap, sched, pmod = compute_risk(req, results)
    gnn_score = predict_interaction(req.drug1, req.drug2)
    ml_score = predict_with_ml(req)

    if gnn_score is not None:
        final_score = 0.7 * rule_score + 0.3 * gnn_score
    else:
        final_score = rule_score

    severity = (
        "HIGH" if final_score > 0.7 else
        "MEDIUM" if final_score > 0.4 else
        "LOW"
    )

    response = {
        "interaction": final_score > 0,
        "mechanisms": mechanisms,
        "evidence": evidence,
        "risk_score": round(final_score, 3),
        "severity": severity,
        "components": {
            "rule_score": round(rule_score, 3),
            "ml_score": round(ml_score, 3) if ml_score is not None else None
        },
        "temporal": {
            "overlap": round(overlap, 3),
            "schedule_factor": sched
        },
        "patient": {
            "modifier": pmod
        }
    }

    if gnn_score is not None:
        response["gnn"] = {"score": round(gnn_score, 3)}

    return response

def predict_with_ml(req):
    if model is None:
        return None

    features = [[
        req.age,
        req.weight,
        req.dose1,
        req.dose2,
        req.start1,
        req.start2,
        req.interval1,
        req.interval2,
        req.half_life1,
        req.half_life2,
        int(req.poor_metabolizer)
    ]]

    return float(model.predict(features)[0])