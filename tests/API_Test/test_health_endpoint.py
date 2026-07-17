from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

EXPECTED_HEALTH_RESPONSE_KEYS = {
    "trace_id",
    "status"
}

def assert_trace_id_contract(response, body):
    assert "x-trace-id" in response.headers
    assert "trace_id" in body
    assert body["trace_id"] == response.headers["x-trace-id"]
    assert isinstance(body["trace_id"], str)
    assert body["trace_id"] != ""

def test_health_endpoint():
    response = client.get("/health")
    body = response.json()

    assert response.status_code == 200
    assert set(body.keys()) == EXPECTED_HEALTH_RESPONSE_KEYS
    assert body["status"] == "ok"
    assert_trace_id_contract(response, body)

def test_health_trace_id():
    first_response = client.get("/health")
    second_response = client.get("/health")

    first_body = first_response.json()
    second_body = second_response.json()

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    assert_trace_id_contract(first_response, first_body)
    assert_trace_id_contract(second_response, second_body)

    assert first_body["trace_id"] != second_body["trace_id"]
    assert first_response.headers["x-trace-id"] != second_response.headers["x-trace-id"]