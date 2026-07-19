# API Contract

이 문서는 `AI Decision Risk Signal Monitoring System`의 FastAPI API 계약을 정의한다.

API layer는 외부 요청과 응답 형식을 고정하고 core evaluation pipeline을 HTTP 환경에서 안전하게 호출하는 역할을 한다.

현재 API는 다음 endpoint를 제공한다.

```text
GET  /health
POST /evaluate
```

---

## 1. API Design Goals

이 API의 목표는 단순히 core pipeline을 외부에서 호출하는 것이 아니다.

핵심 목표는 다음과 같다.

- 외부 JSON request를 명확한 schema로 검증한다.
- API validation error와 core validation error를 분리한다.
- 모든 응답에 trace_id를 포함한다.
- response body의 trace_id와 X-Trace-Id header를 일치시킨다.
- core 내부 객체를 API response에 그대로 노출하지 않는다.
- risk, uncertainty, critical override, human_required를 구조화된 응답으로 제공한다.

API layer는 판단을 수행하지 않는다. 판단은 core evaluation pipeline에서 수행된다.

---

## 2. API Layer Responsibilities

API layer의 책임은 다음과 같다.

- HTTP endpoint 제공
- request body schema validation
- response schema contract 제공
- trace_id 생성 및 전파
- exception handling
- status code mapping
- core result를 external API response로 변환

API layer가 직접 수행하지 않는 것:

- risk rule 판단
- uncertainty 계산
- critical override 판단
- final_level 결정
- human_required 결정
- action recommendation 생성

---

## 3. Trace ID Contract

모든 API response는 `trace_id`를 포함한다.

또한 모든 response header에는 `X-Trace-Id`가 포함된다.

```text
response.body.trace_id == response.headers["X-Trace-Id"]
```

이 계약은 정상 응답과 에러 응답 모두에 적용된다.

목적:

- 요청 단위 추적성 확보
- API test에서 response contract 검증 가능
- 향후 logging / observability 확장 기반 제공

---

## 4. GET /health

### Purpose

`GET /health`는 API 서버가 정상적으로 응답 가능한지 확인하는 endpoint이다.

이 endpoint는 core evaluation pipeline을 호출하지 않는다.

---

### Request

```http
GET /health
```

Request body는 필요하지 않다.

---

### Success Response

Status Code:

```text
200 OK
```

Response body:

```json
{
  "trace_id": "generated-trace-id",
  "status": "ok"
}
```

Response header:

```http
X-Trace-Id: generated-trace-id
```

Contract:

```text
body.trace_id == header.X-Trace-Id
status == "ok"
```

---

## 5. POST /evaluate

### Purpose

`POST /evaluate`는 하나의 AI decision event를 평가하고 위험 신호와 불확실성, 인간 검토 필요 여부를 구조화된 alert response로 반환한다.

---

### Request

```http
POST /evaluate
Content-Type: application/json
```

Request body는 `EvaluateRequest` schema를 따른다.

```json
{
  "event_id": "evt_demo_001",
  "decision_type": "approve",
  "confidence": 0.3,
  "latency_ms": 2800,
  "model_version": null,
  "error_code": null,
  "metadata": {
    "source": "demo"
  }
}
```

---

## 6. EvaluateRequest Schema

| Field | Type | Required | Description |
|---|---|---:|---|
| `event_id` | `str` | Yes | 이벤트 식별자 |
| `decision_type` | `str \| null` | No | AI 또는 시스템의 판단 유형 |
| `confidence` | `float \| null` | No | 판단 confidence score |
| `latency_ms` | `int \| null` | No | 응답 지연 시간 |
| `model_version` | `str \| null` | No | 모델 버전 |
| `error_code` | `str \| null` | No | 시스템 오류 코드 |
| `metadata` | `object` | No | 추가 메타데이터 |

현재 `metadata`의 기본값은 빈 object이다.

```json
{
  "metadata": {}
}
```

---

## 7. EvaluateResponse Schema

정상 평가 응답은 `EvaluateResponse` schema를 따른다.

| Field | Type | Description |
|---|---|---|
| `trace_id` | `str` | 요청 추적 ID |
| `event_id` | `str` | 평가된 이벤트 ID |
| `level` | `str` | 최종 해석 level |
| `risk_score` | `int` | risk category signal의 score 합 |
| `uncertainty_score` | `int` | uncertainty category signal의 score 합 |
| `human_required` | `bool` | 인간 검토 필요 여부 |
| `recommended_actions` | `list[str]` | 운영 행동 후보 |
| `reason_summary` | `str` | gate/action 판단 요약 |
| `signals` | `list[SignalResponse]` | 발동된 signal 목록 |
| `metadata` | `object` | 입력 metadata |

---

## 8. SignalResponse Schema

각 signal은 발동된 rule을 외부 응답 형식으로 구조화한 것이다.

| Field | Type | Description |
|---|---|---|
| `rule_id` | `str` | 발동된 rule ID |
| `category` | `str` | signal category |
| `score` | `int` | signal score |
| `reason` | `str` | signal 발생 이유 |
| `evidence` | `object` | 판단 근거 필드 |
| `is_critical_override` | `bool` | critical override 여부 |
| `metadata` | `object` | rule-level metadata |

예시:

```json
{
  "rule_id": "approve_confidence_low",
  "category": "risk",
  "score": 3,
  "reason": "approve decision with low confidence",
  "evidence": {
    "decision_type": "approve",
    "confidence": 0.3
  },
  "is_critical_override": false,
  "metadata": {}
}
```

---

## 9. Normal Success Example

### Request

```json
{
  "event_id": "evt_demo_high_risk_uncertainty",
  "decision_type": "approve",
  "confidence": 0.3,
  "latency_ms": 2800,
  "model_version": null,
  "error_code": null,
  "metadata": {
    "source": "demo"
  }
}
```

---

### Response

Status Code:

```text
200 OK
```

Response body:

```json
{
  "trace_id": "generated-trace-id",
  "event_id": "evt_demo_high_risk_uncertainty",
  "level": "WARN",
  "risk_score": 5,
  "uncertainty_score": 1,
  "human_required": true,
  "recommended_actions": [
    "human_review_required",
    "review_missing_or_incomplete_information",
    "monitor_closely"
  ],
  "reason_summary": "high risk score detected, but uncertainty prevents automatic critical finalization",
  "signals": [
    {
      "rule_id": "approve_confidence_low",
      "category": "risk",
      "score": 3,
      "reason": "approve decision with low confidence",
      "evidence": {
        "decision_type": "approve",
        "confidence": 0.3
      },
      "is_critical_override": false,
      "metadata": {}
    },
    {
      "rule_id": "latency_high",
      "category": "risk",
      "score": 2,
      "reason": "response latency exceeded threshold",
      "evidence": {
        "latency_ms": 2800
      },
      "is_critical_override": false,
      "metadata": {}
    },
    {
      "rule_id": "missing_model_version",
      "category": "uncertainty",
      "score": 1,
      "reason": "model_version field is missing",
      "evidence": {
        "model_version": null
      },
      "is_critical_override": false,
      "metadata": {}
    }
  ],
  "metadata": {
    "source": "demo"
  }
}
```

---

## 10. Critical Override Example

### Request

```json
{
  "event_id": "evt_demo_failure_override",
  "decision_type": "approve",
  "confidence": 0.9,
  "latency_ms": 300,
  "model_version": "v1",
  "error_code": "gateway_failure",
  "metadata": {}
}
```

---

### Response Summary

```text
level: CRITICAL
risk_score: 0
uncertainty_score: 0
human_required: true
```

Expected signal:

```json
{
  "rule_id": "evaluation_integrity_override",
  "category": "failure",
  "score": 0,
  "reason": "evaluation integrity failure requires critical review",
  "evidence": {
    "error_code": "gateway_failure"
  },
  "is_critical_override": true,
  "metadata": {
    "failure_type": "system_error",
    "score_contribution": "none",
    "override_type": "critical"
  }
}
```

Expected actions:

```text
human_review_required
immediate_investigation
escalate_incident
```

---

## 11. ErrorResponse Schema

에러 응답은 `ErrorResponse` schema를 따른다.

| Field | Type | Description |
|---|---|---|
| `trace_id` | `str` | 요청 추적 ID |
| `error_type` | `str` | 에러 분류 |
| `message` | `str` | 에러 메시지 |
| `details` | `list[object]` | 상세 에러 정보 |

예시:

```json
{
  "trace_id": "generated-trace-id",
  "error_type": "api_validation_error",
  "message": "Request format or type is invalid.",
  "details": []
}
```

---

## 12. Status Code Policy

| Status Code | Error Type | Meaning |
|---:|---|---|
| 200 | - | 정상 평가 완료 |
| 400 | `core_validation_error` | JSON 형식은 맞지만 core domain validation 위반 |
| 422 | `api_validation_error` | request body 형식 또는 타입 오류 |
| 500 | `system_error` | 예상하지 못한 서버 내부 오류 |

---

## 13. 400 Core Validation Error

### Meaning

400은 request body가 API schema는 통과했지만 core domain validation에서 거부된 경우이다.

즉 JSON 구조와 타입은 맞지만 시스템의 domain rule에 맞지 않는 입력이다.

---

### Examples

```text
confidence = 1.5
latency_ms = -1
decision_type = "pending"
event_id = "   "
```

---

### Response

Status Code:

```text
400 Bad Request
```

Response body:

```json
{
  "trace_id": "generated-trace-id",
  "error_type": "core_validation_error",
  "message": "core validation error message",
  "details": []
}
```

---

## 14. 422 API Validation Error

### Meaning

422는 request body가 API schema 자체를 통과하지 못한 경우이다.

즉 core pipeline으로 들어가기 전에 FastAPI/Pydantic layer에서 차단된다.

---

### Examples

```text
event_id = 1234
confidence = "not-a-number"
latency_ms = "slow"
metadata = "not-an-object"
```

---

### Response

Status Code:

```text
422 Unprocessable Entity
```

Response body:

```json
{
  "trace_id": "generated-trace-id",
  "error_type": "api_validation_error",
  "message": "Request format or type is invalid.",
  "details": [
    {
      "loc": ["body", "field_name"],
      "msg": "error message",
      "type": "error_type"
    }
  ]
}
```

---

## 15. 500 System Error

### Meaning

500은 예상하지 못한 서버 내부 오류가 발생한 경우이다.

이 에러는 정상적인 validation 실패가 아니다.

---

### Response

Status Code:

```text
500 Internal Server Error
```

Response body:

```json
{
  "trace_id": "generated-trace-id",
  "error_type": "system_error",
  "message": "Unexpected internal server error.",
  "details": []
}
```

---

## 16. API Validation vs Core Validation

이 시스템은 validation을 두 계층으로 나눈다.

```text
API validation
→ 요청 형식과 타입 검증

Core validation
→ domain rule 검증
```

구분 기준:

| Input | Layer | Status Code |
|---|---|---:|
| `confidence = "not-a-number"` | API validation | 422 |
| `confidence = 1.5` | Core validation | 400 |
| `latency_ms = "slow"` | API validation | 422 |
| `latency_ms = -1` | Core validation | 400 |
| `decision_type = "pending"` | Core validation | 400 |
| `event_id = "   "` | Core validation | 400 |
| `metadata = "not-an-object"` | API validation | 422 |

이 분리는 운영 관점에서 중요하다.

```text
422
→ 클라이언트가 request format/type을 잘못 보냄

400
→ request format은 맞지만 domain rule에 맞지 않음
```

---

## 17. Response Invariants

API response는 다음 invariant를 지켜야 한다.

- 모든 응답은 trace_id를 포함한다.
- 모든 응답은 X-Trace-Id header를 포함한다.
- response.body.trace_id == response.headers["X-Trace-Id"].
- 정상 응답은 EvaluateResponse schema를 따른다.
- 에러 응답은 ErrorResponse schema를 따른다.
- SignalResponse는 is_critical_override 필드를 사용한다.
-  API response는 내부 core object를 그대로 노출하지 않는다.
- failure signal은 risk_score에 합산되지 않는다.
- uncertainty signal은 risk_score에 합산되지 않는다.

---

## 18. Current Limitations

현재 API는 MVP 범위이다.

아직 포함되지 않은 것:

```text
- authentication
- authorization
- database persistence
- alert history query
- GET /alerts
- GET /alerts/{event_id}
- pagination
- filtering
- sorting
- production logging
- rate limiting
- deployment configuration
```
