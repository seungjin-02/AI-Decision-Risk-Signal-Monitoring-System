import json
import sqlite3
import pytest

from datetime import datetime

from app.db.alert_repository import PersistenceError
from app.db.connection import create_connection
from core.main import evaluate_event
from core.step01_DecisionEvent import DecisionEvent

def test_save_stores_alert_row(repository, test_db_path):
    event = DecisionEvent(
        event_id="event_repository_001",
        decision_type="approve",
        confidence=0.3,
        latency_ms=800,
        model_version="v1",
        error_code=None,
        metadata={
            "source": "repository_test",
        },
    )

    alert = evaluate_event(event)

    saved = repository.save(
        alert=alert,
        trace_id="trace_test_001",
    )

    connection = create_connection(test_db_path)

    try:
        alert_row = connection.execute(
            """
            SELECT
                alert_id,
                trace_id,
                event_id,
                level,
                risk_score,
                uncertainty_score,
                human_required,
                reason_summary,
                metadata,
                created_at
            FROM alerts
            WHERE alert_id = ?
            """,
            (saved.alert_id,)
        ).fetchone()

        assert alert_row is not None
        assert alert_row["alert_id"] == saved.alert_id
        assert alert_row["trace_id"] == "trace_test_001"
        assert alert_row["event_id"] == alert.event_id
        assert alert_row["level"] == alert.level
        assert alert_row["risk_score"] == alert.risk_score
        assert alert_row["uncertainty_score"] == alert.uncertainty_score
        assert alert_row["human_required"] == int(alert.human_required)
        assert alert_row["reason_summary"] == alert.reason_summary
        assert json.loads(alert_row["metadata"]) == alert.metadata
        assert alert_row["created_at"]

    finally:
        connection.close()

def test_save_stores_signal_row(repository, test_db_path):
    event = DecisionEvent(
        event_id="event_repository_002",
        decision_type="approve",
        confidence=0.3,
        latency_ms=800,
        model_version="v1",
        error_code=None,
        metadata={
            "source": "repository_test",
        },
    )

    alert = evaluate_event(event)

    saved = repository.save(
        alert=alert,
        trace_id="trace_test_002",
    )

    connection = create_connection(test_db_path)

    try:
        signal_rows = connection.execute(
            """
            SELECT
                signal_id,
                alert_id,
                rule_id,
                category,
                score,
                reason,
                evidence,
                is_critical_override,
                metadata
            FROM alert_signals
            WHERE alert_id = ?
            ORDER BY signal_id
            """,
            (saved.alert_id,)
        ).fetchall()

        assert len(signal_rows) == len(alert.signals)

        for signal_row, signal in zip(signal_rows, alert.signals):
            assert signal_row["signal_id"] is not None
            assert signal_row["alert_id"] == saved.alert_id
            assert signal_row["rule_id"] == signal.rule_id
            assert signal_row["category"] == signal.category
            assert signal_row["score"] == signal.score
            assert signal_row["reason"] == signal.reason
            assert json.loads(signal_row["evidence"]) == signal.evidence
            assert signal_row["is_critical_override"] == int(signal.is_critical_override)
            assert json.loads(signal_row["metadata"]) == signal.metadata

    finally:
        connection.close()

def test_save_stores_action_row(repository, test_db_path):
    event = DecisionEvent(
        event_id="event_repository_003",
        decision_type="approve",
        confidence=0.3,
        latency_ms=800,
        model_version="v1",
        error_code=None,
        metadata={
            "source": "repository_test",
        },
    )

    alert = evaluate_event(event)

    saved = repository.save(
        alert=alert,
        trace_id="trace_test_003",
    )

    connection = create_connection(test_db_path)

    try:
        action_rows = connection.execute(
            """
            SELECT
                action_id,
                alert_id,
                action_code,
                action_order
            FROM alert_actions
            WHERE alert_id = ?
            ORDER BY action_order
            """,
            (saved.alert_id,),
        ).fetchall()

        assert len(action_rows) == len(alert.recommended_actions)

        for expected_order, action_row in enumerate(action_rows):
            action_code = alert.recommended_actions[expected_order]

            assert action_row["action_id"] is not None
            assert action_row["alert_id"] == saved.alert_id
            assert action_row["action_code"] == action_code
            assert action_row["action_order"] == expected_order

    finally:
        connection.close()

def test_save_rollback(repository, test_db_path):
    event = DecisionEvent(
        event_id="event_repository_004",
        decision_type="approve",
        confidence=0.3,
        latency_ms=800,
        model_version="v1",
        error_code=None,
        metadata={
            "source": "repository_test",
        },
    )

    alert = evaluate_event(event)

    # 동일한 rule_id를 가진 signal을 의도적으로 중복 추가
    alert.signals.append(alert.signals[0])

    with pytest.raises(PersistenceError) as exc_info:
        repository.save(
            alert=alert,
            trace_id="trace_test_004",
        )

    # PersistenceError가 원래 IntegrityError를 보존하는지 검증
    assert isinstance(exc_info.value.__cause__, sqlite3.IntegrityError)

    connection = create_connection(test_db_path)

    try:
        alert_count = connection.execute(
            "SELECT COUNT(*) FROM alerts"
        ).fetchone()[0]

        signal_count = connection.execute(
            "SELECT COUNT(*) FROM alert_signals"
        ).fetchone()[0]

        action_count = connection.execute(
            "SELECT COUNT(*) FROM alert_actions"
        ).fetchone()[0]

        assert alert_count == 0
        assert signal_count == 0
        assert action_count == 0

    finally:
        connection.close()

def test_find_by_id_returns_none_when_alert_does_not_exist(repository):
    result = repository.find_by_id(alert_id=999)

    assert result is None

def test_find_by_id_returns_existing_alert(repository):
    event = DecisionEvent(
        event_id="event_find_by_id_001",
        decision_type="approve",
        confidence=0.3,
        latency_ms=800,
        model_version="v1",
        error_code=None,
        metadata={
            "source": "repository_find_test",
        },
    )

    alert = evaluate_event(event)

    saved = repository.save(
        alert=alert,
        trace_id="trace_find_by_id_001",
    )

    result = repository.find_by_id(
        alert_id=saved.alert_id,
    )

    assert result is not None
    assert result.alert_id == saved.alert_id
    assert result.trace_id == "trace_find_by_id_001"
    assert result.event_id == alert.event_id
    assert result.level == alert.level
    assert result.risk_score == alert.risk_score
    assert result.uncertainty_score == alert.uncertainty_score
    assert result.human_required is alert.human_required
    assert result.reason_summary == alert.reason_summary
    assert result.metadata == alert.metadata
    assert result.created_at == saved.created_at
    assert result.recommended_actions == alert.recommended_actions
    assert result.signals == alert.signals
    assert isinstance(result.human_required, bool)
    assert isinstance(result.metadata, dict)
    for signal in result.signals:
        assert isinstance(signal.is_critical_override, bool)
        assert isinstance(signal.evidence, dict)
        assert isinstance(signal.metadata, dict)

def test_search_returns_empty_list_when_database_is_empty(repository):
    results = repository.search(limit=10)

    assert results == []

def test_search_out_of_limit_range_raise_value_error(repository):
    for invalid_limit in 0, 101:
        with pytest.raises(ValueError, match="limit must be between 1 and 100"):
            repository.search(limit=invalid_limit)

def test_search_applies_limit_and_preserves_alert_details(repository):
    first_event = DecisionEvent(
        event_id="event_search_001",
        decision_type="approve",
        confidence=0.3,
        latency_ms=800,
        model_version="v1",
        error_code=None,
        metadata={
            "source": "repository_search_test1",
        },
    )

    first_alert = evaluate_event(first_event)

    first_saved = repository.save(
        alert=first_alert,
        trace_id="trace_search_001",
    )

    second_event = DecisionEvent(
        event_id="event_search_002",
        decision_type="approve",
        confidence=0.8,
        latency_ms=1800,
        model_version="v2",
        error_code=None,
        metadata={
            "source": "repository_search_test2",
        },
    )

    second_alert = evaluate_event(second_event)

    second_saved = repository.save(
        alert=second_alert,
        trace_id="trace_search_002",
    )

    result_by_one = repository.search(limit=1)

    assert len(result_by_one) == 1

    result = result_by_one[0]

    assert result.alert_id == second_saved.alert_id
    assert result.trace_id == "trace_search_002"
    assert result.event_id == second_alert.event_id
    assert result.level == second_alert.level
    assert result.risk_score == second_alert.risk_score
    assert result.uncertainty_score == second_alert.uncertainty_score
    assert result.human_required is second_alert.human_required
    assert result.reason_summary == second_alert.reason_summary
    assert result.metadata == second_alert.metadata
    assert result.created_at == second_saved.created_at
    assert result.recommended_actions == second_alert.recommended_actions
    assert result.signals == second_alert.signals

    result_by_two = repository.search(limit=2)

    assert len(result_by_two) == 2

    recent_result, older_result = result_by_two

    assert recent_result.alert_id == second_saved.alert_id
    assert older_result.alert_id == first_saved.alert_id
    assert recent_result.signals == second_alert.signals
    assert recent_result.recommended_actions == second_alert.recommended_actions
    assert older_result.signals == first_alert.signals
    assert older_result.recommended_actions == first_alert.recommended_actions

def test_search_filters_by_level(repository):
    info_event = DecisionEvent(
        event_id="event_search_level_info",
        decision_type="approve",
        confidence=0.95,
        latency_ms=300,
        model_version="v1",
        error_code=None,
        metadata={
            "source": "repository_search_level_test",
        },
    )

    info_alert = evaluate_event(info_event)

    assert info_alert.level == "INFO"

    info_saved = repository.save(
        alert=info_alert,
        trace_id="trace_search_level_info",
    )

    critical_event = DecisionEvent(
        event_id="event_search_level_critical",
        decision_type="approve",
        confidence=0.3,
        latency_ms=2800,
        model_version="v1",
        error_code=None,
        metadata={
            "source": "repository_search_level_test",
        },
    )

    critical_alert = evaluate_event(critical_event)

    assert critical_alert.level == "CRITICAL"

    critical_saved = repository.save(
        alert=critical_alert,
        trace_id="trace_search_level_critical",
    )

    results = repository.search(
        limit=10,
        level="CRITICAL",
    )

    assert [result.alert_id for result in results] == [critical_saved.alert_id]

def test_search_filters_by_human_required(repository):
    not_required_event = DecisionEvent(
        event_id="event_search_human_not_required",
        decision_type="approve",
        confidence=0.95,
        latency_ms=300,
        model_version="v1",
        error_code=None,
        metadata={
            "source": "repository_search_human_test",
        },
    )

    not_required_alert = evaluate_event(
        not_required_event
    )

    assert not_required_alert.human_required is False

    not_required_saved = repository.save(
        alert=not_required_alert,
        trace_id="trace_search_human_not_required",
    )

    required_event = DecisionEvent(
        event_id="event_search_human_required",
        decision_type="approve",
        confidence=0.3,
        latency_ms=2800,
        model_version="v1",
        error_code=None,
        metadata={
            "source": "repository_search_human_test",
        },
    )

    required_alert = evaluate_event(required_event)

    assert required_alert.human_required is True

    required_saved = repository.save(
        alert=required_alert,
        trace_id="trace_search_human_required",
    )

    required_results = repository.search(
        limit=10,
        human_required=True,
    )

    assert [result.alert_id for result in required_results] == [required_saved.alert_id]

    not_required_results = repository.search(
        limit=10,
        human_required=False,
    )

    assert [result.alert_id for result in not_required_results] == [not_required_saved.alert_id]

def test_search_filters_by_created_at_range(repository, test_db_path):
    event = DecisionEvent(
        event_id="event_search_created_at",
        decision_type="approve",
        confidence=0.95,
        latency_ms=300,
        model_version="v1",
        error_code=None,
        metadata={
            "source": "repository_search_time_test",
        },
    )

    alert = evaluate_event(event)

    before_saved = repository.save(
        alert=alert,
        trace_id="trace_search_time_before",
    )

    start_saved = repository.save(
        alert=alert,
        trace_id="trace_search_time_start",
    )

    end_saved = repository.save(
        alert=alert,
        trace_id="trace_search_time_end",
    )

    connection = create_connection(test_db_path)

    try:
        timestamps = [
            (
                "2026-08-20T04:00:00+00:00",
                before_saved.alert_id,
            ),
            (
                "2026-08-20T05:00:00+00:00",
                start_saved.alert_id,
            ),
            (
                "2026-08-20T06:00:00+00:00",
                end_saved.alert_id,
            ),
        ]

        for created_at, alert_id in timestamps:
            connection.execute(
                """
                UPDATE alerts
                SET created_at = ?
                WHERE alert_id = ?
                """,
                (
                    created_at,
                    alert_id,
                ),
            )

        connection.commit()

    finally:
        connection.close()

    created_from = datetime.fromisoformat(
        "2026-08-20T14:00:00+09:00"
    )

    created_to = datetime.fromisoformat(
        "2026-08-20T15:00:00+09:00"
    )

    results = repository.search(
        limit=10,
        created_from=created_from,
        created_to=created_to,
    )

    assert [result.alert_id for result in results] == [start_saved.alert_id]

    from_only_results = repository.search(
        limit=10,
        created_from=created_from,
    )

    assert [result.alert_id for result in from_only_results] == [end_saved.alert_id, start_saved.alert_id]

    to_only_results = repository.search(
        limit=10,
        created_to=created_to,
    )

    assert [result.alert_id for result in to_only_results] == [start_saved.alert_id, before_saved.alert_id]

def test_search_combines_filters(repository):
    warn_required_event = DecisionEvent(
        event_id="event_search_and_warn_required",
        decision_type="approve",
        confidence=0.3,
        latency_ms=800,
        model_version=" ",
        error_code=None,
        metadata={
            "source": "repository_search_and_test",
        },
    )

    warn_required_alert = evaluate_event(warn_required_event)

    assert warn_required_alert.level == "WARN"
    assert warn_required_alert.human_required is True

    warn_required_saved = repository.save(
        alert=warn_required_alert,
        trace_id="trace_search_and_warn_required",
    )

    warn_not_required_event = DecisionEvent(
        event_id="event_search_and_warn_not_required",
        decision_type="approve",
        confidence=0.3,
        latency_ms=800,
        model_version="v1",
        error_code=None,
        metadata={
            "source": "repository_search_and_test",
        },
    )

    warn_not_required_alert = evaluate_event(warn_not_required_event)

    assert warn_not_required_alert.level == "WARN"
    assert warn_not_required_alert.human_required is False

    warn_not_required_saved = repository.save(
        alert=warn_not_required_alert,
        trace_id=(
            "trace_search_and_warn_not_required"
        ),
    )

    critical_required_event = DecisionEvent(
        event_id="event_search_and_critical_required",
        decision_type="approve",
        confidence=0.3,
        latency_ms=2800,
        model_version="v1",
        error_code=None,
        metadata={
            "source": "repository_search_and_test",
        },
    )

    critical_required_alert = evaluate_event(critical_required_event)

    assert critical_required_alert.level == "CRITICAL"
    assert critical_required_alert.human_required is True

    critical_required_saved = repository.save(
        alert=critical_required_alert,
        trace_id=(
            "trace_search_and_critical_required"
        ),
    )

    results = repository.search(
        limit=10,
        level="WARN",
        human_required=True,
    )

    result_ids = [result.alert_id for result in results]

    assert result_ids == [warn_required_saved.alert_id]
    assert warn_not_required_saved.alert_id not in result_ids
    assert critical_required_saved.alert_id not in result_ids

def test_search_rejects_invalid_level(repository):
    with pytest.raises(
        ValueError,
        match="level must be INFO, WARN, CRITICAL",
    ):
        repository.search(
            limit=5,
            level="UNKNOWN",
        )

def test_search_rejects_datetime_without_timezone(repository):
    naive_datetime = datetime.fromisoformat(
        "2026-08-20T05:00:00"
    )

    assert naive_datetime.tzinfo is None

    with pytest.raises(
        ValueError,
        match=(
            "created_from and created_to "
            "must include timezone"
        ),
    ):
        repository.search(
            limit=5,
            created_from=naive_datetime,
        )

    with pytest.raises(
        ValueError,
        match=(
            "created_from and created_to "
            "must include timezone"
        ),
    ):
        repository.search(
            limit=5,
            created_to=naive_datetime,
        )

def test_search_rejects_invalid_created_at_range(repository):
    same_time = datetime.fromisoformat(
        "2026-08-20T05:00:00+00:00"
    )

    earlier_time = datetime.fromisoformat(
        "2026-08-20T04:00:00+00:00"
    )

    later_time = datetime.fromisoformat(
        "2026-08-20T06:00:00+00:00"
    )

    invalid_ranges = [
        (same_time, same_time),
        (later_time, earlier_time)
    ]

    for created_from, created_to in invalid_ranges:
        with pytest.raises(
            ValueError,
            match=(
                "created_from must be earlier than created_to"
            ),
        ):
            repository.search(
                limit=5,
                created_from=created_from,
                created_to=created_to
            )

def test_search_uses_created_at_and_alert_id_cursor(repository, test_db_path):
    event = DecisionEvent(
        event_id="event_repository_cursor",
        decision_type="approve",
        confidence=0.95,
        latency_ms=300,
        model_version="v1",
        error_code=None,
        metadata={
            "source": "repository_cursor_test",
        },
    )

    alert = evaluate_event(event)

    saved_alerts = [
        repository.save(
            alert=alert,
            trace_id=f"trace_repository_cursor_{number}",
        )
        for number in range(1, 5)
    ]

    connection = create_connection(test_db_path)

    try:
        timestamps = [
            (
                "2026-08-20T06:00:00+00:00",
                saved_alerts[0].alert_id,
            ),
            (
                "2026-08-20T04:00:00+00:00",
                saved_alerts[1].alert_id,
            ),
            (
                "2026-08-20T05:00:00+00:00",
                saved_alerts[2].alert_id,
            ),
            (
                "2026-08-20T05:00:00+00:00",
                saved_alerts[3].alert_id,
            ),
        ]

        for created_at, alert_id in timestamps:
            connection.execute(
                """
                UPDATE alerts
                SET created_at = ?
                WHERE alert_id = ?
                """,
                (created_at,alert_id)
            )

        connection.commit()

    finally:
        connection.close()

    first_page = repository.search(limit=2)

    assert [result.alert_id for result in first_page] == [saved_alerts[0].alert_id, saved_alerts[3].alert_id]

    second_page = repository.search(
        limit=2,
        cursor_created_at=datetime.fromisoformat("2026-08-20T05:00:00+00:00"),
        cursor_alert_id=saved_alerts[3].alert_id,
    )

    assert [result.alert_id for result in second_page] == [saved_alerts[2].alert_id, saved_alerts[1].alert_id]

def test_search_rejects_partial_cursor(repository):
    cursor_created_at = datetime.fromisoformat(
        "2026-08-20T05:00:00+00:00"
    )

    with pytest.raises(
        ValueError,
        match="cursor_created_at and cursor_alert_id must be provided together"
    ):
        repository.search(
            limit=2,
            cursor_created_at=cursor_created_at,
        )

    with pytest.raises(
        ValueError,
        match="cursor_created_at and cursor_alert_id must be provided together"):
        repository.search(
            limit=2,
            cursor_alert_id=4,
        )

def test_search_rejects_cursor_datetime_without_timezone(repository):
    cursor_created_at = datetime.fromisoformat(
        "2026-08-20T05:00:00"
    )

    with pytest.raises(
        ValueError,
        match="cursor_created_at must include timezone",
    ):
        repository.search(
            limit=2,
            cursor_created_at=cursor_created_at,
            cursor_alert_id=4,
        )

def test_search_rejects_non_positive_cursor_alert_id(repository):
    cursor_created_at = datetime.fromisoformat(
        "2026-08-20T05:00:00+00:00"
    )

    for invalid_cursor_alert_id in (0, -1):
        with pytest.raises(
            ValueError,
            match="cursor_alert_id must be greater than 0"
        ):
            repository.search(
                limit=2,
                cursor_created_at=cursor_created_at,
                cursor_alert_id=invalid_cursor_alert_id,
            )

def test_search_combines_level_filter_and_cursor(repository, test_db_path):
    info_event = DecisionEvent(
        event_id="event_search_cursor_info",
        decision_type="approve",
        confidence=0.95,
        latency_ms=300,
        model_version="v1",
        error_code=None,
        metadata={
            "source": "repository_cursor_filter_test",
        }
    )

    info_alert = evaluate_event(info_event)

    assert info_alert.level == "INFO"

    critical_event = DecisionEvent(
        event_id="event_search_cursor_critical",
        decision_type="approve",
        confidence=0.3,
        latency_ms=2800,
        model_version="v1",
        error_code=None,
        metadata={
            "source": "repository_cursor_filter_test",
        },
    )

    critical_alert = evaluate_event(critical_event)

    assert critical_alert.level == "CRITICAL"

    info_old_saved = repository.save(
        alert=info_alert,
        trace_id="trace_cursor_filter_info_old",
    )

    critical_saved = repository.save(
        alert=critical_alert,
        trace_id="trace_cursor_filter_critical",
    )

    info_cursor_saved = repository.save(
        alert=info_alert,
        trace_id="trace_cursor_filter_info_cursor",
    )

    info_new_saved = repository.save(
        alert=info_alert,
        trace_id="trace_cursor_filter_info_new",
    )

    connection = create_connection(test_db_path)

    try:
        timestamps = [
            (
                "2026-08-20T04:00:00+00:00",
                info_old_saved.alert_id,
            ),
            (
                "2026-08-20T04:30:00+00:00",
                critical_saved.alert_id,
            ),
            (
                "2026-08-20T05:00:00+00:00",
                info_cursor_saved.alert_id,
            ),
            (
                "2026-08-20T06:00:00+00:00",
                info_new_saved.alert_id,
            ),
        ]

        for created_at, alert_id in timestamps:
            connection.execute(
                """
                UPDATE alerts
                SET created_at = ?
                WHERE alert_id = ?
                """,
                (
                    created_at,
                    alert_id,
                ),
            )

        connection.commit()

    finally:
        connection.close()

    first_page = repository.search(
        limit=2,
        level="INFO",
    )

    assert [result.alert_id for result in first_page] == [info_new_saved.alert_id, info_cursor_saved.alert_id]

    second_page = repository.search(
        limit=2,
        level="INFO",
        cursor_created_at=datetime.fromisoformat(
            "2026-08-20T05:00:00+00:00"
        ),
        cursor_alert_id=info_cursor_saved.alert_id,
    )

    second_page_ids = [result.alert_id for result in second_page]

    assert second_page_ids == [info_old_saved.alert_id]

    assert critical_saved.alert_id not in second_page_ids