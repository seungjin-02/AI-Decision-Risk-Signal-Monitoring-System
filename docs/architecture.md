# Architecture

이 문서는 `AI Decision Risk Signal Monitoring System`의 전체 구조와 파이프라인 흐름을 설명한다.

현재 버전은 실제 운영 배포용 완성 시스템이 아니라 AI 의사결정 이벤트를 입력받아 위험 신호, 불확실성, 인간 검토 필요 여부를 구조화하는 **rule-based MVP**이다.

---

## 1. Architecture Overview

이 시스템은 하나의 이벤트가 여러 단계를 거쳐 최종 `AlertOutput`으로 변환되는 pipeline 구조를 가진다.

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

각 단계는 독립된 책임을 가지며, 이전 단계의 결과를 받아 다음 단계로 전달한다.

이 구조의 핵심은 다음과 같다.

```text
1. 잘못된 입력은 rule 평가 전에 차단한다.
2. risk와 uncertainty는 분리해서 계산한다.
3. 최종 해석은 Gate Interpretation에서만 수행한다.
4. Action Generation은 판단을 다시 하지 않고 운영 행동으로 번역한다.
5. Alert Output은 결과를 재계산하지 않고 조립만 한다.
```

---

## 2. Main Entry Point

전체 pipeline의 진입점은 `core/main.py`의 `evaluate_event()` 함수이다.

```text
core/main.py
```

`evaluate_event()`는 다음 순서로 이벤트를 처리한다.

```text
1. validate_event(event)
2. normalize_event(event)
3. build_evaluation_context(normalized)
4. evaluate_rule(normalized, context)
5. build_signals(evaluations, normalized)
6. aggregate_scores(signals)
7. derive_gate_inputs(signals, score_summary)
8. interpret_gate(gate_inputs)
9. generate_action(decision, signals)
10. build_alert_output(...)
```

이 함수는 각 step을 연결하는 조립 역할만 수행한다.

`main.py`가 직접 수행하지 않는 것:

```text
- rule 조건 판단
- score 계산
- final_level 결정
- human_required 결정
- action 생성 로직
```

이러한 책임은 각각의 step 파일로 분리되어 있다.

---

## 3. Pipeline Steps

### 3-1 Step 01 — DecisionEvent

```text
core/step01_DecisionEvent.py
```

`DecisionEvent`는 외부에서 들어오는 의사결정 이벤트를 표현한다.

주요 필드:

```text
event_id
decision_type
confidence
latency_ms
model_version
error_code
metadata
```

이 단계는 판단을 수행하지 않는다.  
입력 이벤트의 기본 구조만 정의한다.

---

### 3-2 Validation

```text
core/event_validation.py
```

Validation 단계는 잘못된 입력이 pipeline 내부로 들어오는 것을 막는다.

예를 들어 다음 값들은 invalid input으로 처리된다.

```text
confidence = 1.5
confidence = -0.1
confidence = "abc"
latency_ms = -100
decision_type = "approvee"
event_id = ""
metadata = "not-a-dict"
```

Validation 실패 시 pipeline은 중단되고 `ValueError`가 발생한다.

```text
invalid input
→ ValueError
→ rule evaluation으로 진행하지 않음
```

이 단계의 목적은 invalid input이 risk나 uncertainty로 잘못 해석되는 것을 방지하는 것이다.

---

### 3-3 Step 02 — Normalization

```text
core/step02_NormalizedEvent.py
```

Normalization 단계는 입력값을 내부 처리에 적합한 형태로 변환한다.

예시:

```text
decision_type=" APPROVE "
→ "approve"

confidence="0.52"
→ 0.52

latency_ms="2800"
→ 2800
```

Normalization은 값을 정리할 뿐, 위험 판단을 수행하지 않는다.

---

### 3-4 Step 03 — Evaluation Context

```text
core/step03_EvaluationContext.py
```

Evaluation Context는 rule 평가 전에 필요한 문맥 정보를 만든다.

주요 책임:

```text
- 어떤 필드가 존재하는지 기록
- 어떤 필드가 누락되었는지 기록
- 어떤 rule 평가가 제한되는지 기록
```

예시:

```text
confidence=None
→ missing_fields에 confidence 기록
→ confidence 기반 rule 평가 제한

decision_type=None
→ decision_type_dependent_rules_blocked 기록

model_version=None
→ missing_fields에 기록
→ evaluation limit은 아님
```

이 단계는 rule을 직접 평가하지 않는다.  
rule 평가에 필요한 context만 제공한다.

---

### 3-5 Step 04 — Rule Evaluation

```text
core/step04_RuleEvaluation.py
```

Rule Evaluation 단계는 사전에 정의된 rule을 평가한다.

예시 rule:

```text
approve_confidence_low
latency_high
missing_confidence
missing_model_version
system_error_override
```

이 단계의 출력은 `RuleEvaluation` 목록이다.

각 rule evaluation은 다음 정보를 가진다.

```text
rule_id
triggered
category
score
reason
is_high_risk
```

Rule Evaluation은 아직 최종 score나 level을 결정하지 않는다.  
각 rule이 발동되었는지만 판단한다.

---

### 3-6 Step 05 — Signal Generation

```text
core/step05_SignalGeneration.py
```

Signal Generation 단계는 발동된 rule만 `Signal`로 변환한다.

```text
RuleEvaluation(triggered=True)
→ Signal
```

발동되지 않은 rule은 signal로 생성되지 않는다.

Signal은 이후 score aggregation과 action generation에서 사용된다.

Signal의 주요 정보:

```text
rule_id
category
score
reason
evidence
is_high_risk
```

이 단계는 rule을 다시 평가하지 않는다.  
이미 평가된 rule 결과를 구조화된 signal로 변환한다.

---

### 3-7 Step 06 — Score Aggregation

```text
core/step06_ScoreAggregation.py
```

Score Aggregation 단계는 signal을 기반으로 score를 집계한다.

이 시스템은 risk와 uncertainty를 하나의 점수로 합치지 않는다.

```text
risk_score
→ risk category signal의 score 합산

uncertainty_score
→ uncertainty category signal의 score 합산
```

또한 high-risk signal은 일반 score 누적과 별도로 처리된다.

```text
has_high_risk_signal
→ True / False
```

이 단계의 핵심은 다음과 같다.

```text
uncertainty는 risk_score에 직접 더해지지 않는다.
high-risk signal은 score가 아니라 별도 flag로 유지된다.
```

---

### 3-8 Step 07 — Gate Interpretation

```text
core/step07_GateInterpretation.py
```

Gate Interpretation은 최종 해석을 수행하는 핵심 단계이다.

입력:

```text
risk_score
uncertainty_score
has_high_risk_signal
has_stability_signal
```

출력:

```text
GateDecision
```

`GateDecision`은 다음 정보를 포함한다.

```text
final_level
boundary
human_review
gate_reason
```

이 시스템에서 최종 level과 human_required는 서로 다른 개념이다.

```text
final_level
→ 시스템 해석 수준

human_required
→ 시스템이 자동 확정을 멈추고 인간 검토를 요구해야 하는지 여부
```

예시:

```text
risk_score=5
uncertainty_score=1

→ level=WARN
→ human_required=True
```

이는 위험이 낮다는 의미가 아니다.

```text
높은 위험 신호는 감지되었지만,
불확실성으로 인해 시스템이 CRITICAL을 자동 확정하지 않는다는 의미이다.
```

---

### 3-9 Step 08 — Action Generation

```text
core/step08_ActionGeneration.py
```

Action Generation 단계는 `GateDecision`과 `Signal`을 기반으로 운영 행동 후보를 생성한다.

예시 action:

```text
human_review_required
immediate_investigation
review_missing_or_incomplete_information
monitor_closely
escalate_incident
no_immediate_action_required
```

이 단계는 판단을 다시 하지 않는다.

하지 않는 것:

```text
- risk_score 재계산
- final_level 변경
- human_required 재판단
- priority 생성
```

Action Generation은 이미 만들어진 gate 결과와 signal 원인을 운영 행동으로 번역한다.

---

### 3.10 Step 09 — Alert Output

```text
core/step09_AlertOutput.py
```

Alert Output 단계는 최종 결과를 조립한다.

출력 객체:

```text
AlertOutput
```

주요 필드:

```text
event_id
level
risk_score
uncertainty_score
human_required
recommended_actions
reason_summary
signals
metadata
```

이 단계는 결과를 재계산하지 않는다.

```text
risk_score
→ ScoreSummary에서 가져옴

level
→ GateDecision에서 가져옴

recommended_actions
→ ActionRecommendation에서 가져옴

reason_summary
→ ActionRecommendation.message에서 가져옴
```

Alert Output은 최종 판단자가 아니라 이미 만들어진 결과를 외부에 전달하기 위한 출력 레이어이다.

---

## 4. Data Flow Summary

```text
DecisionEvent
  ↓
ValidationResult
  ↓
NormalizedEvent
  ↓
EvaluationContext
  ↓
RuleEvaluation[]
  ↓
Signal[]
  ↓
ScoreSummary
  ↓
GateInputs
  ↓
GateDecision
  ↓
ActionRecommendation
  ↓
AlertOutput
```

각 데이터 객체는 다음 단계로 필요한 정보만 전달한다.

---

## 5. Responsibility Separation

이 프로젝트는 각 step의 책임을 명확히 분리한다.

| Layer | Responsibility |
|---|---|
| Validation | invalid input 차단 |
| Normalization | 입력값 정규화 |
| Evaluation Context | missing field와 evaluation limit 기록 |
| Rule Evaluation | rule 발동 여부 평가 |
| Signal Generation | triggered rule을 signal로 변환 |
| Score Aggregation | risk와 uncertainty 분리 집계 |
| Gate Interpretation | final_level과 human_required 결정 |
| Action Generation | 운영 행동 후보 생성 |
| Alert Output | 최종 출력 조립 |

이 구조를 통해 특정 단계의 변경이 다른 단계의 책임을 침범하지 않도록 한다.

---

## 6. Design Constraints

이 architecture는 다음 제약을 따른다.

```text
1. invalid input은 rule evaluation으로 넘어가지 않는다.
2. uncertainty는 risk_score에 직접 더해지지 않는다.
3. high-risk signal은 일반 score가 아니라 override flag로 유지된다.
4. final_level과 human_required는 분리된다.
5. action generation은 risk를 재해석하지 않는다.
6. priority는 생성하지 않는다.
7. alert output은 결과를 재계산하지 않는다.
```

이 제약은 테스트로도 보호된다.

---

## 7. Current Scope

현재 architecture는 MVP 수준이다.

현재 포함된 것:

```text
- rule-based pipeline
- validation layer
- risk / uncertainty 분리
- gate interpretation
- action generation
- alert output
- pytest 기반 테스트
```

현재 포함되지 않은 것:

```text
- API 서버
- 데이터베이스
- 인증/권한
- 실시간 대시보드
- 배포 환경
- 운영 로그 시스템
- 동적 threshold 최적화
```

따라서 이 문서는 완성형 운영 시스템의 architecture가 아니라,  
AI 의사결정 결과를 구조화하기 위한 rule-based MVP architecture를 설명한다.
