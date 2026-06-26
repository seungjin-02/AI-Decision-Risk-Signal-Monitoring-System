from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_evaluate_endpoint_returns_normal_response():
    payload = {
        "event_id": "evt_001",
        "decision_type": "approve",
        "confidence": 0.52,
        "latency_ms": 2800,
        "model_version": "v1",
        "error_code": None,
        "metadata": {},
    }
    response = client.post("/evaluate", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert "trace_id" in body
    assert body["event_id"] == "evt_001"
    assert "level" in body
    assert "risk_score" in body
    assert "uncertainty_score" in body
    assert "human_required" in body
    assert "recommended_actions" in body
    assert "signals" in body