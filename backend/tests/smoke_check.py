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
    "drug1": "Aspirin",
    "drug2": "Warfarin",
    "age": 45,
    "weight": 70.0,
    "dose1": 100.0,
    "dose2": 100.0,
    "start1": 0.0,
    "start2": 2.0,
    "interval1": 24.0,
    "interval2": 24.0,
    "half_life1": 0.25,
    "half_life2": 40.0,
    "poor_metabolizer": False,
}

payload_timeline = {
    "drug1": "Aspirin",
    "drug2": "Warfarin",
    "start1": 0.0,
    "start2": 2.0,
    "interval1": 24.0,
    "interval2": 24.0,
    "half_life1": 0.25,
    "half_life2": 40.0,
}

call_get('/api/v1/analytics')
call_get('/api/v1/graph/neighborhood/Aspirin')
call_get('/api/v1/graph/Aspirin/Warfarin')
call_get('/api/v1/search/Aspirin')
call_get('/api/v1/alternatives/Aspirin')
call_post('/api/v1/timeline', payload_timeline)
call_post('/api/v1/polypharmacy', {"drugs": ["Aspirin", "Warfarin", "Metformin"]})
call_post('/api/v1/analyze', payload_analyze)
