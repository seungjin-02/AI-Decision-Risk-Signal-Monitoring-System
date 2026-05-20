# AI Decision Risk Signal Monitoring System (MVP 진행중)

AI 의사결정 과정에서 발생할 수 있는 **위험 신호(Risk Signal)** 와 **불확실성(Uncertainty)** 을 분리하고 시스템이 자동으로 판단을 확정해도 되는지 또는 인간 검토가 필요한지를 구조화하는 MVP 프로젝트입니다.

이 프로젝트는 AI의 결정을 자동 승인하거나 거절하는 시스템이 아닙니다.  
대신 AI 의사결정 결과를 그대로 신뢰하기 전에 위험 신호와 판단 제한 요소를 분리하여 **인간이 책임 있게 판단할 수 있는 구조**를 제공하는 것을 목표로 합니다.

---

## Executive Summary

기존의 단순 threshold 또는 score 기반 시스템은 위험과 불확실성을 하나의 결과로 압축하기 쉽습니다.

그러나 실제 운영 상황에서는 다음 요소가 분리되어야 합니다.

- 실제로 관측된 위험 신호
- 입력 누락 또는 해석 제한으로 인한 불확실성
- 시스템이 자동으로 판단을 확정할 수 있는지 여부
- 인간 검토가 필요한 조건

이 시스템은 다음 요소를 명확히 분리합니다.

```text
Risk Signal
→ 관측 가능한 위험 신호

Uncertainty
→ 판단을 제한하는 정보 부족 또는 추적성 부족

Human Required
→ 시스템이 자동 확정을 멈추고 인간 검토를 요구해야 하는 상태
```

핵심 목표는 최대 자동화가 아니라,  
**어디까지 시스템이 해석할 수 있고 어디서 인간 판단이 필요한지 명확히 드러내는 것**입니다.

---

## Problem Statement

AI 기반 의사결정 시스템이나 모니터링 시스템은 종종 내부 판단 결과를 단일 score, level, alert 형태로 압축합니다.

이 방식은 단순하고 빠르지만 다음과 같은 문제가 있습니다.

- 위험 신호와 불확실성이 구분되지 않음
- 입력 정보가 부족한 상황에서도 시스템이 판단을 확정한 것처럼 보일 수 있음
- 운영자가 결과의 근거를 확인하기 어려움
- 자동화된 판단과 인간 책임 사이의 경계가 모호해짐
- 단순 threshold 기반 판단이 실제 판단 가능성을 과대평가할 수 있음

예를 들어 같은 높은 risk score가 나오더라도 다음 두 상황은 다르게 처리되어야 합니다.

```text
1. 충분한 정보가 있는 상태에서 관측된 높은 위험
2. 입력 정보가 부족한 상태에서 관측된 높은 위험
```

두 경우 모두 위험 신호는 높을 수 있지만,  
두 번째 경우에는 시스템이 스스로 CRITICAL을 확정하는 것이 아니라 인간 검토를 요구해야 합니다.

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

### 3. HUMAN_REQUIRED는 실패가 아니라 설계된 결과이다

`human_required=True`는 시스템 실패가 아닙니다.

이는 다음을 의미합니다.

```text
현재 상황에서는 시스템이 자동으로 판단을 확정하지 않고 인간 검토가 필요하다.
```

즉 `human_required`는 fallback이 아니라 의도적으로 설계된 결과입니다.

---

### 4. Priority를 생성하지 않는다

이 시스템은 사건 간 처리 우선순위를 생성하지 않습니다.

`priority`는 시스템이 어떤 사건을 먼저 처리해야 하는지 판단하는 값으로 해석될 수 있습니다.  
이 프로젝트에서는 최종 처리 순서와 우선순위 판단을 인간 운영자의 책임으로 남깁니다.

대신 시스템은 단일 이벤트에 대해 필요한 운영 행동 후보만 제공합니다.

---

## System Architecture

```text
DecisionEvent
 → Validation
 → Normalization
 → Evaluation Context
 → Rule Evaluation
 → Signal Generation
 → Score Aggregation
 → Gate Interpretation
 → Action Generation
 → Alert Output
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

## Test Strategy

테스트는 세 가지 계층으로 구성되어 있습니다.

```text
tests/
  unit/
  integration/
  invariants/
```

### Unit Tests

각 pipeline step의 독립적인 책임을 검증합니다.

### Integration Tests

`DecisionEvent`가 전체 pipeline을 거쳐 `AlertOutput`으로 변환되는 흐름을 검증합니다.

### Invariant Tests

시스템의 핵심 설계 원칙이 깨지지 않도록 보호합니다.

예시:

```text
uncertainty는 risk_score에 직접 더해지지 않는다.
high-risk signal은 score가 아니라 override 조건으로 처리된다.
human_required는 final_level과 분리된다.
priority는 생성하지 않는다.
AlertOutput은 결과를 재계산하지 않고 조립만 한다.
```

---

## Repository Structure

```text
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
  unit/
    test_normalization.py
    test_validation.py
    test_evaluation_context.py
    test_rule_evaluation.py
    test_signal_generation.py
    test_score_aggregation.py
    test_gate_interpretation.py
    test_action_generation.py
    test_alert_output.py

  integration/
    test_pipeline_validation.py
    test_full_pipeline.py

  invariants/
    test_design_invariants.py

docs/
  decision-boundary.md
  design-decisions.md
  validation-policy.md
  test-strategy.md
```

---

## How to Run

```bash
python core/main.py
```

---

## How to Test

전체 테스트 실행:

```bash
pytest -v
```

단위 테스트 실행:

```bash
pytest tests/unit -v
```

통합 테스트 실행:

```bash
pytest tests/integration -v
```

설계 불변조건 테스트 실행:

```bash
pytest tests/invariants -v
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
- 동적 threshold 최적화
- 최대 자동화 추구

대신 다음을 수행합니다.

- 위험 신호 구조화
- 불확실성 분리
- 평가 제한 조건 기록
- 인간 검토 필요 여부 명시
- 자동 판단 경계 정의

---

## Current Scope

현재 버전은 MVP입니다.

주요 초점은 다음과 같습니다.

- 명확한 decision pipeline 구성
- validation과 rule evaluation 분리
- risk와 uncertainty 분리
- high-risk override 처리
- human_required 설계
- pytest 기반 unit / integration / invariant 테스트 구성

향후 확장 가능 영역은 다음과 같습니다.

- API 계층 추가
- request_id 기반 logging
- timeout / fallback 정책
- policy versioning
- 운영자 화면 또는 dashboard 연동
- 배포 및 관측성 강화

---

## Summary

이 프로젝트는 AI를 활용해 결정을 자동화하는 시스템이 아닙니다.

핵심은 다음 질문에 답하는 것입니다.

```text
AI 또는 시스템이 어디까지 해석할 수 있고 어디서 멈춰야 하는가?
```

따라서 이 프로젝트는 결론을 대신 내리는 것이 아니라 위험 신호와 불확실성을 분리하여 인간 판단이 필요한 지점을 명확히 구조화하는 시스템입니다.
