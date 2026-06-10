import pytest
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_analyze_endpoint():
    payload = {
        "drug1": "DB001",
        "drug2": "DB002",
        "age": 45,
        "weight": 70.0,
        "dose1": 100.0,
        "dose2": 100.0,
        "start1": 0.0,
        "start2": 2.0,
        "interval1": 24.0,
        "interval2": 24.0,
        "half_life1": 24.0,
        "half_life2": 12.0,
        "poor_metabolizer": False,
    }
    r = client.post("/api/v1/analyze", json=payload)
    assert r.status_code == 200, r.text
    js = r.json()
    # required fields
    for k in ("interaction", "risk_score", "severity", "mechanisms", "graph_paths", "explanation", "recommendations"):
        assert k in js


def test_polypharmacy_endpoint():
    payload = {"drugs": ["DB001", "DB002", "DB003"]}
    r = client.post("/api/v1/polypharmacy", json=payload)
    assert r.status_code == 200, r.text
    js = r.json()
    assert "highest_risk" in js and "average_risk" in js and "results" in js


def test_timeline_endpoint():
    payload = {
        "drug1": "DB001",
        "drug2": "DB002",
        "start1": 0.0,
        "start2": 2.0,
        "interval1": 24.0,
        "interval2": 24.0,
        "half_life1": 24.0,
        "half_life2": 12.0,
    }
    r = client.post("/api/v1/timeline", json=payload)
    assert r.status_code == 200, r.text
    js = r.json()
    assert isinstance(js, list) and len(js) > 0
    assert all("hour" in item and "risk" in item and "temporal_overlap" in item for item in js)


def test_graph_pair_same_node_returns_200():
    r = client.get("/api/v1/graph/DB001/DB001")
    assert r.status_code == 200, r.text
    js = r.json()
    assert "nodes" in js and "edges" in js


def test_graph_neighborhood():
    r = client.get("/api/v1/graph/neighborhood/DB001")
    assert r.status_code == 200, r.text
    js = r.json()
    assert "nodes" in js and "edges" in js


def test_alternatives_endpoint():
    r = client.get("/api/v1/alternatives/DB001")
    assert r.status_code == 200, r.text
    js = r.json()
    assert isinstance(js, list)


def test_analytics_endpoint():
    r = client.get("/api/v1/analytics")
    assert r.status_code == 200, r.text
    js = r.json()
    for k in ("total_drugs", "total_enzymes", "total_pathways", "total_side_effects", "top_drugs", "top_enzymes", "top_pathways", "top_side_effects"):
        assert k in js


def test_export_report_endpoint():
    payload = {
        "drug1": "DB001",
        "drug2": "DB002",
        "risk_score": 0.78,
        "severity": "MODERATE",
        "mechanisms": ["CYP3A4 inhibition", "QT prolongation"],
        "graph_paths": [
            {"path": ["DB001", "DB002"], "relation": "interacts"}
        ],
        "recommendations": ["Monitor ECG", "Reduce dose"],
    }
    r = client.post("/api/v1/export-report", json=payload)
    assert r.status_code == 200, r.text
    assert r.headers["content-type"] == "application/pdf"
    assert r.headers["content-disposition"].startswith("attachment;"), r.headers
    assert r.content[:4] == b"%PDF"
