# Decision Boundary

이 문서는 `AI Decision Risk Signal Monitoring System`에서 시스템이 어디까지 자동 해석을 수행하고, 어떤 조건에서 인간 검토를 요구하는지 설명한다.

현재 버전은 AI 의사결정 이벤트를 구조화하여 **위험 신호, 불확실성, critical override, 인간 검토 필요 여부**를 분리하는 FastAPI 기반 rule-based MVP이다.

이 문서의 핵심은 다음 질문이다.

- 시스템이 이 이벤트를 어디까지 해석할 수 있는가?
- 그리고 어느 시점에서 인간 검토가 필요한가?

---

## 1. Core Idea

이 프로젝트는 AI 또는 시스템이 최종 결정을 대신 내리는 것을 목표로 하지 않는다.

시스템은 다음을 수행하지 않는다.

- 자동 승인
- 자동 거절
- 최종 의사결정 확정
- 사건 간 priority 결정
- 인간 판단 대체

대신 시스템은 다음을 수행한다.

- 위험 신호 구조화
- 불확실성 분리
- 평가 제한 조건 기록
- critical override 분리
- 인간 검토 필요 여부 표시
- 자동 해석 경계 명시

즉 이 시스템의 목적은 결론을 대신 내리는 것이 아니라 **시스템이 어디까지 해석할 수 있고 어디서 멈춰야 하는지**를 명확히 드러내는 것이다.

---

## 2. Boundary의 의미

Decision Boundary는 단순히 위험도가 높은지 낮은지를 판단하는 기준이 아니다.

이 문서에서 Boundary는 다음을 의미한다.

```text
현재 시스템이 이 해석 결과를 자동으로 확정해도 되는가?
아니면 인간 검토가 필요한가?
```

따라서 boundary는 다음 값들을 하나의 score로 합쳐 판단하지 않는다.

```text
risk_score
uncertainty_score
has_critical_override_signal
has_stability_signal
```

대신 각 값을 분리한 상태로 유지한 뒤, Gate Interpretation 단계에서 정책적으로 해석한다.

---

## 3. Key Concepts

### 3.1 risk_score

`risk_score`는 실제로 관측된 위험 신호의 누적이다.

예시:

```text
approve 결정에서 낮은 confidence
높은 latency
```

risk_score는 “관측 가능한 위험 조건”을 나타낸다.

중요한 점은 다음과 같다.

- risk_score는 risk category signal만 합산한다.
- uncertainty signal은 risk_score에 합산하지 않는다.
- failure signal은 risk_score에 합산하지 않는다.

---

### 3.2 uncertainty_score

`uncertainty_score`는 위험 그 자체가 아니라 판단을 제한하는 정보 부족 상태를 나타낸다.

예시:

```text
confidence = None
model_version = None
```

불확실성은 위험을 직접 낮추거나 높이지 않는다.

```text
uncertainty_score가 증가한다 ≠ risk_score가 증가한다
```

불확실성은 시스템이 해당 해석을 자동으로 확정할 수 있는지에 영향을 준다.

---

### 3.3 failure signal

`failure signal`은 시스템 오류 또는 평가 무결성 실패를 나타낸다.

예시:

```text
error_code = "timeout_01"
error_code = "gateway_failure"
```

failure signal은 일반 risk signal이 아니다.

```text
category = "failure"
score = 0
is_critical_override = True
```

따라서 failure signal은 `risk_score`에 합산되지 않는다.

```text
failure signal 발생
→ risk_score 증가 아님
→ critical override flag 활성화
→ Gate Interpretation에서 CRITICAL로 해석
```

---

### 3.4 critical override

`critical override`는 score 합산 결과와 별개로 시스템이 즉시 인간 검토를 요구해야 하는 상태를 의미한다.

이 프로젝트에서 critical override는 다음 필드로 표현된다.

```text
is_critical_override = True
```

대표 rule:

```text
evaluation_integrity_override
```

critical override의 목적은 다음과 같다.

- system failure를 risk_score로 위장하지 않는다.
- failure path를 일반 risk path와 분리한다.
- score가 0이어도 CRITICAL 해석이 가능하게 한다.

---

### 3.5 human_required

`human_required`는 시스템이 자동 해석을 멈추고 인간 검토를 요구해야 하는지를 나타낸다.

```text
human_required = True
→ 시스템이 현재 해석을 인간 검토 없이 확정하지 않는다.
```

이는 시스템 실패가 아니며 의도적으로 설계된 결과이다.

---

### 3.6 final_level

`final_level`은 시스템이 현재 이벤트를 어떤 수준으로 해석했는지를 나타낸다.

```text
INFO
WARN
CRITICAL
```

단, `final_level`은 순수 위험도만을 의미하지 않는다.

이 값은 다음 요소들을 함께 고려한 **시스템 해석 결과**이다.

```text
risk_score
uncertainty_score
has_critical_override_signal
has_stability_signal
```

따라서 다음 상태도 가능하다.

```text
level = WARN
human_required = True
```

이는 모순이 아니다.

의미는 다음과 같다.

```text
위험 신호는 존재하지만 시스템이 더 강한 해석을 자동 확정할 수 없어 인간 검토가 필요하다.
```

---

## 4. Boundary Logic

### 4.1 Low Risk + Low Uncertainty

조건:

```text
risk_score = 0
uncertainty_score = 0
has_critical_override_signal = False
```

결과:

```text
level = INFO
human_required = False
auto_finalize_allowed = True
```

의미:

```text
관측된 위험 신호와 판단 제한 요소가 낮으므로 시스템은 INFO 수준의 해석을 제공할 수 있다.
```

예상 action:

```text
no_immediate_action_required
```

---

### 4.2 Low Risk + Uncertainty

조건:

```text
risk_score = 0
uncertainty_score >= 1
has_critical_override_signal = False
```

결과:

```text
level = INFO
human_required = False
auto_finalize_allowed = True
```

의미:

```text
위험 신호는 낮지만 일부 정보가 부족하다.
강제 인간 검토까지 요구하지는 않지만 누락 정보 확인 action을 제공한다.
```

예상 action:

```text
review_missing_or_incomplete_information
no_immediate_action_required
```

이 상태에서 `INFO`는 “모든 정보가 완전하다”는 뜻이 아니다.
위험 신호가 낮다는 뜻이다.

---

### 4.3 Medium Risk + Low Uncertainty

조건:

```text
risk_score >= 2
risk_score < 4
uncertainty_score = 0
has_critical_override_signal = False
```

결과:

```text
level = WARN
human_required = False
auto_finalize_allowed = True
```

의미:

```text
중간 수준의 위험 신호가 감지되었지만 판단을 제한하는 불확실성은 낮다.
```

예상 action:

```text
monitor_closely
```

---

### 4.4 Medium Risk + Uncertainty

조건:

```text
risk_score >= 2
risk_score < 4
uncertainty_score >= 1
has_critical_override_signal = False
```

결과:

```text
level = WARN
human_required = True
auto_finalize_allowed = False
```

의미:

```text
중간 수준의 위험 신호가 있으며 불확실성으로 인해 시스템이 자동 해석을 확정하지 않는다.
```

예상 action:

```text
human_review_required
review_missing_or_incomplete_information
monitor_closely
```

---

### 4.5 High Risk + Low Uncertainty

조건:

```text
risk_score >= 4
uncertainty_score = 0
has_critical_override_signal = False
```

결과:

```text
level = CRITICAL
human_required = True
auto_finalize_allowed = False
```

의미:

```text
높은 위험 신호가 감지되었고 판단을 제한하는 불확실성이 낮다.
```

이 경우 시스템은 CRITICAL 수준의 해석을 제공할 수 있다.
다만 CRITICAL 상황이므로 인간 검토는 필요하다.

예상 action:

```text
human_review_required
escalate_incident
```

---

### 4.6 High Risk + Uncertainty

조건:

```text
risk_score >= 4
uncertainty_score >= 1
has_critical_override_signal = False
```

결과:

```text
level = WARN
human_required = True
auto_finalize_allowed = False
```

의미:

```text
높은 위험 신호는 감지되었다.
하지만 불확실성 때문에 시스템이 CRITICAL을 자동 확정하지 않는다.
따라서 인간 검토가 필요하다.
```

즉 uncertainty가 risk_score를 낮춘 것이 아니다.

```text
risk_score는 유지된다.
다만 시스템의 자동 확정 가능성이 제한된다.
```

예상 action:

```text
human_review_required
review_missing_or_incomplete_information
monitor_closely
```

---

### 4.7 Critical Override / Evaluation Integrity Failure

조건:

```text
has_critical_override_signal = True
```

대표 signal:

```text
rule_id = "evaluation_integrity_override"
category = "failure"
score = 0
is_critical_override = True
```

결과:

```text
level = CRITICAL
human_required = True
auto_finalize_allowed = False
```

예시:

```text
error_code = "timeout_01"
error_code = "gateway_failure"
```

이 경우 시스템 오류 또는 평가 무결성 실패로 보고 CRITICAL 해석을 유도한다.

중요한 점은 다음과 같다.

```text
failure signal은 risk_score에 합산되지 않는다.
score는 0이다.
CRITICAL 해석은 score 때문이 아니라 critical override flag 때문이다.
```

예상 action:

```text
human_review_required
immediate_investigation
escalate_incident
```

---

## 5. Why WARN + human_required=True Is Valid

일반적으로 WARN은 CRITICAL보다 낮은 수준으로 보일 수 있다.

하지만 이 시스템에서 다음 상태는 유효하다.

```text
level = WARN
human_required = True
```

이 상태는 다음을 의미한다.

```text
위험 신호가 없다는 뜻이 아니다.
인간 검토가 불필요하다는 뜻도 아니다.
시스템이 현재 정보를 바탕으로 더 강한 해석을 자동 확정하지 않는다는 뜻이다.
```

즉 `WARN + human_required=True`는 일반 경고가 아니라 **자동 확정이 제한된 검토 필요 상태**이다.

대표 케이스:

```text
risk_score >= 4
uncertainty_score >= 1

→ level = WARN
→ human_required = True
```

이는 risk_score가 낮아진 것이 아니다.
불확실성 때문에 시스템이 CRITICAL을 자동 확정하지 않는 것이다.

---

## 6. Why human_required Is Separate from level

`level`과 `human_required`는 서로 다른 축이다.

```text
level
→ 시스템 해석 수준

human_required
→ 인간 검토 필요 여부
```

예를 들어 다음 두 상태는 서로 다르다.

```text
level = WARN
human_required = False
```

```text
level = WARN
human_required = True
```

둘 다 WARN이지만 의미는 다르다.

첫 번째는 중간 위험 신호가 있지만 자동 해석이 가능한 상태이다.
두 번째는 불확실성 또는 판단 제한으로 인해 인간 검토가 필요한 상태이다.

이 분리는 중요하다.

```text
level만으로 인간 검토 여부를 결정하지 않는다.
human_required는 별도의 decision boundary 결과이다.
```

---

## 7. Why Critical Override Is Separate from risk_score

critical override는 일반 risk score와 분리된다.

예를 들어 다음 입력을 보자.

```text
decision_type = "approve"
confidence = 0.9
latency_ms = 300
model_version = "v1"
error_code = "gateway_failure"
```

일반 risk rule 관점에서는 낮은 confidence도 아니고 high latency도 아니다.

따라서 risk_score는 0일 수 있다.

```text
risk_score = 0
uncertainty_score = 0
```

하지만 `error_code="gateway_failure"`는 evaluation integrity failure이다.

따라서 다음 signal이 생성된다.

```text
rule_id = "evaluation_integrity_override"
category = "failure"
score = 0
is_critical_override = True
```

최종 해석은 다음과 같다.

```text
level = CRITICAL
human_required = True
```

이 설계의 의미:

```text
시스템 오류를 risk_score로 위장하지 않는다.
risk_score가 0이어도 failure path는 CRITICAL이 될 수 있다.
critical override는 score가 아니라 별도 flag로 처리한다.
```

---

## 8. Why Priority Is Not Generated

이 시스템은 `priority`를 생성하지 않는다.

priority는 사건 간 처리 순서를 의미할 수 있다.

```text
이 이벤트를 다른 이벤트보다 먼저 처리해야 한다.
```

이 프로젝트는 이러한 판단을 시스템이 자동으로 수행하지 않는다.

대신 단일 이벤트에 대한 운영 행동 후보만 제공한다.

```text
human_review_required
review_missing_or_incomplete_information
monitor_closely
escalate_incident
immediate_investigation
```

이 action들은 priority가 아니다.

```text
priority
→ 사건 간 순서 판단

action
→ 단일 이벤트에 대한 대응 행동 후보
```

최종 처리 순서와 우선순위 판단은 인간 검토자 또는 운영자의 책임으로 남긴다.

---

## 9. auto_finalize_allowed와 human_required

현재 MVP에서는 대부분 다음 관계가 성립한다.

```text
human_required = True
→ auto_finalize_allowed = False
```

하지만 두 값은 개념적으로 다르다.

```text
auto_finalize_allowed
→ 시스템이 자동 해석을 확정할 수 있는지 여부

human_required
→ 인간 검토가 필요한지 여부
```

현재 구현에서는 두 값이 강하게 연결되어 있지만, 향후 정책이 확장되면 다음과 같은 상태도 고려할 수 있다.

```text
auto_finalize_allowed = False
human_required = False
```

예를 들어 시스템이 자동 확정은 하지 않지만 즉시 인간 검토를 강제하지 않고 보류 상태로 둘 수 있다.

현재 MVP에서는 단순성과 명확성을 위해 `human_required`와 `auto_finalize_allowed`를 직접 연결한다.

---

## 10. Boundary Constraints

이 시스템의 decision boundary는 다음 제약을 가진다.

- uncertainty는 risk_score를 직접 낮추거나 높이지 않는다.
- risk와 uncertainty는 하나의 combined score로 합치지 않는다.
- failure signal은 risk_score에 합산하지 않는다.
- critical override는 score가 아니라 is_critical_override flag로 처리한다.
- human_required는 final_level과 분리한다.
- priority는 생성하지 않는다.
- Gate Interpretation 이후 단계는 final_level을 재계산하지 않는다.
- system failure는 risk score로 위장하지 않는다.

이 제약은 unit, integration, design invariant, API test를 통해 보호된다.

---

## 11. Summary

이 시스템의 decision boundary는 단순히 위험도를 계산하는 기준이 아니다.

핵심은 다음 질문이다.

- 현재 시스템이 이 해석을 자동으로 확정할 수 있는가?
- 아니면 인간 검토가 필요한가?

따라서 이 프로젝트는 결정을 대신 내리는 것이 아니라 AI 의사결정 결과를 해석할 때 시스템이 멈춰야 하는 지점을 명확히 정의한다.

`human_required=True`는 실패가 아니라 설계된 결과이다.
`critical override`는 risk score가 아니라 failure path와 override flag로 처리된다.
