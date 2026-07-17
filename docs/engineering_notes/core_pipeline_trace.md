# Core Pipeline Trace

## Goal

오늘의 목표는 core 코드를 수정하지 않고, 대표 DecisionEvent가 AlertOutput으로 변환되는 전체 흐름을 손으로 추적하는 것이다.

---

## Current Pipeline

```text
DecisionEvent
→ ValidationResult
→ NormalizedEvent
→ EvaluationContext
→ RuleEvaluation
→ Signal
→ ScoreSummary
→ GateInputs
→ GateDecision
→ ActionRecommendation
→ AlertOutput
```
---

## Event A — Normal Event

### Input

```
DecisionEvent(
    event_id="evt_normal_001",
    decision_type="approve",
    confidence=0.9,
    latency_ms=800,
    model_version="v1",
    error_code=None,
    metadata={}
)
```

---

### Step Trace

-> ValidationResult | is_valid = True, issues = []
>> event_id가 있고, confidence=0.9는 0.0~1.0 범위 안이며, latency_ms=800은 0 이상이고, decision_type="approve"는 허용값이다.

-> NormalizedEvent | event_id="evt_normal_001", decision_type="approve", confidence=0.9, latency_ms=800, model_version="v1", error_code=None, metadata={}
>> normalize_event가 문자열 공백 제거, decision_type 소문자화, confidence float 변환, latency int 변환, metadata 복사를 수행한다.

-> EvaluationContext | missing_fields=["error_code"], evaluation_limits=[], field_presence={"decision_type": True, "confidence": True, "latency_ms": True, "model_version": True, "error_code": False}
>> 현재 context는 error_code도 추적 대상에 넣기 때문에 error_code=None이면 missing_fields에 들어간다. 수정 예정.

-> Triggered Rules | None
>> confidence가 0.9라 low confidence가 아니고, latency_ms=800은 high latency 기준 2000보다 낮고, confidence/model_version도 존재하며, error_code도 없다.

-> Signals | []
>> trigger된 rule이 없으므로 SignalGeneration에서 signal이 생성되지 않는다.

-> ScoreSummary | risk_score=0, uncertainty_score=0
>> risk signal도 uncertainty signal도 없기 때문에 둘 다 0이다.

-> GateInputs | risk_score=0, uncertainty_score=0, has_high_risk_signal=False, has_stability_signal=False
>> signal이 없으므로 high risk signal도 stability signal도 없다.

-> GateDecision | final_level=RiskLevel.INFO, boundary=DecisionBoundaryResult(auto_finalize_allowed=True, reason="automatic finalization is allowed"), human_review=HumanReviewRequirement(required=False, reason="human review is not required", source="decision_boundary"), gate_reason="risk signals remain low and do not require escalation")
>> risk_score가 0이고 uncertainty_score도 0이며 high-risk signal이 없으므로 INFO로 해석되고 human review는 필요하지 않다.

-> ActionRecommendation | actions=["no_immediate_action_required"], message="risk signals remain low and do not require escalation"
>> human review가 필요 없고, high-risk signal도 없고, uncertainty signal도 없으며, final_level이 INFO이기 때문에 즉시 조치 없음 action이 생성된다.

-> AlertOutput | event_id="evt_normal_001", level="INFO", risk_score=0, uncertainty_score=0, human_required=False, recommended_actions=["no_immediate_action_required"], reason_summary="risk signals remain low and do not require escalation", signals=[], metadata={}
>> ActionRecommendation의 actions가 recommended_actions로 들어가고, message가 reason_summary로 들어간다.

---

## Event B — Low Confidence Approve

### Input

```
DecisionEvent(
    event_id="evt_low_conf_001",
    decision_type="approve",
    confidence=0.42,
    latency_ms=800,
    model_version="v1",
    error_code=None,
    metadata={}
)
```

-> ValidationResult | is_valid=True, issues=[]
>> event_id가 있고, confidence=0.42는 0.0~1.0 범위 안이며, latency_ms=800은 0 이상이고, decision_type="approve"는 허용값이다. 낮은 confidence는 validation error가 아니다.

-> NormalizedEvent | event_id="evt_low_conf_001", decision_type="approve", confidence=0.42, latency_ms=800, model_version="v1", error_code=None, metadata={}
>> 문자열 공백 제거, decision_type 소문자화, confidence float 변환, latency int 변환, metadata 복사가 수행된다.

-> EvaluationContext | missing_fields=["error_code"], evaluation_limits=[], field_presence={"decision_type": True, "confidence": True, "latency_ms": True, "model_version": True, "error_code": False}
>> 현재 context는 error_code도 추적 대상에 넣기 때문에 error_code=None이면 missing_fields에 들어간다. 수정 예정.

-> Triggered Rules | ["approve_confidence_low"]
>> decision_type="approve"이고 confidence=0.42가 threshold 0.6 이하이므로 approve_confidence_low rule이 trigger된다.

-> Signals | [Signal(rule_id="approve_confidence_low", category="risk", score=3, reason="approve decision with low confidence", evidence={"decision_type": "approve", "confidence": 0.42}, is_high_risk=False, metadata={})]
>> trigger된 rule이 Signal로 변환된다. rule의 category, score, reason, evidence_fields, is_high_risk가 Signal로 복사된다.

-> ScoreSummary | risk_score=3, uncertainty_score=0
>> category가 "risk"인 signal의 score 3이 risk_score에 합산된다. uncertainty signal은 없으므로 uncertainty_score는 0이다.

-> GateInputs | risk_score=3, uncertainty_score=0, has_high_risk_signal=False, has_stability_signal=False
>> low confidence signal은 is_high_risk=False이므로 high-risk signal은 없다. stability signal도 없다.

-> GateDecision | final_level=RiskLevel.WARN, boundary=DecisionBoundaryResult(auto_finalize_allowed=True, reason="automatic finalization is allowed"), human_review=HumanReviewRequirement(required=False, reason="human review is not required", source="decision_boundary"), gate_reason="medium risk with low uncertainty can be handled as warning-level interpretation"
>> risk_score=3은 medium risk zone이고, uncertainty_score=0이므로 WARN으로 해석된다. human review는 요구하지 않는다.

-> ActionRecommendation | actions=["monitor_closely"], message="medium risk with low uncertainty can be handled as warning-level interpretation"
>> human review가 필요 없고, high-risk signal도 없고, uncertainty signal도 없다. final_level=RiskLevel.WARN이므로 "monitor_closely"가 추가된다.

-> AlertOutput | event_id="evt_low_conf_001", level="WARN", risk_score=3, uncertainty_score=0, human_required=False, recommended_actions=["monitor_closely"], reason_summary="medium risk with low uncertainty can be handled as warning-level interpretation", signals=[...], metadata={}

---

## Event C — Timeout

### Input

```
DecisionEvent(
    event_id="evt_timeout_001",
    decision_type="approve",
    confidence=0.9,
    latency_ms=800,
    model_version="v1",
    error_code="timeout_01",
    metadata={}
)
```

-> ValidationResult | is_valid=True, issues=[]
>> 현재 validation은 error_code="timeout_01"을 invalid input으로 보지 않는다.

-> NormalizedEvent | event_id="evt_timeout_001", decision_type="approve", confidence=0.9, latency_ms=800, model_version="v1", error_code="timeout_01", metadata={}
>> error_code는 strip + lowercase 처리된다. 이미 "timeout_01"이므로 그대로 유지된다.

-> EvaluationContext | missing_fields=[], evaluation_limits=[], field_presence={"decision_type": True, "confidence": True, "latency_ms": True, "model_version": True, "error_code": True}
>> 모든 추적 필드가 존재한다. 따라서 missing_fields와 evaluation_limits는 비어 있다.

-> Triggered Rules | ["system_error_override"]
>> error_code="timeout_01"이 system_error_override의 threshold인 ["timeout_01", "gateway_failure"]에 포함되어 있다.

-> Signals | [Signal(rule_id="system_error_override", category="risk", score=0, reason="critical system error detected", evidence={"error_code": "timeout_01"}, is_high_risk=True, metadata={})]
>> 현재 system_error_override는 category="risk", score=0, is_high_risk=True인 rule로 정의되어 있다.

-> ScoreSummary | risk_score=0, uncertainty_score=0
>> signal category는 "risk"지만 score가 0이므로 risk_score는 증가하지 않는다. uncertainty signal도 없다.

-> GateInputs | risk_score=0, uncertainty_score=0, has_high_risk_signal=True, has_stability_signal=False
>> system_error_override signal의 is_high_risk=True 때문에 has_high_risk_signal=True가 된다.

-> GateDecision | final_level=RiskLevel.CRITICAL, boundary=DecisionBoundaryResult(auto_finalize_allowed=False, reason="automatic finalization is restricted"), human_review=HumanReviewRequirement(required=True, reason="human review is required", source="decision_boundary"), gate_reason="high-risk signal triggered critical interpretation and requires human review"
>> GateInterpretation은 has_high_risk_signal=True이면 risk_score와 무관하게 CRITICAL로 해석하고 human review를 요구한다.

-> ActionRecommendation | actions=["human_review_required", "immediate_investigation", "escalate_incident"], message="high-risk signal triggered critical interpretation and requires human review"
>> human review가 필요하므로 "human_review_required", high-risk signal이 있으므로 "immediate_investigation", final_level이 CRITICAL이므로 "escalate_incident"가 추가된다.

-> AlertOutput | event_id="evt_timeout_001", level="CRITICAL", risk_score=0, uncertainty_score=0, human_required=True, recommended_actions=["human_review_required", "immediate_investigation", "escalate_incident"], reason_summary="high-risk signal triggered critical interpretation and requires human review", signals=[...], metadata={}
>> score는 0이지만 high-risk gate 결과와 action recommendation이 최종 output으로 포장된다.

---

## Conclusion

trace를 통해 현재 core pipeline은 단계적으로 추적 가능하다는 점을 확인했다. 그러나 timeout_01 사례에서 system/model failure가 risk-category signal로 표현되고, is_high_risk=True를 통해 CRITICAL gate로 이어지는 문제가 확인되었다.

따라서 현재 핵심 문제는 risk_score 자체의 직접 오염이 아니라, failure와 risk 사이의 semantic contamination 및 gate-level contamination이다. 이후 고도화에서는 FailureClassification을 별도 단계로 분리하는 방향이 필요하다.













