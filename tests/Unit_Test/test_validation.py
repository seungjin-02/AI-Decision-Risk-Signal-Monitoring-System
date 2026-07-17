from core.step01_DecisionEvent import DecisionEvent
from core.event_validation import ValidationIssue, format_validation_issues, validate_event

def get_issue_fields(result):
    return [issue.field_name for issue in result.issues]

def get_issue_by_field(result, field_name: str) -> ValidationIssue:
    for issue in result.issues:
        if issue.field_name == field_name:
            return issue
    raise AssertionError(f"validation issue not found: {field_name}")

def test_valid_event_passes_validation():
    event = DecisionEvent(
        event_id = "evt_validation_001",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = 800,
        model_version = "v1",
        error_code = None
    )

    result = validate_event(event)

    assert result.is_valid is True
    assert result.issues == []

def test_event_id_must_not_be_none():
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


def test_event_id_must_be_string():
    event = DecisionEvent(
        event_id = 123,
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = 800,
        model_version = "v1",
        error_code = None
    )

    result = validate_event(event)

    assert result.is_valid is False
    assert "event_id" in get_issue_fields(result)


def test_event_id_must_not_be_blank():
    event = DecisionEvent(
        event_id = "   ",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = 800,
        model_version = "v1",
        error_code = None
    )

    result = validate_event(event)

    assert result.is_valid is False
    assert "event_id" in get_issue_fields(result)

def test_confidence_none_is_allowed():
    event = DecisionEvent(
        event_id = "evt_validation_002",
        decision_type = "approve",
        confidence = None,
        latency_ms = 800,
        model_version = "v1",
        error_code = None
    )

    result = validate_event(event)

    assert result.is_valid is True
    assert "confidence" not in get_issue_fields(result)

def test_confidence_at_lower_boundary_is_valid():
    event = DecisionEvent(
        event_id = "evt_validation_003",
        decision_type = "approve",
        confidence = 0.0,
        latency_ms = 800,
        model_version = "v1",
        error_code = None
    )

    result = validate_event(event)

    assert result.is_valid is True

def test_confidence_at_upper_boundary_is_valid():
    event = DecisionEvent(
        event_id = "evt_validation_004",
        decision_type = "approve",
        confidence = 1.0,
        latency_ms = 800,
        model_version = "v1",
        error_code = None
    )

    result = validate_event(event)

    assert result.is_valid is True

def test_confidence_below_zero_is_validation_error():
    event = DecisionEvent(
        event_id = "evt_validation_005",
        decision_type = "approve",
        confidence = -0.1,
        latency_ms = 800,
        model_version = "v1",
        error_code = None
    )

    result = validate_event(event)

    assert result.is_valid is False
    assert "confidence" in get_issue_fields(result)

def test_confidence_above_one_is_validation_error():
    event = DecisionEvent(
        event_id = "evt_validation_006",
        decision_type = "approve",
        confidence = 1.5,
        latency_ms = 800,
        model_version = "v1",
        error_code = None
    )

    result = validate_event(event)

    assert result.is_valid is False
    assert "confidence" in get_issue_fields(result)

def test_confidence_string_is_validation_error():
    event = DecisionEvent(
        event_id = "evt_validation_007",
        decision_type = "approve",
        confidence = "0.52",
        latency_ms = 800,
        model_version = "v1",
        error_code = None
    )

    result = validate_event(event)

    assert result.is_valid is False
    assert "confidence" in get_issue_fields(result)

def test_confidence_bool_is_validation_error():
    event = DecisionEvent(
        event_id = "evt_validation_008",
        decision_type = "approve",
        confidence = True,
        latency_ms = 800,
        model_version = "v1",
        error_code = None
    )

    result = validate_event(event)

    assert result.is_valid is False
    assert "confidence" in get_issue_fields(result)

def test_latency_ms_none_is_allowed():
    event = DecisionEvent(
        event_id = "evt_validation_009",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = None,
        model_version = "v1",
        error_code = None
    )

    result = validate_event(event)

    assert result.is_valid is True
    assert "latency_ms" not in get_issue_fields(result)

def test_latency_ms_zero_is_valid():
    event = DecisionEvent(
        event_id = "evt_validation_010",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = 0,
        model_version = "v1",
        error_code = None
    )

    result = validate_event(event)

    assert result.is_valid is True

def test_negative_latency_ms_is_validation_error():
    event = DecisionEvent(
        event_id = "evt_validation_011",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = -1,
        model_version = "v1",
        error_code = None
    )

    result = validate_event(event)

    assert result.is_valid is False
    assert "latency_ms" in get_issue_fields(result)

def test_latency_ms_string_is_validation_error():
    event = DecisionEvent(
        event_id = "evt_validation_012",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = "2800",
        model_version = "v1",
        error_code = None
    )

    result = validate_event(event)

    assert result.is_valid is False
    assert "latency_ms" in get_issue_fields(result)

def test_latency_ms_float_is_validation_error():
    event = DecisionEvent(
        event_id = "evt_validation_013",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = 1800.5,
        model_version = "v1",
        error_code = None
    )

    result = validate_event(event)

    assert result.is_valid is False
    assert "latency_ms" in get_issue_fields(result)


def test_latency_ms_bool_is_validation_error():
    event = DecisionEvent(
        event_id = "evt_validation_014",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = True,
        model_version = "v1",
        error_code = None
    )

    result = validate_event(event)

    assert result.is_valid is False
    assert "latency_ms" in get_issue_fields(result)

def test_decision_type_none_is_allowed():
    event = DecisionEvent(
        event_id = "evt_validation_015",
        decision_type = None,
        confidence = 0.9,
        latency_ms = 800,
        model_version = "v1",
        error_code = None
    )

    result = validate_event(event)

    assert result.is_valid is True
    assert "decision_type" not in get_issue_fields(result)

def test_decision_type_approve_is_valid():
    event = DecisionEvent(
        event_id = "evt_validation_016",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = 800,
        model_version = "v1",
        error_code = None
    )

    result = validate_event(event)

    assert result.is_valid is True

def test_decision_type_reject_is_valid():
    event = DecisionEvent(
        event_id = "evt_validation_017",
        decision_type = "reject",
        confidence = 0.9,
        latency_ms = 800,
        model_version = "v1",
        error_code = None
    )

    result = validate_event(event)

    assert result.is_valid is True

def test_decision_type_is_case_and_whitespace_tolerant():
    event = DecisionEvent(
        event_id = "evt_validation_018",
        decision_type = " APPROVE ",
        confidence = 0.9,
        latency_ms = 800,
        model_version = "v1",
        error_code = None
    )

    result = validate_event(event)

    assert result.is_valid is True

def test_blank_decision_type_is_validation_error():
    event = DecisionEvent(
        event_id = "evt_validation_019",
        decision_type = "   ",
        confidence = 0.9,
        latency_ms = 800,
        model_version = "v1",
        error_code = None
    )

    result = validate_event(event)

    assert result.is_valid is False
    assert "decision_type" in get_issue_fields(result)

def test_invalid_decision_type_is_validation_error():
    event = DecisionEvent(
        event_id = "evt_validation_020",
        decision_type = "approveee",
        confidence = 0.9,
        latency_ms = 800,
        model_version = "v1",
        error_code = None
    )

    result = validate_event(event)

    assert result.is_valid is False
    assert "decision_type" in get_issue_fields(result)

def test_non_string_decision_type_is_validation_error():
    event = DecisionEvent(
        event_id = "evt_validation_021",
        decision_type = 123,
        confidence = 0.9,
        latency_ms = 800,
        model_version = "v1",
        error_code = None
    )

    result = validate_event(event)

    assert result.is_valid is False
    assert "decision_type" in get_issue_fields(result)

def test_model_version_none_is_allowed():
    event = DecisionEvent(
        event_id = "evt_validation_022",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = 800,
        model_version = None,
        error_code = None
    )

    result = validate_event(event)

    assert result.is_valid is True
    assert "model_version" not in get_issue_fields(result)

def test_model_version_string_is_valid():
    event = DecisionEvent(
        event_id = "evt_validation_023",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = 800,
        model_version = "v1",
        error_code = None
    )

    result = validate_event(event)

    assert result.is_valid is True

def test_blank_model_version_is_allowed():
    event = DecisionEvent(
        event_id = "evt_validation_024",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = 800,
        model_version = "   ",
        error_code = None
    )

    result = validate_event(event)

    assert result.is_valid is True
    assert "model_version" not in get_issue_fields(result)

def test_model_version_non_string_is_validation_error():
    event = DecisionEvent(
        event_id = "evt_validation_025",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = 800,
        model_version = 100,
        error_code = None
    )

    result = validate_event(event)

    assert result.is_valid is False
    assert "model_version" in get_issue_fields(result)

def test_error_code_none_is_valid():
    event = DecisionEvent(
        event_id = "evt_validation_026",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = 800,
        model_version = "v1",
        error_code = None
    )

    result = validate_event(event)

    assert result.is_valid is True

def test_error_code_string_is_valid():
    event = DecisionEvent(
        event_id = "evt_validation_027",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = 800,
        model_version = "v1",
        error_code = "gateway_failure"
    )

    result = validate_event(event)

    assert result.is_valid is True

def test_blank_error_code_is_allowed():
    event = DecisionEvent(
        event_id = "evt_validation_028",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = 800,
        model_version = "v1",
        error_code = "   "
    )

    result = validate_event(event)

    assert result.is_valid is True
    assert "error_code" not in get_issue_fields(result)

def test_error_code_non_string_is_validation_error():
    event = DecisionEvent(
        event_id = "evt_validation_029",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = 800,
        model_version = "v1",
        error_code = 500
    )

    result = validate_event(event)

    assert result.is_valid is False
    assert "error_code" in get_issue_fields(result)

def test_metadata_dict_is_valid():
    event = DecisionEvent(
        event_id = "evt_validation_030",
        decision_type = "approve",
        confidence = 0.9,
        latency_ms = 800,
        model_version = "v1",
        error_code = None,
        metadata = {"request_id": "req_001"}
    )

    result = validate_event(event)

    assert result.is_valid is True

def test_metadata_must_be_dict():
    event = DecisionEvent(
        event_id = "evt_validation_031",
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

def test_multiple_validation_errors_are_accumulated():
    event = DecisionEvent(
        event_id = "   ",
        decision_type = "approveee",
        confidence = 1.5,
        latency_ms = -1,
        model_version = 100,
        error_code = 500,
        metadata = "non-a-dict"
    )

    result = validate_event(event)

    assert result.is_valid is False
    assert set(get_issue_fields(result)) == {
        "event_id",
        "decision_type",
        "confidence",
        "latency_ms",
        "model_version",
        "error_code",
        "metadata",
    }