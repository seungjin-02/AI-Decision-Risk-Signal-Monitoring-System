# Test Strategy

이 문서는 `AI Decision Risk Signal Monitoring System`의 테스트 구조와 테스트가 보호하는 설계 원칙을 설명한다.

현재 버전은 실제 운영 배포용 완성 시스템이 아니라 AI 의사결정 이벤트를 구조화하여 위험 신호, 불확실성, 인간 검토 필요 여부를 검증하는 rule-based MVP이다.

---

## 1. Purpose

이 프로젝트의 테스트는 단순히 함수가 실행되는지만 확인하지 않는다.

테스트의 목적은 다음과 같다.

```text
1. 각 pipeline step이 자신의 책임만 수행하는지 확인한다.
2. 전체 pipeline이 DecisionEvent에서 AlertOutput까지 올바르게 연결되는지 확인한다.
3. risk와 uncertainty 분리 같은 핵심 설계 원칙이 깨지지 않도록 보호한다.
```

특히 이 프로젝트에서는 작은 코드 변경이 설계 철학을 쉽게 깨뜨릴 수 있다.

예를 들어 다음과 같은 변경은 기능상으로는 동작할 수 있지만, 설계상으로는 잘못된 변경이다.

```text
uncertainty_score를 risk_score에 더하는 변경
high-risk signal을 일반 score로만 처리하는 변경
human_required를 final_level에 종속시키는 변경
priority 필드를 다시 생성하는 변경
```

따라서 테스트는 기능 검증뿐 아니라 설계 불변조건을 보호하는 역할을 한다.

---

## 2. Test Directory Structure

테스트는 세 가지 계층으로 분리되어 있다.

```text
tests/
  unit/
  integration/
  invariants/
```

각 계층은 서로 다른 목적을 가진다.

```text
unit
→ 각 step의 독립 책임 검증

integration
→ 전체 pipeline 연결 검증

invariants
→ 반드시 유지되어야 하는 설계 원칙 검증
```

---

## 3. Unit Tests

Unit test는 각 pipeline step이 독립적으로 자신의 책임을 수행하는지 검증한다.

```text
tests/unit/
```

대상 예시:

```text
test_validation.py
test_normalization.py
test_evaluation_context.py
test_rule_evaluation.py
test_signal_generation.py
test_score_aggregation.py
test_gate_interpretation.py
test_action_generation.py
test_alert_output.py
```

---

## 4. Unit Test Responsibilities

### 4-1 Validation Test

검증 대상:

```text
event_validation.py  
```

주요 확인 사항:

```text
invalid input은 ValidationIssue로 기록된다.
confidence=1.5는 validation error이다.
confidence=None은 validation error가 아니다.
decision_type="approvee"는 validation error이다.
metadata는 dictionary여야 한다.
validation issue는 사람이 읽을 수 있는 메시지로 변환된다.
```

Validation test는 잘못된 입력이 rule evaluation으로 넘어가지 않도록 보호한다.

---

### 4-2 Normalization Test

검증 대상:

```text
step02_NormalizedEvent.py
```

주요 확인 사항:

```text
문자열 decision_type은 소문자/공백 제거 형태로 정규화된다.
문자열 confidence는 float으로 변환된다.
문자열 latency_ms는 int로 변환된다.
빈 문자열 또는 None은 의미 있는 missing value로 유지된다.
```

Normalization test는 입력 정리와 판단 로직이 섞이지 않도록 보호한다.

---

### 4-3 Evaluation Context Test

검증 대상:

```text
step03_EvaluationContext.py
```

주요 확인 사항:

```text
누락 필드가 missing_fields에 기록된다.
confidence=None은 confidence 기반 rule 평가 제한으로 연결된다.
decision_type=None은 decision-specific rule 평가 제한으로 연결된다.
model_version=None은 missing field로 기록되지만 evaluation limit은 아니다.
```

Evaluation Context test는 rule evaluation 전에 판단 제한 조건이 올바르게 정리되는지 확인한다.

---

### 4-4 Rule Evaluation Test

검증 대상:

```text
step04_RuleEvaluation.py
```

주요 확인 사항:

```text
approve + low confidence는 risk rule을 trigger한다.
high latency는 risk rule을 trigger한다.
missing confidence는 uncertainty rule을 trigger한다.
missing model_version은 uncertainty rule을 trigger한다.
gateway_failure는 high-risk rule을 trigger한다.
```

Rule Evaluation test는 개별 rule의 발동 조건을 검증한다.

---

### 4-5 Signal Generation Test

검증 대상:

```text
step05_SignalGeneration.py
```

주요 확인 사항:

```text
triggered=True인 rule만 Signal로 변환된다.
triggered=False인 rule은 Signal로 생성되지 않는다.
Signal은 rule_id, category, score, reason, evidence를 유지한다.
high-risk rule은 is_high_risk=True를 유지한다.
```

Signal Generation test는 rule 평가 결과가 이후 pipeline에서 사용할 수 있는 구조화된 signal로 변환되는지 확인한다.

---

### 4-6 Score Aggregation Test

검증 대상:

```text
step06_ScoreAggregation.py
```

주요 확인 사항:

```text
risk signal은 risk_score에 합산된다.
uncertainty signal은 uncertainty_score에 합산된다.
uncertainty signal은 risk_score에 더해지지 않는다.
high-risk signal은 score가 아니라 별도 flag로 유지된다.
```

Score Aggregation test는 risk와 uncertainty가 섞이지 않도록 보호한다.

---

### 4-7 Gate Interpretation Test

검증 대상:

```text
step07_GateInterpretation.py
```

주요 확인 사항:

```text
low risk + low uncertainty는 INFO이다.
medium risk는 WARN이다.
high risk + low uncertainty는 CRITICAL이다.
high risk + uncertainty는 WARN + human_required=True이다.
high-risk override는 CRITICAL + human_required=True이다.
```

Gate Interpretation test는 최종 해석이 명시된 boundary logic을 따르는지 확인한다.

---

### 4-8 Action Generation Test

검증 대상:

```text
step08_ActionGeneration.py
```

주요 확인 사항:

```text
human_required=True이면 human_review_required action이 생성된다.
high-risk signal이 있으면 immediate_investigation action이 생성된다.
uncertainty signal이 있으면 review_missing_or_incomplete_information action이 생성된다.
CRITICAL은 escalate_incident action으로 연결된다.
WARN은 monitor_closely action으로 연결된다.
priority는 생성하지 않는다.
```

Action Generation test는 action이 판단 추천이 아니라 운영 행동 번역으로 유지되는지 확인한다.

---

### 4-9 Alert Output Test

검증 대상:

```text
step09_AlertOutput.py
```

주요 확인 사항:

```text
AlertOutput은 이미 계산된 결과를 조립한다.
risk_score를 재계산하지 않는다.
final_level을 재판단하지 않는다.
recommended_actions를 새로 생성하지 않는다.
reason_summary는 action.message에서 가져온다.
metadata는 복사되어 보존된다.
priority 필드는 존재하지 않는다.
```

Alert Output test는 최종 출력 레이어가 판단을 다시 수행하지 않도록 보호한다.

---

## 5. Integration Tests

Integration test는 여러 step이 연결된 전체 pipeline 흐름을 검증한다.

```text
tests/integration/
```

주요 테스트:

```text
test_pipeline_validation.py
test_full_pipeline.py
```

---

### 5-1. Pipeline Validation Test

`test_pipeline_validation.py`는 validation이 pipeline 입구에서 정상적으로 작동하는지 확인한다.

핵심 원칙:

```text
invalid input은 rule evaluation으로 넘어가지 않는다.
```

예시:

```text
confidence=1.5
→ ValueError
→ normalize_event 실행 안 됨
→ evaluate_rule 실행 안 됨
→ AlertOutput 생성 안 됨
```

이 테스트는 invalid input이 risk나 uncertainty로 잘못 해석되는 것을 방지한다.

---

### 5-2. Full Pipeline Test

`test_full_pipeline.py`는 `DecisionEvent`가 전체 pipeline을 거쳐 최종 `AlertOutput`으로 변환되는 흐름을 검증한다.

검증 예시:

```text
normal input
→ INFO

low confidence approve
→ WARN

high latency
→ WARN

low confidence + high latency
→ CRITICAL

high risk + uncertainty
→ WARN + human_required=True

gateway_failure
→ CRITICAL + human_required=True

missing confidence
→ uncertainty

invalid input
→ ValueError
```

Full Pipeline Test는 각 step이 개별적으로 맞는 것뿐 아니라 조립된 전체 시스템도 설계대로 동작하는지 확인한다.

---

## 6. Design Invariant Tests

Invariant test는 시스템의 핵심 설계 원칙이 깨지지 않도록 보호한다.

```text
tests/invariants/
```

주요 테스트:

```text
test_design_invariants.py
```

Invariant test는 기능 테스트보다 더 강한 의미를 가진다.

기능상으로는 동작하더라도 아래 원칙이 깨지면 이 프로젝트의 설계 의도는 훼손된다.

---

## 7. Protected Design Invariants

### 7-1 Uncertainty must not increase risk_score directly

```text
uncertainty signal
→ uncertainty_score 증가
→ risk_score에는 직접 반영하지 않음
```

이 원칙은 risk와 uncertainty를 분리하기 위한 핵심 조건이다.

---

### 7-2 High-risk signal must work as override

```text
high-risk signal
→ 일반 score 누적이 아니라 override flag로 유지
```

이 원칙은 시스템 오류성 또는 명시적 위험 신호가 일반 점수 합산에 묻히지 않도록 보호한다.

---

### 7-3 human_required must remain separate from final_level

```text
level = WARN
human_required = True
```

이 상태는 유효하다.

`human_required`는 위험 수준 자체가 아니라 시스템이 자동 확정을 멈춰야 하는지를 나타낸다.

---

### 7-4 ActionGeneration must not reinterpret risk

Action Generation은 다음을 수행하지 않는다.

```text
risk_score 재계산
final_level 변경
human_required 재판단
```

Action Generation은 이미 만들어진 GateDecision과 Signal 원인을 운영 행동으로 번역한다.

---

### 7-5 Priority must not be generated

이 시스템은 사건 간 우선순위를 생성하지 않는다.

```text
priority
→ 사건 간 처리 순서 판단
```

이 판단은 시스템이 아니라 인간 검토자 또는 운영자의 책임으로 남긴다.

---

### 7-6 AlertOutput must not recalculate decisions

Alert Output은 다음을 수행하지 않는다.

```text
risk_score 재계산
uncertainty_score 재계산
final_level 재판단
action 재생성
```

최종 출력은 기존 결과를 조립하는 역할만 한다.

---

## 8. How to Run Tests

전체 테스트 실행:

```bash
pytest -v
```

Unit test만 실행:

```bash
pytest tests/unit -v
```

Integration test만 실행:

```bash
pytest tests/integration -v
```

Invariant test만 실행:

```bash
pytest tests/invariants -v
```

---

## 9. Why This Test Structure Matters

이 프로젝트는 단순한 rule-based alert 예제가 아니다.

핵심은 다음 구조를 유지하는 것이다.

```text
risk와 uncertainty 분리
human_required와 final_level 분리
validation과 rule evaluation 분리
action generation과 decision interpretation 분리
alert output과 decision recalculation 분리
```

따라서 테스트도 단순 결과값 확인에 그치지 않고 각 계층의 책임이 섞이지 않도록 설계되어 있다.

---

## 10. Summary

이 프로젝트의 테스트 전략은 세 가지 목표를 가진다.

```text
1. 각 step의 기능이 올바르게 동작하는지 확인한다.
2. 전체 pipeline이 대표 케이스에서 설계대로 연결되는지 확인한다.
3. 핵심 설계 원칙이 코드 변경으로 깨지지 않도록 보호한다.
```

테스트는 이 프로젝트에서 단순한 보조 수단이 아니라 decision boundary를 코드 수준에서 유지하기 위한 안전장치이다.
