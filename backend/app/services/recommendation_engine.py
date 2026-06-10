from typing import List


def generate_recommendations(severity: str, mechanisms: List[str], risk_score: float) -> List[str]:
    """Return simple clinical recommendations based on severity.

    Rules:
    - LOW: Continue therapy
    - MEDIUM: Monitor patient
    - HIGH: Consider dose adjustment
    - CRITICAL: Avoid combination
    """
    sev = (severity or "").upper()
    recs = []
    if sev == "LOW":
        recs.append("Continue therapy")
    elif sev == "MEDIUM":
        recs.append("Monitor patient")
    elif sev == "HIGH":
        recs.append("Consider dose adjustment")
    elif sev == "CRITICAL":
        recs.append("Avoid combination")
    else:
        # fallback by numeric risk
        if risk_score is not None:
            if risk_score < 0.33:
                recs.append("Continue therapy")
            elif risk_score < 0.66:
                recs.append("Monitor patient")
            elif risk_score < 0.9:
                recs.append("Consider dose adjustment")
            else:
                recs.append("Avoid combination")
        else:
            recs.append("Review clinical context")

    # add mechanism-specific suggestions
    if mechanisms:
        if any(m for m in mechanisms if "enzyme" in m):
            recs.append("Check CYP interactions and consider therapeutic drug monitoring")
        if any(m for m in mechanisms if "side_effect" in m):
            recs.append("Monitor for overlapping adverse effects")

    return recs
