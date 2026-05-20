from step01_DecisionEvent import DecisionEvent
from event_validation import validate_event, format_validation_issues, ValidationIssue


def get_issue_fields(result):
    return [issues.field_name for issues in result.issues]

def test_valid_event_pass_validation():
    event = DecisionEvent(
        event_id = "event000",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = 800,
        model_version = "v1",
        error_code = None
    )

    result = validate_event(event)
    assert result.is_valid is True
    assert result.issues == []

def test_confidence_is_not_validation_error():
    event = DecisionEvent(
        event_id = "event001",
        decision_type = "approve",
        confidence = None,
        latency_ms = 800,
        model_version = "v1",
        error_code = None
    )

    result = validate_event(event)
    assert result.is_valid is True
    assert "confidence" not in get_issue_fields(result)

def test_confidence_below_zero_is_validation_error():
    event = DecisionEvent(
        event_id = "event002",
        decision_type = "approve",
        confidence = -0.1,
        latency_ms = 800,
        model_version = "v1",
        error_code = None
    )

    result = validate_event(event)
    assert result.is_valid is False
    assert "confidence" in get_issue_fields(result)

def test_confidence_above_zero_is_validation_error():
    event = DecisionEvent(
        event_id = "event003",
        decision_type = "approve",
        confidence = 1.5,
        latency_ms = 800,
        model_version = "v1",
        error_code = None
    )
    result = validate_event(event)
    assert result.is_valid is False
    assert "confidence" in get_issue_fields(result)

def test_confidence_non_numeric_is_validation_error():
    event = DecisionEvent(
        event_id = "event004",
        decision_type = "approve",
        confidence = "abc",
        latency_ms = 800,
        model_version = "v1",
        error_code = None
    )

    result = validate_event(event)
    assert result.is_valid is False
    assert "confidence" in get_issue_fields(result)

def test_model_version_none_is_not_validation_error():
    event = DecisionEvent(
        event_id = "event005",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = 800,
        model_version = None,
        error_code = None
    )

    result = validate_event(event)
    assert result.is_valid is True
    assert "model_version" not in get_issue_fields(result)

def test_invalid_decision_type_is_validation_error():
    event = DecisionEvent(
        event_id = "event006",
        decision_type = "approveee",
        confidence = 0.9,
        latency_ms = 800,
        model_version = "v1",
        error_code = None
    )

    result = validate_event(event)
    assert result.is_valid is False
    assert "decision_type" in get_issue_fields(result)

def test_decision_type_none_is_not_validation_error(): # 현재 구현에서는 validation으로 막지 않는다
    event = DecisionEvent(
        event_id = "event007",
        decision_type = None,
        confidence = 0.9,
        latency_ms = 800,
        model_version = "v1",
        error_code = None
    )

    result = validate_event(event)
    assert result.is_valid is True
    assert "decision_type" not in get_issue_fields(result)

def test_blank_decision_type_is_not_validation_error(): # 현재 구현에서는 validation으로 막지 않는다
    event = DecisionEvent(
        event_id = "event008",
        decision_type = " ",
        confidence = 0.9,
        latency_ms = 800,
        model_version = "v1",
        error_code = None
    )

    result = validate_event(event)
    assert result.is_valid is True
    assert "decision_type" not in get_issue_fields(result)

def test_latency_ms_none_is_not_validation_error():
    event = DecisionEvent(
        event_id = "event009",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = None,
        model_version = "v1",
        error_code = None
    )

    result = validate_event(event)
    assert result.is_valid is True
    assert "latency_ms" not in get_issue_fields(result)

def test_negative_latency_ms_is_validation_error():
    event = DecisionEvent(
        event_id = "event010",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = -800,
        model_version = "v1",
        error_code = None
    )

    result = validate_event(event)
    assert result.is_valid is False
    assert "latency_ms" in get_issue_fields(result)

def test_latency_ms_non_numeric_is_validation_error():
    event = DecisionEvent(
        event_id = "event011",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = "abc",
        model_version = "v1",
        error_code = None
    )

    result = validate_event(event)
    assert result.is_valid is False
    assert "latency_ms" in get_issue_fields(result)

def test_empty_event_id_is_validation_error():
    event = DecisionEvent(
        event_id = " ",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = 800,
        model_version = "v1",
        error_code = None
    )

    result = validate_event(event)
    assert result.is_valid is False
    assert "event_id" in get_issue_fields(result)

def test_event_id_none_is_validation_error():
    event = DecisionEvent(
        event_id = None,
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = 800,
        model_version = "v1",
        error_code = None
    )

    result = validate_event(event)
    assert result.is_valid is False
    assert "event_id" in get_issue_fields(result)

def test_metadata_must_be_dict():
    event = DecisionEvent(
        event_id = "event014",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = 800,
        model_version = "v1",
        error_code = None,
        metadata = "non-a-dict"
    )

    result = validate_event(event)
    assert result.is_valid is False
    assert "metadata" in get_issue_fields(result)

def test_format_validation_issues():
    issues = [
        ValidationIssue(
            field_name = "confidence",
            message = "Confidence must be between 0.0 and 1.0",
            value = 1.5
        )
    ]

    message = format_validation_issues(issues)
    assert "confidence" in message
    assert "Confidence must be between 0.0 and 1.0" in message
    assert "1.5" in message



































