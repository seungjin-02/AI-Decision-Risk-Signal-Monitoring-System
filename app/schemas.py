from typing import Any
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime

class EvaluateRequest(BaseModel):
    event_id: str
    decision_type: str | None = None
    confidence: float | None = None
    latency_ms: int | None = None
    model_version: str | None = None
    error_code: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

class ErrorResponse(BaseModel):
    trace_id: str
    error_type: str
    message: str
    details: list[dict[str, Any]] = Field(default_factory=list)

class SignalResponse(BaseModel):
    # 딕셔너리 키가 아니라 객체 속성(signal.rule_id 등)에서 필드 값을 읽는다.
    # core의 Signal dataclass를 SignalResponse로 검증·변환하기 위한 설정이다.
    model_config = ConfigDict(from_attributes=True)

    rule_id: str
    category: str
    score: int
    reason: str
    evidence: dict[str, Any]
    is_critical_override: bool
    metadata: dict[str, Any]

class EvaluateResponse(BaseModel):
    trace_id: str
    event_id: str
    level: str
    risk_score: int
    uncertainty_score: int
    human_required: bool
    recommended_actions: list[str]
    reason_summary: str
    signals: list[SignalResponse]
    metadata: dict[str, Any]

class AlertDetailResponse(BaseModel):
    # 딕셔너리 키가 아니라 객체 속성(detail.alert_id 등)에서 필드 값을 읽는다.
    # Repository의 AlertDetail dataclass를 API 응답 모델로 검증·변환하기 위한 설정이다.
    model_config = ConfigDict(from_attributes=True)

    alert_id: int
    trace_id: str
    created_at: datetime
    event_id: str
    level: str
    risk_score: int
    uncertainty_score: int
    human_required: bool
    recommended_actions: list[str]
    reason_summary: str
    signals: list[SignalResponse]
    metadata: dict[str, Any]


class AlertListResponse(BaseModel):
    count: int
    limit: int
    alerts: list[AlertDetailResponse]