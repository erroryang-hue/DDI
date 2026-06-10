from typing import List, Dict, Any, Tuple
from itertools import combinations
from app.services.risk_engine import compute_risk


def analyze_polypharmacy(drugs: List[str]) -> Dict[str, Any]:
    """Generate all pairwise combinations, run risk analysis for each pair.

    Returns highest risk interaction, average risk, and all pair results.
    """
    pairs = list(combinations(drugs, 2))
    results = []
    scores = []
    for a, b in pairs:
        final, details = compute_risk(a, b, temporal_overlap=0.0, interaction_score=0.0)
        results.append({"drug1": a, "drug2": b, "risk": final, "details": details})
        scores.append(final)

    if not scores:
        return {"highest_risk": None, "average_risk": 0.0, "results": results}

    avg = sum(scores) / len(scores)
    idx = max(range(len(scores)), key=lambda i: scores[i])
    highest = results[idx]

    return {"highest_risk": highest, "average_risk": avg, "results": results}
