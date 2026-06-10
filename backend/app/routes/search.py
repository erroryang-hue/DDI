from fastapi import APIRouter, HTTPException
import logging
from app.services.search_service import search_drug

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/search/{drug}")
def search(drug: str):
    try:
        res = search_drug(drug)
        if not res:
            raise HTTPException(status_code=404, detail={"error": "drug_not_found"})
        return res
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Search failed: %s", e)
        raise HTTPException(status_code=500, detail={"error": "search_failed"})
