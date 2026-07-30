import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from app.db.connection import create_connection
from core.step09_AlertOutput import AlertOutput

@dataclass(frozen=True)
class SavedAlert:
    alert_id: int
    created_at: str

class AlertRepository:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = db_path

    def save(self, alert: AlertOutput, trace_id: str) -> SavedAlert:
        if not trace_id.strip():
            raise ValueError("trace_id must not be blank")

        created_at = datetime.now(timezone.utc).isoformat()
        connection = create_connection(self.db_path)

        try:
            cursor = connection.execute(
                """
                INSERT INTO alerts (
                    trace_id,
                    event_id,
                    level,
                    risk_score,
                    uncertainty_score,
                    human_required,
                    reason_summary,
                    metadata,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    trace_id,
                    alert.event_id,
                    alert.level,
                    alert.risk_score,
                    alert.uncertainty_score,
                    int(alert.human_required),
                    alert.reason_summary,
                    json.dumps(
                        alert.metadata,
                        ensure_ascii=False,
                        sort_keys=True,
                    ),
                    created_at,
                ),
            )

            alert_id = cursor.lastrowid

            if alert_id is None:
                raise RuntimeError("Failed to create alert_id")

            for signal in alert.signals:
                connection.execute(
                    """
                    INSERT INTO alert_signals (
                        alert_id,
                        rule_id,
                        category,
                        score,
                        reason,
                        evidence,
                        is_critical_override,
                        metadata
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        alert_id,
                        signal.rule_id,
                        signal.category,
                        signal.score,
                        signal.reason,
                        json.dumps(
                            signal.evidence,
                            ensure_ascii=False,
                            sort_keys=True,
                        ),
                        int(signal.is_critical_override),
                        json.dumps(
                            signal.metadata,
                            ensure_ascii=False,
                            sort_keys=True,
                        ),
                    ),
                )

            for action_order, action_code in enumerate(alert.recommended_actions):
                connection.execute(
                    """
                    INSERT INTO alert_actions (
                        alert_id,
                        action_code,
                        action_order
                    )
                    VALUES (?, ?, ?)
                    """,
                    (
                        alert_id,
                        action_code,
                        action_order,
                    ),
                )

            connection.commit()

            return SavedAlert(
                alert_id=alert_id,
                created_at=created_at,
            )

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()