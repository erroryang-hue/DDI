from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_export_report_endpoint():
    payload = {
        "drug1": "DB001",
        "drug2": "DB002",
        "risk_score": 0.78,
        "severity": "MODERATE",
        "mechanisms": ["CYP3A4 inhibition", "QT prolongation"],
        "graph_paths": [{"path": ["DB001", "DB002"], "relation": "interacts"}],
        "recommendations": ["Monitor ECG", "Reduce dose"],
    }
    r = client.post("/api/v1/export-report", json=payload)
    assert r.status_code == 200, r.text
    assert r.headers["content-type"] == "application/pdf"
    assert r.headers["content-disposition"].startswith("attachment;"), r.headers
    assert r.content[:4] == b"%PDF"
