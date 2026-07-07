from fastapi import APIRouter, HTTPException
import logging
from typing import Dict, Any, List
from app.models import DDIRequest
from app.services.interaction_engine import score_interaction
from app.services.temporal_engine import temporal_overlap
from app.services.risk_engine import compute_risk
from app.services.graph_reasoning import find_reasoning_paths
from app.services.explanation_engine import generate_explanation
from app.services.recommendation_engine import generate_recommendations
from app.services.drug_meta import get_half_life
from pathlib import Path
import pandas as pd

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/analyze")
def analyze(req: DDIRequest) -> Dict[str, Any]:
    """Full analyze pipeline with graceful degradation.

    Flow:
    Request -> Graph Reasoning -> RF Model -> GNN Model -> Risk Aggregation -> Explanation -> Recommendation -> Response
    """
    logger.info("Analyze request received: %s / %s", req.drug1, req.drug2)

    # Stage 1: Graph Reasoning
    graph_paths: List[str] = []
    graph_mechanisms: List[str] = []
    try:
        graph_paths, graph_mechanisms = find_reasoning_paths(req.drug1, req.drug2)
        logger.debug("Graph reasoning returned %d paths and mechanisms: %s", len(graph_paths), graph_mechanisms)
    except Exception as e:
        logger.exception("Graph reasoning failed: %s", e)
        graph_paths, graph_mechanisms = [], []

    # Stage 2: Interaction engine
    interaction_score = 0.0
    interaction_mechanisms: List[str] = []
    try:
        interaction_score, interaction_mechanisms = score_interaction(req.drug1, req.drug2)
        logger.debug("Interaction score=%s mechanisms=%s", interaction_score, interaction_mechanisms)
    except Exception as e:
        logger.exception("Interaction scoring failed: %s", e)
        interaction_score, interaction_mechanisms = 0.0, []

    # Stage 3: Temporal overlap
    temporal = 0.0
    try:
        # ensure half-life values are present; if not, use `get_half_life` to lookup
        half1 = req.half_life1
        half2 = req.half_life2
        if half1 is None:
            try:
                h = get_half_life(req.drug1)
                half1 = h if h is not None else 24.0
            except Exception:
                half1 = 24.0
        if half2 is None:
            try:
                h = get_half_life(req.drug2)
                half2 = h if h is not None else 24.0
            except Exception:
                half2 = 24.0

        # Note: `req.start1` and `req.start2` represent times or intervals; the frontend
        # now sends `time_between` as the interval between two drug administrations.
        # If `time_between` is present, prefer it for temporal overlap calculation.
        if getattr(req, "time_between", None) is not None:
            try:
                tb = float(req.time_between)
                temporal = temporal_overlap(0, tb, half1, half2)
            except Exception:
                temporal = temporal_overlap(req.start1, req.start2, half1, half2)
        else:
            temporal = temporal_overlap(req.start1, req.start2, half1, half2)
        logger.debug("Temporal overlap=%s", temporal)
    except Exception as e:
        logger.exception("Temporal overlap computation failed: %s", e)
        temporal = 0.0

    # Stage 4: Risk aggregation (RF + GNN inside compute_risk)
    risk_score = 0.0
    severity = "UNKNOWN"
    components: Dict[str, Any] = {}
    try:
        risk_score, details = compute_risk(
            req.drug1,
            req.drug2,
            temporal,
            interaction_score,
            age=req.age,
            weight=req.weight,
            dose1=req.dose1,
            dose2=req.dose2,
            poor_metabolizer=req.poor_metabolizer,
        )
        components = details
        severity = details.get("severity")
        logger.debug("Risk aggregation produced score=%s severity=%s components=%s", risk_score, severity, components)
    except Exception as e:
        logger.exception("Risk aggregation failed: %s", e)
        # degraded: use interaction_score and temporal only
        try:
            risk_score = float(interaction_score * 0.7 + temporal * 0.3)
        except Exception:
            risk_score = 0.0
        severity = "UNKNOWN"
        components = {"rf_score": None, "gnn_score": None, "interaction_score": interaction_score, "temporal_overlap": temporal}

    # Stage 5: merge mechanisms
    merged_mechanisms = sorted(list(set(interaction_mechanisms or []) | set(graph_mechanisms or [])))

    # Stage 6: Explanation
    explanation = ""
    try:
        explanation = generate_explanation(req.drug1, req.drug2, merged_mechanisms, graph_paths, risk_score)
        logger.debug("Explanation generated: %s", explanation)
    except Exception as e:
        logger.exception("Explanation generation failed: %s", e)
        explanation = "Explanation unavailable due to internal error"

    # Stage 7: Recommendations
    recommendations: List[str] = []
    try:
        recommendations = generate_recommendations(severity, merged_mechanisms, risk_score)
        logger.debug("Recommendations: %s", recommendations)
    except Exception as e:
        logger.exception("Recommendation generation failed: %s", e)
        recommendations = []

    response = {
        "interaction": bool(interaction_score > 0 or len(merged_mechanisms) > 0),
        "risk_score": round(float(risk_score), 3),
        "severity": severity,
        "mechanisms": merged_mechanisms,
        "graph_paths": graph_paths,
        "explanation": explanation,
        "recommendations": recommendations,
    }

    logger.info("Analyze response prepared for %s/%s: %s", req.drug1, req.drug2, response)
    return response
