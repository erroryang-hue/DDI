from fastapi import APIRouter, HTTPException
import logging
from pathlib import Path
import pandas as pd
from app.services.drug_meta import load_drug_catalog
from app.services.search_service import search_drug

logger = logging.getLogger(__name__)
router = APIRouter()

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"


@router.get("/drugs")
def get_drugs_list():
    """Get list of all available drugs with basic information"""
    try:
        drugs = []
        df = load_drug_catalog()
        if df.empty:
            raise HTTPException(status_code=404, detail={"error": "drugs_data_not_found"})

        if "drug_name" in df.columns:
            df = df.drop_duplicates(subset=["drug_name"])

        for _, row in df.iterrows():
            # accept either `half_life` or `half_life_hours`
            hl = None
            if pd.notna(row.get("half_life")):
                try:
                    hl = float(row.get("half_life"))
                except Exception:
                    hl = None
            if hl is None and pd.notna(row.get("half_life_hours")):
                try:
                    hl = float(row.get("half_life_hours"))
                except Exception:
                    hl = None

            drugs.append({
                "name": str(row.get("drug_name", "")),
                "generic_name": str(row.get("generic_name", "")),
                "drug_class": str(row.get("drug_class", "")),
                "atc_class": str(row.get("atc_class", "")),
                "half_life": float(hl) if hl is not None else 0,
            })
        return {"drugs": drugs}
    except Exception as e:
        logger.exception("Get drugs list failed: %s", e)
        raise HTTPException(status_code=500, detail={"error": "get_drugs_failed"})


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
