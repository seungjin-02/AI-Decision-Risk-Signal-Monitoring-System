# Validation Policy

이 문서는 `AI Decision Risk Signal Monitoring System`에서 입력 이벤트를 어떻게 검증하고 invalid input과 missing input을 어떻게 구분하는지 설명한다.

현재 버전은 FastAPI API layer와 core evaluation pipeline이 분리되어 있다. 

따라서 validation도 다음 두 계층으로 나누어 이해해야 한다.

```text
API Validation
→ request body의 형식과 타입 검증
→ 실패 시 422 api_validation_error

Core Validation
→ domain rule과 값의 의미 검증
→ 실패 시 400 core_validation_error
```

이 문서의 핵심은 다음이다.

- 값이 잘못된 경우와 값이 없는 경우를 구분한다.
- API 형식 오류와 core domain 오류를 구분한다.
- 잘못된 입력은 risk나 uncertainty로 해석하지 않는다.
- 정보 부족은 field 역할에 따라 uncertainty 또는 evaluation limit으로 구조화한다.

---

## 1. Purpose

Validation의 목적은 잘못된 입력이 rule evaluation 단계로 들어가지 않도록 막는 것이다.

Core pipeline은 다음 순서를 따른다.

```text
DecisionEvent
 → validate_event
 → normalize_event
 → build_evaluation_context
 → evaluate_rule
```

Core validation에서 실패한 이벤트는 이후 단계로 진행하지 않는다.

```text
invalid input
→ ValueError
→ Normalization 이후 흐름으로 진행하지 않음
→ Rule Evaluation 진행 안 함
→ AlertOutput 생성 안 함
```

API layer에서는 core의 `ValueError`를 `CoreValidationException`으로 변환한 뒤, HTTP 400 `core_validation_error`로 매핑한다.

이는 invalid input이 risk나 uncertainty로 잘못 해석되는 것을 방지하기 위한 설계이다.

---

## 2. Validation Layers

### 2.1 API Validation

API validation은 FastAPI/Pydantic schema layer에서 수행된다.

검증 대상:

```text
request body 형식
field type
required field 존재 여부
metadata object 여부
```

실패 시:

```text
422 api_validation_error
```

예시:

```text
event_id = 1234
confidence = "not-a-number"
latency_ms = "slow"
metadata = "not-an-object"
```

이 단계에서 실패하면 core pipeline으로 들어가지 않는다.

---

### 2.2 Core Validation

Core validation은 API schema를 통과한 뒤 domain rule 기준으로 수행된다.

검증 대상:

```text
event_id blank 여부
confidence 범위
latency_ms 음수 여부
decision_type 허용 값
metadata dict 여부
```

실패 시:

```text
400 core_validation_error
```

예시:

```text
event_id = "   "
confidence = 1.5
confidence = -0.1
latency_ms = -1
decision_type = "pending"
```

Core validation 실패는 정상적인 평가 대상이 아니다.

따라서 risk signal이나 uncertainty signal로 처리하지 않는다.

---

## 3. Invalid Input과 Missing Input의 차이

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

중요한 원칙:

- invalid input은 판단 대상이 아니다.
- missing input은 판단 제한 요소일 수 있다.

---

## 4. Invalid Input

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

Core validation 실패 시 `ValueError`가 발생한다.

API layer에서는 이를 400 `core_validation_error`로 변환한다.

---

## 5. Missing Input

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
confidence = None
→ uncertainty

model_version = None
→ uncertainty

decision_type = None
→ evaluation limit

latency_ms = None
→ missing field
```

즉 missing input은 단순히 “잘못된 입력”이 아니라 판단 가능성을 제한하는 정보로 해석될 수 있다.

---

## 6. API Validation vs Core Validation

이 시스템은 API validation과 core validation을 분리한다.

| Input | Layer | Status Code | Error Type |
|---|---|---:|---|
| `event_id = 1234` | API validation | 422 | `api_validation_error` |
| `event_id = "   "` | Core validation | 400 | `core_validation_error` |
| `confidence = "not-a-number"` | API validation | 422 | `api_validation_error` |
| `confidence = 1.5` | Core validation | 400 | `core_validation_error` |
| `latency_ms = "slow"` | API validation | 422 | `api_validation_error` |
| `latency_ms = -1` | Core validation | 400 | `core_validation_error` |
| `decision_type = "pending"` | Core validation | 400 | `core_validation_error` |
| `metadata = "not-an-object"` | API validation | 422 | `api_validation_error` |

이 구분은 운영 관점에서 중요하다.

```text
422
→ 클라이언트가 request format 또는 type을 잘못 보냄

400
→ request format은 맞지만 domain rule에 맞지 않음
```

---

## 7. Field-Level Validation Policy

### 7.1 event_id

`event_id`는 이벤트를 식별하기 위한 필수 값이다.

API request에서 필수 field이다.

Invalid:

```text
event_id = None
event_id = ""
event_id = " "
```

API validation 예시:

```text
event_id field 누락
event_id = 1234
```

Core validation 예시:

```text
event_id = ""
event_id = "   "
```

이 경우 이벤트 추적이 불가능하므로 validation error로 처리한다.

---

### 7.2 confidence

`confidence`는 존재할 경우 0.0 이상 1.0 이하의 숫자여야 한다.

Valid:

```text
confidence = 0.0
confidence = 0.5
confidence = 1.0
confidence = None
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

`confidence=None`은 invalid input이 아니라 confidence 기반 rule을 평가할 수 없다는 의미이다.

따라서 missing confidence는 uncertainty로 처리된다.

```text
confidence = None
→ uncertainty signal
→ confidence-based rule evaluation 제한
```

반면 `confidence=1.5`는 값이 존재하지만 허용 범위를 벗어난다.

```text
confidence = 1.5
→ core validation error
→ 400 core_validation_error
```

API request에서는 `confidence`를 JSON number로 보내는 것을 기준으로 한다.

```json
{
  "confidence": 0.52
}
```

---

### 7.3 latency_ms

`latency_ms`는 존재할 경우 0 이상의 정수여야 한다.

Valid:

```text
latency_ms = 0
latency_ms = 800
latency_ms = 2800
latency_ms = None
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

`latency_ms=None`은 latency 기반 rule 평가를 제한할 수 있지만 그 자체가 시스템 오류나 위험을 의미하지는 않는다.

따라서 missing latency는 validation error가 아니라 missing field로 기록된다.

```text
latency_ms = None
→ missing field
→ high latency rule 평가 불가
```

API request에서는 `latency_ms`를 JSON integer로 보내는 것을 기준으로 한다.

```json
{
  "latency_ms": 2800
}
```

---

### 7.4 decision_type

`decision_type`은 존재할 경우 허용된 decision type이어야 한다.

Valid:

```text
decision_type = "approve"
decision_type = "reject"
decision_type = None
```

Invalid:

```text
decision_type = "approvee"
decision_type = "unknown"
decision_type = "pending"
decision_type = ""
decision_type = " "
```

`decision_type="approvee"`처럼 허용되지 않은 값은 validation error이다.

`decision_type=None`은 validation error가 아니라 `decision_type`은 rule routing context이므로 일부 rule을 평가할 수 없게 만든다.

예를 들어 다음 rule은 decision_type이 있어야 평가할 수 있다.

```text
approve + low confidence
```

따라서 `decision_type=None`은 decision-specific rule 평가를 제한하는 evaluation limit으로 처리된다.

```text
decision_type = None
→ decision_type_dependent_rules_blocked
```

반면 blank string은 core validation error로 처리한다.

```text
decision_type = "   "
→ 400 core_validation_error
```

---

### 7.5 model_version

`model_version`은 현재 MVP에서 필수 validation 대상은 아니다.

Valid:

```text
model_version = "v1"
model_version = "v2"
model_version = None
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
model_version = None
→ uncertainty signal
```

Normalization 이후 blank string도 `None`으로 정리될 수 있다.

```text
model_version = "   "
→ None
→ uncertainty signal
```

---

### 7.6 error_code

`error_code`는 시스템 오류 또는 평가 무결성 실패를 표현할 수 있다.

예시:

```text
error_code = "timeout_01"
error_code = "gateway_failure"
```

특정 error_code는 `evaluation_integrity_override` rule을 trigger할 수 있다.

```text
error_code = "timeout_01"
→ evaluation_integrity_override
→ category = "failure"
→ score = 0
→ is_critical_override = True
```

중요한 점은 다음과 같다.

```text
error_code 기반 failure signal은 risk_score에 합산되지 않는다.
system failure는 risk score로 위장하지 않는다.
critical override는 score가 아니라 flag로 처리한다.
```

Missing:

```text
error_code = None
error_code = ""
error_code = " "
```

`error_code=None`은 validation error가 아니다.  
또한 그 자체로 uncertainty signal을 만들지 않는다.

```text
error_code = None
→ field_presence에는 False로 기록 가능
→ missing_fields에는 포함하지 않음
→ uncertainty signal 생성 안 함
```

---

### 7.7 metadata

`metadata`는 JSON object여야 한다.

API request 관점:

```json
{
  "metadata": {}
}
```

Python 내부 관점:

```python
metadata = {}
```

즉 API 문서에서는 `metadata`를 JSON object라고 부르고, Python 내부에서는 `dict[str, Any]`로 처리한다.

Valid:

```text
metadata = {}
metadata = {"request_id": "req_001"}
metadata = {"source": "api_test"}
```

Invalid:

```text
metadata = "not-a-dict"
metadata = ["request_id"]
metadata = null
```

metadata가 dictionary/object가 아니면 validation error로 처리한다.

현재 schema에서는 metadata의 기본값이 빈 object이다.

```text
metadata omitted
→ metadata = {}
```

최종 `AlertOutput`에서는 metadata를 원본 그대로 공유하지 않고 복사하여 보존한다.

---

## 8. Validation Failure Format

Core validation 실패 시 시스템은 사람이 읽을 수 있는 메시지를 포함한 `ValueError`를 발생시킨다.

예시:

```text
confidence: Confidence must be between 0.0 and 1.0 (value=1.5)
```

여러 validation issue가 있을 경우 `;`로 연결된다.

예시:

```text
confidence: Confidence must be between 0.0 and 1.0 (value=1.5); latency_ms: Latency ms must be greater than or equal to zero (value=-100)
```

API layer에서는 이 메시지를 400 `core_validation_error` response의 `message`에 담는다.

예시:

```json
{
  "trace_id": "generated-trace-id",
  "error_type": "core_validation_error",
  "message": "confidence: Confidence must be between 0.0 and 1.0 (value=1.5)",
  "details": []
}
```

---

## 9. API Validation Failure Format

API validation 실패 시 FastAPI/Pydantic layer에서 422 `api_validation_error`를 반환한다.

예시:

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

이 응답도 trace_id contract를 따른다.

```text
response.body.trace_id == response.headers["X-Trace-Id"]
```

---

## 10. Why Invalid Input Does Not Become Uncertainty

Invalid input과 uncertainty는 다르다.

예를 들어:

```text
confidence = None
```

은 confidence 정보가 없는 상태이다.

```text
confidence = 1.5
```

는 confidence 값이 존재하지만 허용 범위를 위반한 상태이다.

두 경우를 모두 uncertainty로 처리하면 문제가 생긴다.

```text
잘못된 데이터가 정상적인 판단 제한 요소처럼 pipeline을 통과할 수 있다.
```

따라서 invalid input은 pipeline 초반에서 차단한다.

---

## 11. Why Missing Input Does Not Always Become Validation Error

일부 missing input은 실제 운영 상황에서 발생할 수 있다.

예를 들어 모델 응답에 confidence가 없거나 model_version이 누락될 수 있다.

이런 경우를 모두 validation error로 차단하면 시스템은 정보 부족 상태를 구조화할 수 없다.

따라서 이 프로젝트는 missing input을 필드 역할에 따라 구분한다.

```text
confidence = None
→ uncertainty

model_version = None
→ uncertainty

decision_type = None
→ evaluation limit

latency_ms = None
→ missing field

error_code = None
→ no uncertainty signal
```

이렇게 하면 시스템은 잘못된 입력은 차단하면서도 정보 부족으로 인한 판단 제한은 구조적으로 표현할 수 있다.

---

## 12. Validation Policy Summary

```text
API type / format error
→ 422 api_validation_error
→ core pipeline 진입 전 차단

Core domain error
→ 400 core_validation_error
→ risk / uncertainty로 해석하지 않음

missing confidence
→ uncertainty

missing model_version
→ uncertainty

missing decision_type
→ evaluation limit

missing latency_ms
→ missing field

missing error_code
→ uncertainty 아님

valid input
→ pipeline 계속 진행
```

Validation은 단순한 입력 검사 단계가 아니다.

이 시스템에서 validation은 다음을 보장한다.

- 잘못된 입력은 판단 대상이 되지 않는다.
- 정보 부족은 별도로 구조화된다.
- risk와 uncertainty는 validation 이후 단계에서만 해석된다.
- API validation과 core validation은 분리된다.
- system failure는 risk_score로 위장하지 않는다.

---

## 13. Summary

Validation Policy의 핵심은 다음과 같다.

- 값이 잘못된 경우와 값이 없는 경우를 구분한다.
- API 형식 오류와 core domain 오류를 구분한다.
- system failure와 risk signal을 구분한다.

이 구분을 통해 시스템은 invalid input을 risk나 uncertainty로 오해하지 않고 missing input은 판단 제한 요소로 구조화할 수 있다.

따라서 validation은 전체 decision pipeline의 첫 번째 안전장치이다.