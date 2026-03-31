# Decision Boundary

이 시스템은 자동화의 범위를 명시적으로 제한한다.

---

## Principle

* 시스템은 모든 상황에서 판단을 자동화하지 않는다.

* 판단 가능성과 책임 범위를 기준으로 자동화를 제한한다.

---

## Decision Flow

* 낮은 위험 + 낮은 불확실성
  → 자동 해석 가능

* 높은 위험 + 낮은 불확실성
  → escalation 가능

* 높은 위험 + 높은 불확실성
  → 자동 판단 중단 + human_required

---

## Human Required

human_required는 단순한 fallback이 아니라 시스템이 판단을 중단하고 책임을 인간에게 전달하는 상태이다.

---

## Design Goal

이 시스템의 목표는 판단을 대신하는 것이 아니라 판단이 필요한 지점을 명확히 정의하는 것이다.
