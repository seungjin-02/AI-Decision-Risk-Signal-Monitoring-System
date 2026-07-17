# event_validation.py Code Analysis

## Goal

목표는 event_validation.py의 코드를 함수 단위로 분석하고 validation 단계의 책임과 한계를 명확히 이해하는 것이다.

---

## File Responsibility

event_validation.py는 DecisionEvent가 core pipeline에 진입하기 전에 invalid input을 차단한다.

이 파일은 다음 일을 하지 않는다.

- risk signal 생성
- uncertainty signal 생성
- score 계산
- gate 해석
- action 추천
- AlertOutput 생성

---

## Code Structure

### ValidationIssue

ValidationIssue는 validation 실패 하나를 표현하는 객체다.

field_name은 문제가 발생한 필드 이름이고, message는 실패 이유이며, value는 문제가 된 실제 값이다.

이 객체가 필요한 이유는 validation 실패를 단순 문자열 하나로 끝내지 않고, 어떤 필드가 왜 실패했는지 구조적으로 보존하기 위해서다.

예를 들어 confidence=1.5가 들어오면 다음과 같은 issue가 생성될 수 있다.

```
ValidationIssue(
    field_name="confidence",
    message="confidence must be between 0.0 and 1.0",
    value=1.5
)
```

### ValidationResult

ValidationResult는 전체 validation 결과를 표현한다.

is_valid는 전체 입력이 유효한지 여부를 나타내고, issues는 발견된 모든 validation 문제를 담는다.

bool 하나만 반환하지 않고 issues list를 가지는 이유는, 하나의 입력에서 여러 문제가 동시에 발견될 수 있기 때문이다.

예를 들어 event_id가 비어 있고 confidence가 1.5라면, validation은 첫 번째 오류에서 멈추지 않고 두 issue를 모두 수집할 수 있다.

이 구조는 사용자나 API client에게 더 구체적인 피드백을 줄 수 있다.

### validate_event()

validate_event()는 event_validation.py의 public entrypoint이며 DecisionEvent가 core pipeline에 진입할 수 있는지 판단한다.

이 함수는 먼저 빈 issues 리스트를 생성한 뒤 event_id, confidence, latency_ms, decision_type, metadata에 대한 필드별 검증 함수를 순서대로 호출한다.

각 _validate_xxx 함수는 ValidationIssue를 반환하지 않고, 전달받은 issues 리스트에 문제를 직접 append한다. 따라서 validate_event()는 모든 필드 검증이 끝난 뒤 issues 리스트의 길이를 기준으로 is_valid를 계산한다.

### event_id validation hardening direction

기존 _validate_event_id()는 str(event.event_id).strip()을 사용하기 때문에 event_id=123 같은 non-string 값이 "123"으로 변환되어 validation을 통과할 수 있다.

이는 validation 단계가 invalid input을 차단하는 대신 암묵적으로 변환하는 동작이므로 적절하지 않다.

개선 방향 및 결과

1. event_id가 None인지 검사한다.
2. event_id가 str 타입인지 검사한다.
3. str 타입인 경우에만 strip()으로 빈 문자열 여부를 검사한다.

이렇게 하면 validation은 입력 계약 위반을 명확히 차단하고 normalization은 이미 valid한 event_id를 표준화하는 역할만 수행할 수 있다.

### _validate_confidence()

_validate_confidence()는 confidence가 None이거나 bool이 아닌 int/float인지 먼저 확인하고, 값이 존재하는 경우 0.0 이상 1.0 이하인지 검사해야 한다. 

특히 Python에서는 bool이 int처럼 취급될 수 있으므로, confidence=True나 confidence=False가 1.0 또는 0.0처럼 통과하지 않도록 bool 타입을 별도로 차단해야 한다.

### _validate_latency_ms()

_validate_latency_ms()는 latency_ms가 core pipeline에 들어갈 수 있는 유효한 지연 시간 값인지 검사한다.

이 함수에서 latency_ms=None은 invalid로 처리하지 않는다. latency 정보가 없는 것은 입력 형식 오류가 아니라 평가 정보가 누락된 상태일 수 있기 때문이다. 또한 값이 존재하는 경우 latency_ms는 0 이상의 정수여야 한다.

특히 Python에서는 bool이 int처럼 취급될 수 있으므로, confidence=True나 confidence=False가 1.0 또는 0.0처럼 통과하지 않도록 bool 타입을 별도로 차단해야 한다.

### _validate_decision_type()

_validate_decision_type()은 decision_type이 core pipeline에서 해석 가능한 의사결정 타입인지 검사한다.

값이 존재하는 경우 decision_type은 approve 또는 reject 중 하나여야 한다. 현재 구현은 str(event.decision_type).strip().lower()를 사용해 공백 제거와 소문자화를 수행한 뒤 허용값을 검사한다.

이 방식은 str() 변환 때문에 decision_type=123 같은 non-string 값이 "123"으로 변환된 뒤 invalid value로 처리된다. 결과적으로 invalid가 되기는 하지만 실제 문제는 allowed value 위반이 아니라 type contract 위반이다.

따라서 이번 고도화에서는 decision_type이 None인지 먼저 확인하고, None이 아니라면 string 타입인지 검사한 뒤 strip/lower 및 allowed value 검사를 수행하는 방식이 더 적절하다.

또한 decision_type="" 또는 decision_type=" "를 missing으로 볼지 invalid로 볼지 정책 결정이 필요하다. core contract를 엄격하게 가져간다면 None은 missing으로 허용하되 빈 문자열은 invalid로 차단하는 것이 더 명확하다고 판단한다.

### _validate_metadata()

_validate_metadata()는 metadata가 core pipeline에서 사용할 수 있는 확장 정보 컨테이너인지 검사한다.

metadata는 추가 정보를 담는 필드이므로 dict 형태여야 한다. metadata={}는 부가 정보가 없는 정상 상태로 볼 수 있다.

다만 현재 검증은 metadata 내부의 key/value 타입까지 확인하지는 않는다. 향후 audit log나 JSON serialization 안정성을 강화하려면 metadata key를 string으로 제한하거나, value를 JSON-serializable 타입으로 제한하는 정책을 추가할 수 있다.






