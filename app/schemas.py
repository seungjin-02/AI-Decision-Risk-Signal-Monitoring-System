from typing import Any

from pydantic import BaseModel, Field

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