from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

EXPECTED_EVALUATE_RESPONSE_KEYS = {
    "trace_id",
    "event_id",
    "level",
    "risk_score",
    "uncertainty_score",
    "human_required",
    "recommended_actions",
    "reason_summary",
    "signals",
    "metadata"
}


EXPECTED_SIGNAL_KEYS = {
    "rule_id",
    "category",
    "score",
    "reason",
    "evidence",
    "is_critical_override",
    "metadata"
}

def assert_trace_id_contract(response, body):
    assert "x-trace-id" in response.headers
    assert body["trace_id"] == response.headers["x-trace-id"]

def assert_evaluate_response_contract(response, body):
    assert response.status_code == 200
    assert set(body.keys()) == EXPECTED_EVALUATE_RESPONSE_KEYS
    assert_trace_id_contract(response, body)

def test_evaluate_endpoint():
    payload = {
        "event_id": "evt_api_001",
        "decision_type": "approve",
        "confidence": 0.95,
        "latency_ms": 300,
        "model_version": "v1",
        "error_code": None,
        "metadata": {"source": "api_test"}
    }

    response = client.post("/evaluate", json=payload)
    body = response.json()
    assert_evaluate_response_contract(response, body)

    assert body["event_id"] == "evt_api_001"
    assert body["level"] == "INFO"
    assert body["risk_score"] == 0
    assert body["uncertainty_score"] == 0
    assert body["human_required"] is False
    assert body["recommended_actions"] == ["no_immediate_action_required"]
    assert isinstance(body["reason_summary"], str)
    assert body["signals"] == []
    assert body["metadata"] == {"source": "api_test"}

def test_evaluate_low_confidence_risk_signal():
    payload = {
        "event_id": "evt_api_002",
        "decision_type": "approve",
        "confidence": 0.6,
        "latency_ms": 300,
        "model_version": "v1",
        "error_code": None,
        "metadata": {}
    }

    response = client.post("/evaluate", json=payload)
    body = response.json()
    assert_evaluate_response_contract(response, body)

    assert body["event_id"] == "evt_api_002"
    assert body["level"] == "WARN"
    assert body["risk_score"] == 3
    assert body["uncertainty_score"] == 0
    assert body["human_required"] is False
    assert body["recommended_actions"] == ["monitor_closely"]
    assert len(body["signals"]) == 1
    signal = body["signals"][0]
    assert set(signal.keys()) == EXPECTED_SIGNAL_KEYS
    assert signal["rule_id"] == "approve_confidence_low"
    assert signal["category"] == "risk"
    assert signal["score"] == 3
    assert isinstance(signal["reason"], str)
    assert signal["evidence"]["decision_type"] == "approve"
    assert signal["evidence"]["confidence"] == 0.6
    assert signal["is_critical_override"] is False
    assert signal["metadata"] == {}

def test_evaluate_high_latency_risk_signal():
    payload = {
        "event_id": "evt_api_003",
        "decision_type": "reject",
        "confidence": 0.95,
        "latency_ms": 2000,
        "model_version": "v1",
        "error_code": None,
        "metadata": {}
    }

    response = client.post("/evaluate", json=payload)
    body = response.json()
    assert_evaluate_response_contract(response, body)

    assert body["event_id"] == "evt_api_003"
    assert body["level"] == "WARN"
    assert body["risk_score"] == 2
    assert body["uncertainty_score"] == 0
    assert body["human_required"] is False
    assert body["recommended_actions"] == ["monitor_closely"]
    assert len(body["signals"]) == 1
    signal = body["signals"][0]
    assert set(signal.keys()) == EXPECTED_SIGNAL_KEYS
    assert signal["rule_id"] == "latency_high"
    assert signal["category"] == "risk"
    assert signal["score"] == 2
    assert signal["evidence"]["latency_ms"] == 2000
    assert signal["is_critical_override"] is False
    assert signal["metadata"] == {}

def test_evaluate_critical_risk_signals():
    payload = {
        "event_id": "evt_api_004",
        "decision_type": "approve",
        "confidence": 0.6,
        "latency_ms": 2000,
        "model_version": "v1",
        "error_code": None,
        "metadata": {}
    }

    response = client.post("/evaluate", json=payload)
    body = response.json()
    assert_evaluate_response_contract(response, body)

    assert body["event_id"] == "evt_api_004"
    assert body["level"] == "CRITICAL"
    assert body["risk_score"] == 5
    assert body["uncertainty_score"] == 0
    assert body["human_required"] is True
    assert body["recommended_actions"] == ["human_review_required", "escalate_incident"]
    assert [signal["rule_id"] for signal in body["signals"]] == ["approve_confidence_low", "latency_high"]
    assert [signal["category"] for signal in body["signals"]] == ["risk", "risk"]

def test_evaluate_uncertainty_signal():
    payload = {
        "event_id": "evt_api_005",
        "decision_type": "reject",
        "confidence": 0.95,
        "latency_ms": 300,
        "model_version": None,
        "error_code": None,
        "metadata": {}
    }

    response = client.post("/evaluate", json=payload)
    body = response.json()
    assert_evaluate_response_contract(response, body)

    assert body["event_id"] == "evt_api_005"
    assert body["level"] == "INFO"
    assert body["risk_score"] == 0
    assert body["uncertainty_score"] == 1
    assert body["human_required"] is False
    assert body["recommended_actions"] == ["review_missing_or_incomplete_information", "no_immediate_action_required"]
    assert len(body["signals"]) == 1
    signal = body["signals"][0]
    assert set(signal.keys()) == EXPECTED_SIGNAL_KEYS
    assert signal["rule_id"] == "missing_model_version"
    assert signal["category"] == "uncertainty"
    assert signal["score"] == 1
    assert signal["evidence"]["model_version"] is None
    assert signal["is_critical_override"] is False
    assert signal["metadata"] == {}

def test_evaluate_critical_override():
    payload = {
        "event_id": "evt_api_006",
        "decision_type": "reject",
        "confidence": 0.95,
        "latency_ms": 300,
        "model_version": "v1",
        "error_code": "timeout_01",
        "metadata": {}
    }

    response = client.post("/evaluate", json=payload)
    body = response.json()
    assert_evaluate_response_contract(response, body)

    assert body["event_id"] == "evt_api_006"
    assert body["level"] == "CRITICAL"
    assert body["risk_score"] == 0
    assert body["uncertainty_score"] == 0
    assert body["human_required"] is True
    assert body["recommended_actions"] == ["human_review_required", "immediate_investigation", "escalate_incident"]
    assert len(body["signals"]) == 1
    signal = body["signals"][0]
    assert set(signal.keys()) == EXPECTED_SIGNAL_KEYS
    assert signal["rule_id"] == "evaluation_integrity_override"
    assert signal["category"] == "failure"
    assert signal["score"] == 0
    assert signal["evidence"]["error_code"] == "timeout_01"
    assert signal["is_critical_override"] is True
    assert signal["metadata"]["failure_type"] == "system_error"
    assert signal["metadata"]["score_contribution"] == "none"
    assert signal["metadata"]["override_type"] == "critical"

def test_evaluate_normalizes_input():
    payload = {
        "event_id": "  evt_api_007  ",
        "decision_type": "  APPROVE  ",
        "confidence": 0.95,
        "latency_ms": 300,
        "model_version": "v1",
        "error_code": None,
        "metadata": {}
    }

    response = client.post("/evaluate", json=payload)
    body = response.json()
    assert_evaluate_response_contract(response, body)

    assert body["event_id"] == "evt_api_007"
    assert body["level"] == "INFO"
    assert body["risk_score"] == 0
    assert body["uncertainty_score"] == 0
    assert body["human_required"] is False
    assert body["signals"] == []