# AI Decision Risk Signal Monitoring System

AI 의사결정 과정에서 발생할 수 있는 **위험 신호(Risk Signal)**, **불확실성(Uncertainty)**, **인간 검토 필요 여부(Human Review Requirement)** 를 분리해 구조화하는 FastAPI 기반 MVP 프로젝트입니다.

이 프로젝트는 AI의 결정을 자동 승인하거나 거절하는 시스템이 아닙니다.
대신 AI 또는 자동화 시스템의 판단 결과를 그대로 신뢰하기 전에 어떤 위험 신호가 관측되었고 어떤 정보가 부족하며 어디서 인간 검토가 필요한지를 명확하게 드러내는 것을 목표로 합니다.

---

## Executive Summary

기존의 단순 threshold 또는 score 기반 시스템은 위험과 불확실성을 하나의 결과로 압축하기 쉽습니다.

그러나 실제 운영 상황에서는 다음 요소가 분리되어야 합니다.

- 실제로 관측된 위험 신호
- 입력 누락 또는 해석 제한으로 인한 불확실성
- 시스템이 자동으로 판단을 확정할 수 있는지 여부
- 인간 검토가 필요한 조건
- 시스템 오류 또는 평가 무결성 실패가 risk score로 위장되지 않는 구조

이 시스템은 다음 요소를 명확히 분리합니다.

```text
Risk Signal
→ 관측 가능한 위험 신호

Uncertainty
→ 판단에 필요한 정보가 부족하거나 결과를 재현·확인하기 어려운 상태

Critical Override
→ 시스템 오류 또는 평가 무결성 실패로 인해 점수와 별개로 즉시 인간 검토가 필요한 상태

Human Required
→ 시스템이 자동 확정을 멈추고 인간 검토를 요구해야 하는 상태
```

핵심 목표는 최대 자동화가 아니라 **어디까지 시스템이 해석할 수 있고 어디서 인간 판단이 필요한지 명확히 드러내는 것**입니다.

---

## Problem Statement

AI 기반 의사결정 시스템이나 모니터링 시스템은 종종 내부 판단 결과를 단일 score, level, alert 형태로 압축합니다.

이 방식은 단순하고 빠르지만 다음과 같은 문제가 있습니다.

- 위험 신호와 불확실성이 구분되지 않음
- 입력 정보가 부족한 상황에서도 시스템이 판단을 확정한 것처럼 보일 수 있음
- 시스템 오류가 일반 risk score로 섞여 해석될 수 있음
- 운영자가 결과의 근거를 확인하기 어려움
- 자동화된 판단과 인간 책임 사이의 경계가 모호해짐
- 단순 threshold 기반 판단이 실제 판단 가능성을 과대평가할 수 있음

예를 들어, 같은 높은 risk score가 나오더라도 다음 세 상황은 다르게 처리되어야 합니다.

```text
1. 충분한 정보가 있는 상태에서 관측된 높은 위험
2. 입력 정보가 부족한 상태에서 관측된 높은 위험
3. risk score와 무관하게 시스템 오류가 발생한 상태
```

이 시스템은 세 번째 경우를 risk score에 합산하지 않습니다.  
대신 `failure` category와 `is_critical_override=True` signal로 분리하여 처리합니다.

---

## Core Design Principles

### 1. AI는 판단 주체가 아니다

이 시스템은 최종 결정을 내리지 않습니다.

시스템은 다음을 수행하지 않습니다.

- 자동 승인
- 자동 거절
- 최종 판단 확정
- 사건 간 우선순위 결정
- 인간 판단 대체

대신 시스템은 판단에 필요한 구조를 제공합니다.

---

### 2. 위험과 불확실성을 분리한다

위험과 불확실성은 서로 다른 의미를 가집니다.

```text
risk_score
→ 실제로 관측된 위험 신호의 누적

uncertainty_score
→ 판단을 제한하는 정보 부족 또는 추적성 부족
```

불확실성은 위험을 직접 낮추거나 높이지 않습니다.

대신 시스템이 해당 판단을 자동으로 확정할 수 있는지에 영향을 줍니다.

---

### 3. Critical override는 risk score로 위장하지 않는다

시스템 오류, timeout, gateway failure와 같은 평가 무결성 실패는 일반 risk score에 합산하지 않습니다.

```text
failure signal
→ category = "failure"
→ score = 0
→ is_critical_override = True
```

즉 risk score가 0이어도 critical override가 발생하면 최종 level은 `CRITICAL`이 될 수 있습니다.

---

### 4. HUMAN_REQUIRED는 실패가 아니라 설계된 결과이다

`human_required=True`는 시스템 실패가 아닙니다.

이는 다음을 의미합니다.

```text
현재 상황에서는 시스템이 자동으로 판단을 확정하지 않고 인간 검토가 필요하다.
```

즉 `human_required`는 fallback이 아니라 의도적으로 설계된 결과입니다.

---

### 5. Priority를 생성하지 않는다

이 시스템은 사건 간 처리 우선순위를 생성하지 않습니다.

`priority`는 시스템이 어떤 사건을 먼저 처리해야 하는지 판단하는 값으로 해석될 수 있습니다.  
이 프로젝트에서는 최종 처리 순서와 우선순위 판단을 인간 운영자의 책임으로 남깁니다.

대신 시스템은 단일 이벤트에 대해 필요한 운영 행동 후보만 제공합니다.

---

## System Architecture

현재 시스템은 FastAPI API layer와 core evaluation pipeline으로 분리되어 있습니다.

```text
Client
  → FastAPI API Layer
  → Request Schema Validation
  → Trace ID Middleware
  → Evaluation Service
  → Core Evaluation Pipeline
  → API Response Mapping
  → JSON Response
```

### API Layer

API layer는 HTTP 요청과 응답 계약을 담당합니다.

```text
app/
  main.py
  schemas.py
  services/
    evaluation_service.py
  utils/
    trace.py
```

주요 책임은 다음과 같습니다.

- HTTP endpoint 제공
- request schema validation
- trace_id 생성 및 response header 전파
- API validation error와 core validation error 분리
- core 결과를 API response contract로 변환
- core layer가 HTTP/FastAPI에 의존하지 않도록 보호

---

### Core Pipeline

Core pipeline은 단일 `DecisionEvent`를 평가하여 `AlertOutput`을 생성합니다.

```text
DecisionEvent
 → validate_event
 → normalize_event
 → build_evaluation_context
 → evaluate_rule
 → build_signals
 → summarize_signals
 → interpret_gate
 → generate_action
 → build_alert_output
```

각 단계는 독립된 책임을 가집니다.

| 단계 | 역할 |
|---|---|
| Validation | 잘못된 입력을 rule 평가 전에 차단 |
| Normalization | 입력값을 내부 처리 가능한 형태로 정규화 |
| Evaluation Context | 누락 필드와 평가 제한 조건 기록 |
| Rule Evaluation | 사전에 정의된 규칙 평가 |
| Signal Generation | 발동된 규칙을 구조화된 signal로 변환 |
| Score Aggregation | risk score와 uncertainty score를 분리 집계 |
| Gate Interpretation | 최종 level과 human_required 여부 결정 |
| Action Generation | gate 결과와 signal 원인을 운영 행동으로 번역 |
| Alert Output | 최종 출력 조립 |

판단은 여러 단계에 흩어져 수행되지 않고 **Gate Interpretation 단계에서만 최종 해석됩니다.**

---

## API Contract

### Health Check

```http
GET /health
```

Response:

```json
{
  "trace_id": "generated-trace-id",
  "status": "ok"
}
```

---

### Evaluate Event

```http
POST /evaluate
```

Request:

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

Response:

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

## Error Policy

API layer와 core layer의 validation 책임은 분리되어 있습니다.

| Status Code | Error Type | 의미 |
|---|---|---|
| 200 | - | 정상 평가 완료 |
| 400 | `core_validation_error` | JSON 형식은 맞지만 domain rule을 위반 |
| 422 | `api_validation_error` | 요청 body의 타입 또는 형식이 API schema와 불일치 |
| 500 | `system_error` | 예상하지 못한 서버 내부 오류 |

예시:

```text
confidence = "not-a-number" → 422 api_validation_error
confidence = 1.5 → 400 core_validation_error

latency_ms = "slow" → 422 api_validation_error
latency_ms = -1 → 400 core_validation_error

decision_type = "pending" → 400 core_validation_error
event_id = "   " → 400 core_validation_error
metadata = "not-an-object" → 422 api_validation_error
```

모든 API response는 `trace_id`를 포함하며, response body의 `trace_id`와 header의 `X-Trace-Id`는 동일해야 합니다.

---

## Example Flow

### Input

```json
{
  "event_id": "evt_demo_high_risk_uncertainty",
  "decision_type": "approve",
  "confidence": 0.3,
  "latency_ms": 2800,
  "model_version": null,
  "error_code": null
}
```

### Interpretation

```text
approve + low confidence
→ risk signal

high latency
→ risk signal

missing model_version
→ uncertainty signal
```

### Output Summary

```text
level: WARN
risk_score: 5
uncertainty_score: 1
human_required: true

recommended_actions:
  - human_review_required
  - review_missing_or_incomplete_information
  - monitor_closely
```

이 예시는 이 프로젝트의 핵심 설계를 보여줍니다.

```text
위험 신호는 높지만 불확실성으로 인해 시스템이 CRITICAL을 자동 확정하지 않고 인간 검토를 요구한다.
```

---

## Critical Override Example

### Input

```json
{
  "event_id": "evt_demo_failure_override",
  "decision_type": "approve",
  "confidence": 0.9,
  "latency_ms": 300,
  "model_version": "v1",
  "error_code": "gateway_failure"
}
```

### Output Summary

```text
level: CRITICAL
risk_score: 0
uncertainty_score: 0
human_required: true

signal:
  rule_id: evaluation_integrity_override
  category: failure
  score: 0
  is_critical_override: true

recommended_actions:
  - human_review_required
  - immediate_investigation
  - escalate_incident
```

이 케이스는 system failure를 risk score로 위장하지 않고, 별도의 critical override path로 처리한다는 점을 보여줍니다.

---

## Test Strategy

테스트는 네 가지 계층으로 구성되어 있습니다.

```text
tests/
  Unit_Test/
  Integration_Test/
  Design_Invariant_Test/
  API_Test/
```

### Unit Tests

각 core pipeline step의 독립적인 책임을 검증합니다.

검증 대상 예시:

- normalization
- event validation
- evaluation context
- rule evaluation
- signal generation
- score aggregation
- gate interpretation
- action generation
- alert output

---

### Integration Tests

`DecisionEvent`가 전체 core pipeline을 거쳐 `AlertOutput`으로 변환되는 흐름을 검증합니다.

검증 대상 예시:

- 정상 이벤트
- low confidence risk signal
- high latency risk signal
- high risk with uncertainty
- critical override
- invalid input validation stop

---

### Design Invariant Tests

시스템의 핵심 설계 원칙이 깨지지 않도록 보호합니다.

예시:

- uncertainty는 risk_score에 직접 더해지지 않는다.
- failure signal은 risk_score에 합산되지 않는다.
- critical override는 score가 아니라 override flag로 처리된다.
- human_required는 final_level과 분리된다.
- AlertOutput은 결과를 재계산하지 않고 조립만 한다.

---

### API Tests

FastAPI 계층의 외부 계약을 검증합니다.

검증 대상 예시:

- `GET /health`
- `POST /evaluate`
- success response contract
- signal response schema
- error response schema
- 400 core validation error
- 422 API validation error
- trace_id body/header consistency
- internal core object가 API response에 노출되지 않는지 여부

---

## Repository Structure

```text
app/
  main.py
  schemas.py
  services/
    evaluation_service.py
  utils/
    trace.py

core/
  main.py
  event_validation.py
  step01_DecisionEvent.py
  step02_NormalizedEvent.py
  step03_EvaluationContext.py
  step04_RuleEvaluation.py
  step05_SignalGeneration.py
  step06_ScoreAggregation.py
  step07_GateInterpretation.py
  step08_ActionGeneration.py
  step09_AlertOutput.py

tests/
  Unit_Test/
    test_normalization.py
    test_validation.py
    test_evaluation_context.py
    test_rule_evaluation.py
    test_signal_generation.py
    test_score_aggregation.py
    test_gate_interpretation.py
    test_action_generation.py
    test_alert_output.py

  Integration_Test/
    test_pipeline_validation.py
    test_full_pipeline.py

  Design_Invariant_Test/
    test_design_invariants.py

  API_Test/
    test_evaluate_endpoint.py
    test_api_validation.py
    test_core_validation_error.py
    test_trace_id_response.py
    test_api_response_constraints.py
    test_health_endpoint.py

docs/
  architecture.md
  decision-boundary.md
  validation-policy.md
  test-strategy.md
```

---

## How to Run

### Run Core Pipeline Directly

```bash
python core/main.py
```

### Run FastAPI Server

```bash
uvicorn app.main:app --reload
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

Evaluate event:

```bash
curl -X POST http://127.0.0.1:8000/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "evt_demo_001",
    "decision_type": "approve",
    "confidence": 0.3,
    "latency_ms": 2800,
    "model_version": null,
    "error_code": null,
    "metadata": {
      "source": "curl_demo"
    }
  }'
```

---

## How to Test

전체 테스트 실행:

```bash
python -m pytest -v
```

Unit tests:

```bash
python -m pytest tests/Unit_Test -v
```

Integration tests:

```bash
python -m pytest tests/Integration_Test -v
```

Design invariant tests:

```bash
python -m pytest tests/Design_Invariant_Test -v
```

API tests:

```bash
python -m pytest tests/API_Test -v
```

---

## Documentation

자세한 설계 설명은 아래 문서에서 확인할 수 있습니다.

- [Architecture](docs/architecture.md)
- [Decision Boundary](docs/decision-boundary.md)
- [Validation Policy](docs/validation-policy.md)
- [Test Strategy](docs/test-strategy.md)

---

## What This System Does NOT Do

이 시스템은 다음을 하지 않습니다.

- 자동 승인 / 자동 거절
- 최종 의사결정 대체
- 사건 간 priority 생성
- 불확실성을 risk score에 숨기기
- system failure를 risk score에 합산하기
- 동적 threshold 최적화
- 사용자 인증 / 권한 관리
- DB 기반 alert 저장
- 운영자 dashboard 제공
- 배포 환경 제공

대신 다음을 수행합니다.

- 위험 신호 구조화
- 불확실성 분리
- 평가 제한 조건 기록
- critical override 분리
- 인간 검토 필요 여부 명시
- 자동 판단 경계 정의
- API response contract 제공
- trace_id 기반 요청 추적성 제공

---

## Current Scope

현재 구현된 범위는 다음과 같습니다.

```text
Completed:
- Core decision evaluation pipeline
- Event validation
- Normalization
- Rule evaluation
- Signal generation
- Risk / uncertainty score separation
- Critical override handling
- Gate interpretation
- Action recommendation
- Alert output construction
- FastAPI API layer
- /health endpoint
- /evaluate endpoint
- trace_id middleware
- API response schema
- API error handling
- Unit tests
- Integration tests
- Design invariant tests
- API tests
```

현재 구현되지 않은 범위는 다음과 같습니다.

```text
Not Yet Implemented:
- Database persistence
- Alert history API
- GET /alerts
- GET /alerts/{event_id}
- Authentication / authorization
- Dashboard
- Deployment pipeline
- Observability stack
```

---

## Summary

이 프로젝트는 AI를 활용해 결정을 자동화하는 시스템이 아닙니다.

핵심은 다음 질문에 답하는 것입니다.

```text
AI 또는 시스템이 어디까지 해석할 수 있고 어디서 멈춰야 하는가?
```

따라서 이 프로젝트는 결론을 대신 내리는 것이 아니라 위험 신호와 불확실성을 분리하고 인간 판단이 필요한 지점을 명확히 구조화하는 시스템입니다.