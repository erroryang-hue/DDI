from fastapi import APIRouter, HTTPException
import logging
from pydantic import BaseModel
from app.services.risk_timeline_engine import predict_timeline

logger = logging.getLogger(__name__)
router = APIRouter()


class TimelineRequest(BaseModel):
    drug1: str
    drug2: str
    start1: float
    start2: float
    interval1: float
    interval2: float
    half_life1: float
    half_life2: float


@router.post("/timeline")
def timeline(req: TimelineRequest):
    try:
        return predict_timeline(
            req.drug1,
            req.drug2,
            req.start1,
            req.start2,
            req.interval1,
            req.interval2,
            req.half_life1,
            req.half_life2,
        )
    except FileNotFoundError:
        logger.exception("Data file missing in timeline")
        raise HTTPException(status_code=500, detail="Required data missing")
    except ValueError as e:
        logger.exception("Invalid timeline request: %s", e)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Unhandled error in timeline: %s", e)
        raise HTTPException(status_code=500, detail="Internal service error")
