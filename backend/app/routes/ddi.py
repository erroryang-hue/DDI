from fastapi import APIRouter
from app.models import DDIRequest
from app.services.ddi_service import analyze_ddi

router = APIRouter()

@router.post("/analyze")
def analyze(req: DDIRequest):
    return analyze_ddi(req)