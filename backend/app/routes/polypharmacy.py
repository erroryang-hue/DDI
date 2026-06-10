from fastapi import APIRouter, HTTPException
import logging
from typing import List
from pydantic import BaseModel
from app.services.polypharmacy_engine import analyze_polypharmacy

logger = logging.getLogger(__name__)
router = APIRouter()


class PolyRequest(BaseModel):
    drugs: List[str]


@router.post("/polypharmacy")
def polypharmacy(req: PolyRequest):
    try:
        if not req.drugs:
            raise ValueError("Empty drug list")
        return analyze_polypharmacy(req.drugs)
    except ValueError as e:
        logger.exception("Invalid polypharmacy request")
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError:
        logger.exception("Data file missing in polypharmacy")
        raise HTTPException(status_code=500, detail="Required data missing")
    except Exception as e:
        logger.exception("Unhandled error in polypharmacy: %s", e)
        raise HTTPException(status_code=500, detail="Internal service error")
