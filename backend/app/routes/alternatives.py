from fastapi import APIRouter, HTTPException
import logging
from app.services.alternative_drug_engine import find_alternatives

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/alternatives/{drug_id}")
def alternatives(drug_id: str):
    try:
        res = find_alternatives(drug_id)
        if res is None:
            raise HTTPException(status_code=404, detail="Drug not found")
        return res
    except HTTPException:
        raise
    except FileNotFoundError:
        logger.exception("Data file missing in alternatives")
        raise HTTPException(status_code=500, detail="Required data missing")
    except Exception as e:
        logger.exception("Unhandled error in alternatives: %s", e)
        raise HTTPException(status_code=500, detail="Internal service error")
