import app.main as main_module
from fastapi.testclient import TestClient

client = TestClient(
    main_module.app,
    raise_server_exceptions=False,
)

def test_unexpected_internal_error(monkeypatch):
    def raise_unexpected_error(payload, trace_id):
        raise RuntimeError()

    # test를 위해 모듈 임시 교체
    monkeypatch.setattr(
        main_module,
        "evaluate_request",
        raise_unexpected_error,
    )

    payload = {
        "event_id": "event_system_error_001",
        "decision_type": "approve",
        "confidence": 0.8,
        "latency_ms": 300,
        "model_version": "v1",
        "error_code": None,
        "metadata": {},
    }

    response = client.post("/evaluate", json=payload)
    body = response.json()

    assert response.status_code == 500
    assert set(body.keys()) == {
        "trace_id",
        "error_type",
        "message",
        "details",
    }
    assert body["error_type"] == "system_error"
    assert body["message"] == "Unexpected internal server error"
    assert "x-trace-id" in response.headers
    assert body["trace_id"] == response.headers["x-trace-id"]