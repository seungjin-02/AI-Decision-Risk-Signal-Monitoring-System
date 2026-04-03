# Decision Boundary

이 시스템은 자동화의 범위를 명시적으로 제한한다.

---

## Principle

- 시스템은 모든 상황에서 판단을 자동화하지 않는다.
- 자동화는 판단 가능성이 아니라 책임 가능성을 기준으로 제한한다.

---
## Core Definition

Decision Boundary는 시스템이 감당할 수 있는 판단 책임의 범위를 정의하는 단계이다.

- risk는 상황의 위험도이다
- uncertainty는 판단의 신뢰도이다
- boundary는 책임 허용 범위이다

따라서 Decision Boundary는 risk나 uncertainty에 종속되지 않는다.

## Boundary Decision Logic

시스템은 다음 조건에서 판단을 중단한다

### 1. 책임 불명확성

- 현재 판단 결과에 대한 책임 주체를 명확히 정의할 수 없는 경우

### 2. 근거 불충분

- 자동 확정을 정당화할 수 있는 최소 근거가 보존되지 않는 경우

### 3. 결론 불안정성

- 입력 변화 또는 해석 차이에 따라 판단 결과가 쉽게 변하는 경우

### 4. 설명 불가능성

- 현재 구조로 판단 이유를 명시적으로 설명할 수 없는 경우

위 조건 중 하나라도 충족되면 시스템은 판단을 계속하지 않고 중단한다.

---

## What Boundary is NOT

> ### Risk 기반 경계

```
if level == CRITICAL:
  human_required = True
```

-> risk에 종속된 설계

> ### Uncertainty 기반 경계

```
if uncertainty:
  human_required = True
```

-> uncertainty에 종속된 설계

> ### Score 기반 경계

```
if risk + uncertainty > threshold:
  human_required = True
```

-> 의미 압축으로 인한 경계 붕괴

---

## Human Required

human_required는 단순한 fallback이 아니라 시스템이 판단을 중단하고 책임을 인간에게 전달하는 상태이다.

---

## Design Goal

이 시스템의 목표는 판단을 대신하는 것이 아니라 판단이 필요한 지점을 명확히 정의하는 것이다.
