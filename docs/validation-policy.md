# Validation Policy

이 문서는 `AI Decision Risk Signal Monitoring System`에서 입력 이벤트를 어떻게 검증하고 invalid input과 missing input을 어떻게 구분하는지 설명한다.

현재 버전은 실제 운영 배포용 완성 시스템이 아니라 AI 의사결정 이벤트를 구조화하여 위험 신호와 불확실성을 분리하는 rule-based MVP이다.

---

## 1. Purpose

Validation의 목적은 잘못된 입력이 rule evaluation 단계로 들어가지 않도록 막는 것이다.

이 시스템은 다음 순서를 따른다.

```text
DecisionEvent
 → Validation
 → Normalization
 → Evaluation Context
 → Rule Evaluation
```

Validation에서 실패한 이벤트는 이후 단계로 진행하지 않는다.

```text
invalid input
→ ValueError
→ Normalization 진행 안 함
→ Rule Evaluation 진행 안 함
→ AlertOutput 생성 안 함
```

이는 invalid input이 risk나 uncertainty로 잘못 해석되는 것을 방지하기 위한 설계이다.

---

## 2. Invalid Input과 Missing Input의 차이

이 시스템은 다음 두 개념을 구분한다.

```text
Invalid Input
→ 값이 존재하지만 형식, 범위, 허용 조건을 위반한 입력

Missing Input
→ 값이 없어서 판단에 필요한 정보가 부족한 상태
```

두 개념은 다르게 처리된다.

```text
invalid input
→ validation error

missing input
→ field 역할에 따라 uncertainty 또는 evaluation limit
```

---

## 3. Invalid Input

Invalid input은 값이 존재하지만 시스템이 허용한 형식이나 범위를 벗어난 경우이다.

예시:

```text
confidence = 1.5
confidence = -0.1
confidence = "abc"

latency_ms = -100
latency_ms = "fast"

decision_type = "approvee"
event_id = ""
metadata = "not-a-dict"
```

이러한 입력은 정상적인 판단 대상이 아니다.

따라서 시스템은 이를 risk signal이나 uncertainty signal로 처리하지 않는다.

```text
invalid input
≠ risk
≠ uncertainty
≠ alert
```

Validation 실패 시 `ValueError`가 발생한다.

---

## 4. Missing Input

Missing input은 값이 없거나 비어 있는 상태이다.

예시:

```text
confidence = None
model_version = None
latency_ms = None
decision_type = None
```

Missing input은 항상 validation error가 아니다.

필드의 역할에 따라 다르게 처리된다.

```text
confidence=None
→ uncertainty

model_version=None
→ uncertainty

decision_type=None
→ evaluation limit

latency_ms=None
→ missing field
```

즉 missing input은 단순히 “잘못된 입력”이 아니라 판단 가능성을 제한하는 정보로 해석될 수 있다.

---

## 5. Field-Level Validation Policy

### 5-1 event_id

`event_id`는 이벤트를 식별하기 위한 필수 값이다.

Invalid:

```text
event_id = None
event_id = ""
event_id = " "
```

이 경우 이벤트 추적이 불가능하므로 validation error로 처리한다.

---

### 5-2 confidence

`confidence`는 0.0 이상 1.0 이하의 숫자여야 한다.

Valid:

```text
confidence = 0.0
confidence = 0.5
confidence = 1.0
confidence = "0.52"
```

Invalid:

```text
confidence = -0.1
confidence = 1.5
confidence = "abc"
```

Missing:

```text
confidence = None
```

`confidence=None`은 invalid input이 아니다.  
대신 confidence 기반 rule을 평가할 수 없다는 의미이다.

따라서 missing confidence는 uncertainty로 처리된다.

```text
confidence=None
→ uncertainty signal
→ confidence-based rule evaluation 제한
```

반면 `confidence=1.5`는 값이 존재하지만 허용 범위를 벗어난다.

```text
confidence=1.5
→ validation error
```

---

### 5-3 latency_ms

`latency_ms`는 0 이상의 정수여야 한다.

Valid:

```text
latency_ms = 800
latency_ms = 2800
latency_ms = "2800"
```

Invalid:

```text
latency_ms = -100
latency_ms = "fast"
```

Missing:

```text
latency_ms = None
```

`latency_ms=None`은 latency 기반 rule 평가를 제한할 수 있다.  
하지만 그 자체가 시스템 오류나 위험을 의미하지는 않는다.

따라서 missing latency는 validation error가 아니라 missing field로 기록된다.

---

### 5-4 decision_type

`decision_type`은 허용된 decision type이어야 한다.

Valid:

```text
decision_type = "approve"
decision_type = "reject"
```

Invalid:

```text
decision_type = "approvee"
decision_type = "unknown"
```

Missing:

```text
decision_type = None
decision_type = ""
decision_type = " "
```

`decision_type="approvee"`처럼 허용되지 않은 값은 validation error이다.

그러나 `decision_type=None`은 조금 다르게 처리된다.

`decision_type`은 단순 입력값이 아니라 rule routing context이다.  
예를 들어 다음 rule은 decision_type이 있어야 평가할 수 있다.

```text
approve + low confidence
```

따라서 `decision_type=None`은 일반 uncertainty가 아니라 decision-specific rule 평가를 제한하는 evaluation limit으로 처리된다.

```text
decision_type=None
→ decision_type_dependent_rules_blocked
```

---

### 5-5 model_version

`model_version`은 현재 MVP에서 필수 validation 대상은 아니다.

Valid:

```text
model_version = "v1"
model_version = "v2"
```

Missing:

```text
model_version = None
model_version = ""
model_version = " "
```

`model_version=None`은 현재 이벤트가 위험하다는 뜻이 아니다.

하지만 모델 버전 정보가 없으면 다음 질문에 답하기 어려워진다.

```text
이 결과는 어떤 모델 버전에서 생성되었는가?
같은 입력을 다시 넣었을 때 같은 결과를 재현할 수 있는가?
해당 confidence 값은 어떤 모델 기준에서 해석되어야 하는가?
```

따라서 missing model_version은 risk가 아니라 uncertainty로 처리된다.

```text
model_version=None
→ uncertainty signal
```

---

### 5-6 error_code

`error_code`는 시스템 오류성 신호를 표현할 수 있다.

예시:

```text
error_code = "gateway_failure"
```

특정 error_code는 high-risk signal로 이어질 수 있다.

다만 error_code 자체의 유효성 정책은 현재 MVP에서 제한적으로 다룬다.

현재 범위에서는 error_code가 존재할 경우 rule evaluation 단계에서 high-risk 여부를 판단한다.

---

### 5-7 metadata

`metadata`는 dictionary 형태여야 한다.

Valid:

```text
metadata = {}
metadata = {"request_id": "req_001"}
```

Invalid:

```text
metadata = "not-a-dict"
metadata = ["request_id"]
```

metadata가 dictionary가 아니면 validation error로 처리한다.

최종 `AlertOutput`에서는 metadata를 원본 그대로 공유하지 않고 복사하여 보존한다.

---

## 6. Validation Failure Format

Validation 실패 시 시스템은 사람이 읽을 수 있는 메시지를 포함한 `ValueError`를 발생시킨다.

예시:

```text
confidence: Confidence must be between 0.0 and 1.0 (value=1.5)
```

여러 validation issue가 있을 경우 `;`로 연결된다.

예시:

```text
confidence: Confidence must be between 0.0 and 1.0 (value=1.5); latency_ms: Latency ms must be greater than or equal to zero (value=-100)
```

이 형식은 invalid input의 원인을 빠르게 확인하기 위한 것이다.

---

## 7. Why Invalid Input Does Not Become Uncertainty

Invalid input과 uncertainty는 다르다.

예를 들어:

```text
confidence=None
```

은 confidence 정보가 없는 상태이다.

```text
confidence=1.5
```

는 confidence 값이 존재하지만 허용 범위를 위반한 상태이다.

두 경우를 모두 uncertainty로 처리하면 문제가 생긴다.

```text
잘못된 데이터가 정상적인 판단 제한 요소처럼 pipeline을 통과할 수 있다.
```

따라서 invalid input은 pipeline 초반에서 차단한다.

---

## 8. Why Missing Input Does Not Always Become Validation Error

일부 missing input은 실제 운영 상황에서 발생할 수 있다.

예를 들어 모델 응답에 confidence가 없거나 model_version이 누락될 수 있다.

이런 경우를 모두 validation error로 차단하면 시스템은 정보 부족 상태를 구조화할 수 없다.

따라서 이 프로젝트는 missing input을 필드 역할에 따라 구분한다.

```text
confidence=None
→ uncertainty

model_version=None
→ uncertainty

decision_type=None
→ evaluation limit
```

이렇게 하면 시스템은 잘못된 입력은 차단하면서도 정보 부족으로 인한 판단 제한은 구조적으로 표현할 수 있다.

---

## 9. Validation Policy Summary

```text
invalid input
→ ValueError
→ pipeline 중단

missing confidence
→ uncertainty

missing model_version
→ uncertainty

missing decision_type
→ evaluation limit

valid input
→ pipeline 계속 진행
```

Validation은 단순한 입력 검사 단계가 아니다.

이 시스템에서 validation은 다음을 보장한다.

```text
잘못된 입력은 판단 대상이 되지 않는다.
정보 부족은 별도로 구조화된다.
risk와 uncertainty는 validation 이후 단계에서만 해석된다.
```

---

## 10. Summary

Validation Policy의 핵심은 다음과 같다.

```text
값이 잘못된 경우와 값이 없는 경우를 구분한다.
```

이 구분을 통해 시스템은 invalid input을 risk나 uncertainty로 오해하지 않고 missing input은 판단 제한 요소로 구조화할 수 있다.
따라서 validation은 전체 decision pipeline의 첫 번째 안전장치이다.
