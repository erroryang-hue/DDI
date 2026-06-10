import io
import json
import textwrap
from datetime import datetime
from typing import Any

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from app.models import AnalysisReport


LINE_HEIGHT = 14
LEFT_MARGIN = 72
RIGHT_MARGIN = 540
TOP_MARGIN = 740


def _wrap_text(text: str, width: int = 80) -> list[str]:
    return textwrap.wrap(text, width=width)


def _draw_text_block(c: canvas.Canvas, x: int, y: int, title: str, content_lines: list[str]) -> int:
    c.setFont("Helvetica-Bold", 12)
    c.drawString(x, y, title)
    y -= LINE_HEIGHT
    c.setFont("Helvetica", 10)
    for line in content_lines:
        c.drawString(x + 8, y, line)
        y -= LINE_HEIGHT
    return y - 4


def _ensure_page(c: canvas.Canvas, y: int, required: int) -> int:
    if y < required:
        c.showPage()
        c.setFont("Helvetica", 10)
        return TOP_MARGIN
    return y


def create_analysis_report_pdf(report: AnalysisReport) -> bytes:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    c.setFont("Helvetica-Bold", 18)
    c.drawString(LEFT_MARGIN, TOP_MARGIN, "DDI Analysis Report")
    c.setFont("Helvetica", 10)
    c.drawString(LEFT_MARGIN, TOP_MARGIN - 24, f"Generated: {datetime.utcnow().isoformat()} UTC")
    c.drawString(LEFT_MARGIN, TOP_MARGIN - 40, f"Drug 1: {report.drug1}")
    c.drawString(LEFT_MARGIN, TOP_MARGIN - 56, f"Drug 2: {report.drug2}")

    y = TOP_MARGIN - 80
    y = _ensure_page(c, y, 120)

    y = _draw_text_block(
        c,
        LEFT_MARGIN,
        y,
        "Risk score:",
        [f"{report.risk_score:.3f}"]
    )
    y = _draw_text_block(
        c,
        LEFT_MARGIN,
        y,
        "Severity:",
        [report.severity]
    )

    y = _draw_text_block(
        c,
        LEFT_MARGIN,
        y,
        "Mechanisms:",
        report.mechanisms or ["None detected"]
    )

    graph_representation = json.dumps(report.graph_paths, indent=2)
    graph_lines = []
    for line in graph_representation.splitlines():
        graph_lines.extend(_wrap_text(line, width=90))
    if not graph_lines:
        graph_lines = ["None available"]

    y = _ensure_page(c, y, 120)
    y = _draw_text_block(
        c,
        LEFT_MARGIN,
        y,
        "Graph paths:",
        graph_lines
    )

    y = _ensure_page(c, y, 120)
    y = _draw_text_block(
        c,
        LEFT_MARGIN,
        y,
        "Recommendations:",
        report.recommendations or ["No recommendations available"]
    )

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()
