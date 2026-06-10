from typing import List, Dict
import math
from datetime import datetime, timedelta

from app.services.temporal_engine import temporal_overlap
from app.services.risk_engine import compute_risk


def _decay_concentration(dose_times: List[float], t: float, half_life: float) -> float:
    # t and dose_times in hours; half_life in hours
    if half_life <= 0:
        return 0.0
    k = math.log(2) / half_life
    conc = 0.0
    for dt in dose_times:
        if dt <= t:
            conc += math.exp(-k * (t - dt))
    return conc


def predict_timeline(
    drug1: str,
    drug2: str,
    start1: float,
    start2: float,
    interval1: float,
    interval2: float,
    half_life1: float,
    half_life2: float,
    hours: int = 72,
):
    """Predict risk every hour for `hours` hours. start times and intervals in hours."""
    # generate dose times up to hours for each drug
    doses1 = []
    t = start1
    while t <= hours:
        doses1.append(t)
        t += interval1 if interval1 > 0 else hours + 1

    doses2 = []
    t = start2
    while t <= hours:
        doses2.append(t)
        t += interval2 if interval2 > 0 else hours + 1

    timeline = []
    # interaction static score from interaction engine
    from app.services.interaction_engine import score_interaction

    interaction_score, mechanisms = score_interaction(drug1, drug2)

    for hour in range(0, hours + 1):
        c1 = _decay_concentration(doses1, hour, half_life1)
        c2 = _decay_concentration(doses2, hour, half_life2)
        # normalize concentrations to [0,1]
        maxc1 = max([_decay_concentration(doses1, h, half_life1) for h in range(0, hours + 1)]) or 1.0
        maxc2 = max([_decay_concentration(doses2, h, half_life2) for h in range(0, hours + 1)]) or 1.0
        norm1 = c1 / maxc1
        norm2 = c2 / maxc2
        # temporal overlap proxy: product of normalized concentrations
        temp_overlap = norm1 * norm2

        final, details = compute_risk(drug1, drug2, temp_overlap, interaction_score)
        timeline.append({"hour": hour, "risk": final, "temporal_overlap": temp_overlap})

    return timeline
