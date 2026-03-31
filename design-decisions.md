# Design Decisions

이 문서는 시스템의 핵심 설계 선택과 그 이유를 설명한다.

---

## 1. Why CRITICAL is not determined by a simple score threshold

단순히 risk_score가 높다고 해서 모든 상황이 동일한 위험도를 가지는 것은 아니다.

특히 동일한 score라도 다음과 같은 차이가 존재할 수 있다:

* 입력 정보가 충분한 상태에서 발생한 높은 위험
* 입력 누락 또는 평가 불가능 상태로 인해 불확실성이 높은 상황에서의 위험

이 두 경우는 동일한 score를 가지더라도 자동으로 동일한 수준의 대응(CRITICAL)으로 처리하는 것은 적절하지 않다.

따라서 이 시스템은 단순 score threshold가 아닌:

* high_risk_signal (명확한 위험 신호)
* uncertainty (판단 가능성 제한 요소)

를 함께 고려하여 위험을 해석한다.

---

## 2. Why uncertainty does not reduce risk

불확실성은 위험도를 낮추는 요소가 아니라 판단 가능성을 제한하는 요소이다.

위험은 입력과 규칙을 기반으로 판단 가능한 범위 내에서의 위험도를 의미한다.
반면 불확실성은 입력 누락, 평가 불가능 상태 등으로 인해 해당 판단의 신뢰도를 제한하는 요소이다.

따라서 불확실성이 높다고 해서 위험이 낮아지는 것은 아니다.
대신 시스템은 자동 판단을 보류하고 인간 개입을 요구한다.

---

## 3. Why human_required is separated from level

위험 수준(level)과 인간 개입 여부(human_required)는 서로 다른 차원의 정보이다.

level은 위험의 크기를 나타내고 human_required는 해당 판단을 시스템이 확정할 수 있는지 여부를 나타낸다.

이 둘을 분리함으로써 위험도와 책임 구조를 동시에 표현할 수 있고 자동화의 한계를 명확히 드러낼 수 있다.

---

## 4. Why high_risk signals are restricted

high_risk는 모든 위험 신호에 적용되지 않고 명확한 판단 리스크 또는 시스템 오류 상황에서만 사용된다.

이를 통해 불필요한 CRITICAL escalation를 방지하고 gate의 기본 해석 구조를 유지한다.

---

## 5. Trade-off Considerations

이 시스템은 다음과 같은 trade-off를 가진다:

* 단순한 threshold 시스템보다 복잡도가 증가한다. 대신 판단 구조와 책임 경계를 명확히 할 수 있다

* 자동화 수준은 낮아질 수 있다. 대신 잘못된 자동화를 방지할 수 있다

이러한 선택은 성능 최적화보다 안정성과 책임 명확성을 우선한 결과이다.
