# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.analyze import router as analyze_router
from app.routes.polypharmacy import router as poly_router
from app.routes.alternatives import router as alt_router
from app.routes.timeline import router as timeline_router
from app.routes.graph import router as graph_router
from app.routes.analytics import router as analytics_router
from app.routes.health import router as health_router
from app.routes.search import router as search_router
from app.routes.export_report import router as export_report_router

app = FastAPI(
    title="Drug-Drug Interaction Predictor API",
    description="Hybrid ML/rules-based system for predicting and analyzing drug-drug interactions",
    version="1.0.0"
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Versioned API routes
app.include_router(analyze_router, prefix="/api/v1")
app.include_router(poly_router, prefix="/api/v1")
app.include_router(alt_router, prefix="/api/v1")
app.include_router(timeline_router, prefix="/api/v1")
app.include_router(graph_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")
app.include_router(health_router, prefix="/api/v1")
app.include_router(search_router, prefix="/api/v1")
app.include_router(export_report_router, prefix="/api/v1")