from fastapi import APIRouter, HTTPException
import logging
from app.services.analytics import top_entities

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/analytics")
def get_analytics():
    try:
        return top_entities()
    except FileNotFoundError:
        logger.exception("Data file missing in analytics")
        raise HTTPException(status_code=500, detail="Required data missing")
    except Exception as e:
        logger.exception("Unhandled error in analytics: %s", e)
        raise HTTPException(status_code=500, detail="Internal service error")
