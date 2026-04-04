# Structural Compression: Minimal Structure Validation

## 목적

이 문서는 현재 시스템의 구조를 축소 가능한지 검증하고 불필요한 개념을 제거해도 설계가 유지되는지를 확인하기 위해 작성되었다.

---

## 1. 문제 정의

현재까지 아래와 같은 판단을 위한 기본 구조가 형성되었다.

- RiskLevel
- UncertaintyState
- DecisionBoundaryResult
- HumanReviewRequirement
- GateDecision

이 구조는 의미적으로 명확하지만 다음과 같은 질문이 발생한다:

- 이 구조는 과도한 분리인가 아님 제거 불가능한 최소한의 구조인가

---

## 2. 압축 대상

이 단계에서는 다음 두 영역을 주요 압축 대상으로 설정한다:

### 2-1. Boundary vs Human Review

- DecisionBoundaryResult
- HumanReviewRequirement

### 2-2. Reason 계층

- uncertainty.reason
- boundary.reason
- human_review.reason
- gate_reason

---

## 3. 압축 실험 A — Boundary vs Human Review

### 시도 1. HumanReviewRequirement 제거

```
DecisionBoundaryResult:
  auto_finalize_allowed: bool
```

-> human_review는 not auto_finalize_allowed로 해석

결과
- 경계 판단과 운영 제약이 동일한 의미로 압축됨
- human_review의 독립 의미가 사라짐
- 의미 분리 원칙이 약화됨

결론
- HumanReviewRequirement는 제거할 수 없다

### 시도 2: DecisionBoundaryResult 제거

-> human_review만 유지

결과
- human_review의 생성 출처가 불명확해짐
- risk / uncertainty에서 직접 생성될 위험 발생
- 경계 해석 구조 붕괴

결론
- DecisionBoundaryResult는 제거할 수 없다

### 최종판단

- DecisionBoundaryResult = 경계 해석 결과
- HumanReviewRequirement = 운영 제약 표현

두 개념은 역할이 다르므로 분리 유지하기로 결정한다.

---

## 4. 압축 실험 B - Reason 구조

### 시도 1: gate_reason 제거

결과
- 최종 결론 이유 손실

결론
- gate_reason은 하위 reason의 반복이 아니라 최종 판단에 대한 종합 설명일 경우에만 유지한다

### 시도 2: 하위 reason 제거

결과
- uncertainty 발생 이유 손실
- boundary 중단 이유 손실
- human_review 근거 손실

결론
- 하위 reason은 제거할 수 없다

### 최종판단

- 하위 reason은 각각의 의미를 설명
- gate_reason은 최종 결론을 설명

두 개념은 역할이 다르므로 분리 유지하기로 결정한다

## 5. 최종 구조 판단
압축 실험 결과 다음 구조는 제거 불가능한 최소 구조로 설계, 유지한다:

- RiskLevel
- UncertaintyState
- DecisionBoundaryResult
- HumanReviewRequirement
- GateDecision



















