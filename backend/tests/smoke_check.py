import sys
from pathlib import Path
# ensure repo root/backend is on sys.path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def call_get(path):
    try:
        r = client.get(path)
        print(path, r.status_code)
        try:
            print(r.json())
        except Exception:
            print("<non-json response>")
    except Exception as e:
        print(path, "error", e)

def call_post(path, payload):
    try:
        r = client.post(path, json=payload)
        print(path, r.status_code)
        try:
            print(r.json())
        except Exception:
            print("<non-json response>")
    except Exception as e:
        print(path, "error", e)


payload_analyze = {
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

payload_timeline = {
    "drug1": "DB001",
    "drug2": "DB002",
    "start1": 0.0,
    "start2": 2.0,
    "interval1": 24.0,
    "interval2": 24.0,
    "half_life1": 24.0,
    "half_life2": 12.0,
}

call_get('/api/v1/analytics')
call_get('/api/v1/graph/neighborhood/DB001')
call_get('/api/v1/graph/DB001/DB001')
call_get('/api/v1/search/DB001')
call_get('/api/v1/alternatives/DB001')
call_post('/api/v1/timeline', payload_timeline)
call_post('/api/v1/polypharmacy', {"drugs": ["DB001", "DB002", "DB003"]})
call_post('/api/v1/analyze', payload_analyze)
