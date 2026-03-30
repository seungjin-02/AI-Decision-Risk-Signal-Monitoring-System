# AI Decision Risk Signal Monitoring System

AI 의사결정 과정에서 위험 신호와 불확실성을 구조화하고 인간의 개입이 필요한 시점을 명확히 정의하는 시스템

---

## Executive Summary

이 프로젝트는 AI 의사결정을 자동화하는 것이 아니라 위험 신호와 불확실성을 구조화하여 인간의 판단을 보조하는 것을 목표로 한다.

기존의 단순 threshold 또는 score 기반 시스템은 위험과 불확실성을 구분하지 못하고 자동화와 책임의 경계를 흐리는 단점이 있다.

이 시스템은 다음을 명확히 분리한다:

* 위험 신호 (Risk Signals)
* 불확실성 (Uncertainty)
* 판단 책임 (Decision Responsibility)

이를 통해 위험 신호를 구조적으로 드러내고 불확실한 상황에서 자동 판단을 제한하며 인간 개입이 필요한 지점을 명확히 정의한다.

---

## Problem Statement

기존의 alert/monitoring 시스템은 내부적으로 판단을 수행한 뒤 그 결과만을 운영자에게 전달하는 구조이다.
이러한 구조는 운영자가 해당 판단이 어떤 근거와 과정을 통해 이루어졌는지 확인하기 어려우며 그 결과에 대한 대응 또한 제한적인 정보에 의존하게 된다.

특히 이러한 구조는 다음과 같은 문제를 발생시킨다:

* 판단의 근거와 과정이 충분히 드러나지 않음
* 결과에 대한 대응이 어려움
* 자동화된 판단과 인간 책임 사이의 경계가 모호해짐

또한 threshold 또는 score 기반의 단순 규칙 시스템은 조건문 형태의 판단만을 제공하기 때문에 왜 해당 결과가 도출되었는지에 대한 구조적 설명이 부족하다는 단점이 있다.

그 결과 위험과 불확실성이 구분되지 않고 자동화된 판단이 과도하게 적용되거나 책임 주체가 명확하게 정의되지 않는 문제가 발생한다.

이 프로젝트는 이러한 문제를 해결하기 위해 AI 의사결정 과정에서의 판단 구조와 책임 관리를 명확히 정의하고 그 과정을 투명하게 드러내는 것을 목표로 한다.

---

## Core Design Principles

1. **AI는 판단 주체가 아니다**
   
   * 시스템은 결론이 아니라 구조를 제공한다
     
2. **위험과 불확실성을 분리한다**

   * 불확실성은 위험을 낮추지 않는다
   * 대신 자동 판단을 제한한다

3. **HUMAN_REQUIRED는 설계된 결과이다**

   * fallback이 아니라 의도된 상태이다

---

## System Architecture

```text
Event
 → Normalize
 → Evaluation Context
 → Rule Evaluation
 → Signal Generation
 → Score Aggregation
 → Gate Interpretation
 → Action Generation
 → Alert Output
```

각 단계는 역할이 명확히 분리되어 있으며 판단은 단일 지점(Gate)에서만 수행된다.

---

## Key Design Decisions

### Why CRITICAL is not determined by a simple score threshold

단순히 risk_score가 높다고 해서 모든 상황이 동일한 위험도를 가지는 것은 아니다.

특히 동일한 score라도 다음과 같은 차이가 존재할 수 있다:

* 입력 정보가 충분한 상태에서 발생한 높은 위험
* 입력 누락 또는 평가 불가능 상태로 인해 불확실성이 높은 상황에서의 위험

이 두 경우는 동일한 score를 가지더라도 자동으로 동일한 수준의 대응(CRITICAL)으로 처리하는 것은 적절하지 않다.

따라서 이 시스템은 단순 score threshold가 아닌:

* high_risk_signal (명확한 위험 신호)
* uncertainty (판단 가능성 제한 요소)

를 함께 고려하여 위험을 시스템에서 자동으로 확정할 것인지 또는 인간의 판단으로 넘길 것인지를 결정한다.

---

### Why uncertainty does not reduce risk

불확실성은 위험도를 낮추는 요소가 아니라 판단 가능성을 제한하는 요소이다.

위험(risk)은 주어진 입력과 규칙을 기반으로 판단 가능한 범위 내에서의 위험도를 의미한다. 
반면 불확실성(uncertainty)은 입력 누락, 평가 불가능 상태 등으로 인해 해당 위험을 얼마나 신뢰할 수 있는지를 나타낸다.

따라서 불확실성이 높다고 해서 위험이 낮아지는 것은 아니다. 대신 이 시스템은 해당 위험을 자동으로 확정하지 않고 판단을 보류한 뒤 인간의 개입(human_required)을 통해 처리하도록 한다.

---

### Why human_required is separated from level

위험 수준(level)과 인간 개입 여부(human_required)는 서로 다른 차원의 정보이다.

level은 위험의 크기를 나타내는 지표이며 human_required는 시스템이 해당 판단을 스스로 확정할 수 있는지 여부를 나타낸다.

이 둘을 분리함으로써, 위험도와 판단 책임을 동시에 표현할 수 있고 자동화의 한계를 명확히 드러낼 수 있다.

---

## Decision Boundary

이 시스템은 자동화의 범위를 명시적으로 제한한다.

* 낮은 위험 → 자동 해석 가능
* 높은 위험 + 낮은 불확실성 → escalation 가능
* 높은 위험 + 높은 불확실성 → 자동 판단 중단 + 인간 개입 필요

이를 통해 시스템이 과도하게 판단하지 않도록 하고 책임이 인간에게 명확히 전달되도록 한다.

---

## Example Flow

입력 이벤트:

```json
{
  "decision_type": "approve",
  "confidence": 0.52,
  "latency_ms": 2800
}
```

출력 결과:

* level: WARN
* human_required: True
* recommended_action: Human review required before proceeding

---

## What This System Does NOT Do

* 자동 승인 / 거절을 수행하지 않는다
* 최대 자동화를 목표로 하지 않는다
* 불확실성을 하나의 점수로 숨기지 않는다

대신:

* 불확실성을 드러낸다
* 위험 신호를 구조화한다
* 인간 개입이 필요한 시점을 명확히 한다

---

## Repository Structure

```
app/
  ├── models/
  ├── rules/
  ├── engine/
  ├── api/
  ├── repository/

docs/
  ├── architecture.md
  ├── decision-boundary.md
  ├── design-decisions.md
```

---

## Summary

이 프로젝트는 AI를 활용하여 결정을 자동화하는 시스템이 아니라,
**어디까지 자동화하고 어디서 멈춰야 하는지를 설계한 시스템**이다.
