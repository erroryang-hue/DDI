from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import logging
from io import BytesIO

from app.models import AnalysisReport
from app.services.report_service import create_analysis_report_pdf

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/export-report")
def export_report(report: AnalysisReport):
    try:
        pdf_data = create_analysis_report_pdf(report)
        return StreamingResponse(
            BytesIO(pdf_data),
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=ddi-analysis-report.pdf"},
        )
    except Exception as e:
        logger.exception("Failed to generate PDF report: %s", e)
        raise HTTPException(status_code=500, detail={"error": "report_generation_failed", "message": str(e)})
