# Uncertainty separation: Risk vs Uncertainty

## 목적

이 시스템은 위험강도(Risk)와 판단의 불확실성(Uncertainty)을 분리하여 판단 구조의 의미를 보존한다.

---

## 1. 문제 정의

기존의 시스템에서는 불확실성을 다음과 같이 처리하는 경향이 있다:
- 위험수준으로 흡수
- 점수로 압축
- 단순 human review 조건으로 변환

이러한 방식은 불확실성을 독립 개념으로 보존하지 못한다.

---

## 2. 붕괴 패턴

> ### Risk 흡수

```
if uncertainty_high:
  level = CRITICAL
```
- 불확실성이 위험으로 변형됨

> ### Score 압축

```
score = risk + uncertainty
```
- 의미가 다른 두 축이 단일 값으로 압축됨

> ### 단순 매핑

```
human_required = uncertainty_high
```
- 불확실성의 구조가 제거됨

---

## 3. 설계 결정

- uncertainty는 risk와 독립된 메타-판단 신호이다
- uncertainty는 특정 조건(정보 불완전성, 경계 불안전성, 규칙 충돌성, 해석 제약성 등)에 의해 생성된다.
- human_review는 uncertainty 자체가 아니라 이를 해석한 결과이다

---

## 4. 생성 vs 승격

- uncertainty는 생성된다
- human_review는 승격된다

이 둘은 동일한 개념이 아니다.

---

## 5. 현재 단계의 컷라인

- uncertainty의 세부 유형 분해는 아직 설계 미결정 상태로 둔다
- human_review 승격 기준은 아직 확정하지 않는다

