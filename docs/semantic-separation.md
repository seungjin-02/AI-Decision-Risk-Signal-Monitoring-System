# Semantic Separation: level vs human_review

## 목적

위험 강도와 자동 판단 가능 여부를 분리하여 판단 구조의 의미를 보존한다.

---

## 1. 문제 정의

판단 결과는 다음 두 값을 포함한다.

- `level`: 위험 신호의 강도
- `human_review.required`: 자동 판단 가능 여부

두 값은 함께 출력되지만 서로 다른 의미를 가진다.

---

## 2. 핵심 설계 기준

- `level` → 위험의 크기
- `human_required` → 판단 권한 제약

위험 강도와 판단 권한은 동일한 기준이 아니다.

---

## 3. 구조 분리 필요성

### Case 1
LOW + human_required = True  
→ 위험은 낮지만 자동 판단 불가

### Case 2
CRITICAL + human_required = False  
→ 위험은 높지만 자동 판단 가능

### Case 3
WARN + human_required = 상황에 따라 다름  

### 결론

level과 human_required는 함수적으로 종속되지 않는다.

---

## 4. 금지되는 설계

### 결합 상태
`WARN_CRITICAL`
`WARN_AUTO`
`LOW_AUTO`

문제:

- 의미가 문자열에 숨어버림  
- 후속 로직이 상태 이름에 종속됨  
- 확장 시 조건문 수정 필요  

---

### 암묵적 매핑

`human_required = (level == CRITICAL)`

문제:
- 판단 권한이 위험도에 종속됨
- 불확실성, 정보 부족을 표현할 수 없음

## 5. 설계 결정

```
GateDecision:
  level: RiskLevel
  human_review: HumanReviewRequirement
```

- 두 값은 독립적으로 유지된다
- human_required는 별도 상태가 아니라 파생 값이다
- 단일 status로 결합하지 않는다

