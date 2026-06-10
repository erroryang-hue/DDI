from fastapi import APIRouter, HTTPException
import logging
from pathlib import Path
from app.graph.graph_builder import build_graph

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
def health_check():
    root = Path(__file__).resolve().parents[2]
    models_dir = root / "models"
    data_dir = root / "data"

    report = {
        "rf_model": False,
        "gnn_model": False,
        "graph": False,
        "demo_cases": False,
        "details": {},
    }

    try:
        rf = models_dir / "rf_model.pkl"
        gnn = models_dir / "gnn_model.pt"
        report["rf_model"] = rf.exists()
        report["gnn_model"] = gnn.exists()
        report["demo_cases"] = (data_dir / "demo_cases.csv").exists()

        # try to load graph
        try:
            G = build_graph()
            report["graph"] = True if G is not None else False
        except Exception as e:
            logger.exception("Graph load failed: %s", e)
            report["details"]["graph_error"] = str(e)

        return report
    except Exception as e:
        logger.exception("Health check failed: %s", e)
        raise HTTPException(status_code=500, detail="Health check failed")
