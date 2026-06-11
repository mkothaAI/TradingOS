from __future__ import annotations

import sys
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.schemas import (
    AlertEvent,
    AlertRoutingHint,
    AlertSeverity,
    AlertSeverityCode,
    AlertSourceKind,
    AlertTrigger,
    AlertTriggerType,
    EntryBias,
    EntryPlan,
    EvidenceContext,
    FollowUpAnswer,
    FollowUpAnswerType,
    FollowUpQuestion,
    FollowUpTarget,
    FollowUpTargetKind,
    FreshnessEnvelope,
    FreshnessLabel,
    InvalidationPlan,
    MonitoringCondition,
    MonitoringConditionType,
    MonitoringState,
    MonitoringStateStatus,
    OptionContractSnapshot,
    OptionContractType,
    OptionsProfile,
    RecommendationBlock,
    RecommendationBlockType,
    RecommendationStatus,
    RiskPlan,
    SizeInfo,
)
from backend.schemas.shared import SourceLink
from trading_os_v1.providers.dashboard_contracts import (
    DashboardAlertEventProjection,
    DashboardMonitoringStateProjection,
    DashboardOptionsProfileProjection,
    DashboardProjectionBundle,
    DashboardRecommendationBlockProjection,
    build_dashboard_projection_bundle,
    build_dashboard_shell_model,
    project_alert_event,
    project_monitoring_state,
    project_options_profile,
    project_recommendation_block,
)


def _freshness_envelope() -> FreshnessEnvelope:
    return FreshnessEnvelope(
        freshness_label=FreshnessLabel.REAL_TIME,
        evidence_timestamp=datetime(2026, 5, 25, 14, 0, tzinfo=timezone.utc),
        received_at=datetime(2026, 5, 25, 14, 0, 10, tzinfo=timezone.utc),
        delay_seconds=10,
        staleness_seconds=0,
    )


def _evidence_context(freshness_envelope: FreshnessEnvelope) -> EvidenceContext:
    return EvidenceContext(
        ticker="AAPL",
        analysis_id="analysis-transport-1",
        verdict_ref="verdict-transport-1",
        evidence_ids=["ev-transport-1"],
        source_links=[SourceLink(rule_id="rule-transport-1", file="transport.py")],
        primary_topics=["transport", "projection"],
        freshness=freshness_envelope,
        provenance_summary="projection evidence",
    )


def _follow_up_question(freshness_envelope: FreshnessEnvelope, evidence_context: EvidenceContext) -> FollowUpQuestion:
    return FollowUpQuestion(
        question_id="fuq-1",
        thread_id="thread-1",
        ticker="AAPL",
        target=FollowUpTarget(
            target_kind=FollowUpTargetKind.ADVISORY_AGENT,
            target_name="market_structure",
            display_name="Market Structure",
        ),
        question_text="Is the setup still intact?",
        asked_at=datetime(2026, 5, 25, 14, 1, tzinfo=timezone.utc),
        as_of_date=date(2026, 5, 25),
        evidence_context=evidence_context,
        follow_up_mode="watch_and_wait",
    )


def _follow_up_answer(freshness_envelope: FreshnessEnvelope, evidence_context: EvidenceContext) -> FollowUpAnswer:
    return FollowUpAnswer(
        answer_id="fua-1",
        question_id="fuq-1",
        ticker="AAPL",
        target=FollowUpTarget(
            target_kind=FollowUpTargetKind.ADVISORY_AGENT,
            target_name="market_structure",
            display_name="Market Structure",
        ),
        answer_text="The setup remains intact for now.",
        answer_type=FollowUpAnswerType.ADVISORY,
        generated_at=datetime(2026, 5, 25, 14, 2, tzinfo=timezone.utc),
        as_of_date=date(2026, 5, 25),
        evidence_context=evidence_context,
        freshness=freshness_envelope,
        supporting_rule_ids=["rule-transport-1"],
    )


def _recommendation_block(freshness_envelope: FreshnessEnvelope, evidence_context: EvidenceContext) -> RecommendationBlock:
    entry_plan = EntryPlan(
        entry_bias=EntryBias.LONG,
        timing_window="next session",
        capital_allocation=10.0,
        size_plan=SizeInfo(allowed_qty=10, notional=1000.0),
        entry_conditions=["close above resistance"],
        entry_triggers=["breakout confirmation"],
        entry_rationale="Momentum remains constructive.",
        freshness=freshness_envelope,
        evidence_context=evidence_context,
    )
    risk_plan = RiskPlan(
        risk_level="moderate",
        stop_loss="below prior swing low",
        risk_conditions=["trend remains intact"],
        risk_notes="Risk remains bounded.",
        freshness=freshness_envelope,
        evidence_context=evidence_context,
    )
    invalidation_plan = InvalidationPlan(
        invalidation_conditions=["breaks support"],
        invalidation_message="Thesis no longer holds.",
        reassessment_needed=True,
        freshness=freshness_envelope,
        evidence_context=evidence_context,
    )
    return RecommendationBlock(
        block_id="block-1",
        block_type=RecommendationBlockType.ENTRY,
        headline="Entry setup",
        summary="Constructive setup with explicit risk controls.",
        status=RecommendationStatus.SUPPORTIVE,
        evidence_context=evidence_context,
        freshness=freshness_envelope,
        entry_plan=entry_plan,
        risk_plan=risk_plan,
        invalidation_plan=invalidation_plan,
    )


def _options_profile(freshness_envelope: FreshnessEnvelope, evidence_context: EvidenceContext) -> OptionsProfile:
    contract_snapshot = OptionContractSnapshot(
        contract_id="contract-1",
        underlying_ticker="AAPL",
        contract_type=OptionContractType.CALL,
        expiry=date(2026, 6, 19),
        strike=210.0,
        freshness=freshness_envelope,
        evidence_context=evidence_context,
    )
    return OptionsProfile(
        profile_id="options-1",
        ticker="AAPL",
        as_of_date=date(2026, 5, 25),
        generated_at=datetime(2026, 5, 25, 14, 3, tzinfo=timezone.utc),
        symbolic_verdict_ref="verdict-transport-1",
        evidence_context=evidence_context,
        freshness=freshness_envelope,
        contract_snapshots=[contract_snapshot],
    )


def _monitoring_state(freshness_envelope: FreshnessEnvelope, evidence_context: EvidenceContext) -> MonitoringState:
    condition = MonitoringCondition(
        condition_id="cond-1",
        condition_type=MonitoringConditionType.THESIS_BREAKAGE,
        condition_name="support break",
        condition_description="Price closes below support.",
        trigger_basis="daily close below support",
        freshness=freshness_envelope,
        evidence_context=evidence_context,
    )
    return MonitoringState(
        state_id="state-1",
        context_id="ctx-1",
        ticker="AAPL",
        symbolic_verdict_ref="verdict-transport-1",
        status=MonitoringStateStatus.THESIS_AT_RISK,
        last_checked_at=datetime(2026, 5, 25, 14, 4, tzinfo=timezone.utc),
        active_condition_ids=[condition.condition_id],
        current_conditions=[condition],
        state_summary="watch list elevated",
        freshness=freshness_envelope,
        evidence_context=evidence_context,
    )


def _alert_event(
    freshness_envelope: FreshnessEnvelope,
    evidence_context: EvidenceContext,
    monitoring_state: MonitoringState,
) -> AlertEvent:
    severity = AlertSeverity(
        severity_code=AlertSeverityCode.HIGH,
        severity_label="high",
        severity_rank=3,
        escalation_needed=True,
        freshness=freshness_envelope,
    )
    trigger = AlertTrigger(
        trigger_id="trigger-1",
        condition_id=monitoring_state.current_conditions[0].condition_id,
        trigger_type=AlertTriggerType.THRESHOLD_BREACH,
        trigger_basis="daily close crossed below support threshold",
        trigger_value="194.8",
        threshold="195",
        comparison_operator="<=",
        evidence_context=evidence_context,
        freshness=freshness_envelope,
    )
    return AlertEvent(
        alert_id="alert-1",
        ticker="AAPL",
        symbolic_verdict_ref=monitoring_state.symbolic_verdict_ref,
        source_kind=AlertSourceKind.MONITORING_STATE,
        source_id=monitoring_state.state_id,
        alert_type="watch_condition_triggered",
        severity=severity,
        trigger=trigger,
        routing_hint=AlertRoutingHint(
            hint_id="hint-1",
            priority=1,
            audience="analyst",
            urgency="immediate",
        ),
        summary="Support broke and review is needed.",
        observed_at=datetime(2026, 5, 25, 14, 5, tzinfo=timezone.utc),
        evidence_context=evidence_context,
        freshness=freshness_envelope,
        requires_review=True,
    )


def test_projection_bundle_keeps_transport_shapes_flat() -> None:
    freshness_envelope = _freshness_envelope()
    evidence_context = _evidence_context(freshness_envelope)
    follow_up_question = _follow_up_question(freshness_envelope, evidence_context)
    follow_up_answer = _follow_up_answer(freshness_envelope, evidence_context)
    recommendation_block = _recommendation_block(freshness_envelope, evidence_context)
    options_profile = _options_profile(freshness_envelope, evidence_context)
    monitoring_state = _monitoring_state(freshness_envelope, evidence_context)
    alert_event = _alert_event(freshness_envelope, evidence_context, monitoring_state)

    bundle = build_dashboard_projection_bundle(
        follow_up_questions=[follow_up_question],
        follow_up_answers=[follow_up_answer],
        recommendation_blocks=[recommendation_block],
        options_profiles=[options_profile],
        monitoring_states=[monitoring_state],
        alert_events=[alert_event],
    )

    assert isinstance(bundle, DashboardProjectionBundle)
    assert bundle.follow_up_questions[0].target_name == "market_structure"
    assert bundle.recommendation_blocks[0].plan_kinds == ("entry", "risk", "invalidation")
    assert bundle.options_profiles[0].has_greeks is False
    assert bundle.monitoring_states[0].current_condition_ids == ("cond-1",)
    assert bundle.alert_events[0].routing_audience == "analyst"
    assert bundle.alert_events[0].severity_code == "high"


def test_projection_helpers_do_not_expose_nested_domain_models() -> None:
    freshness_envelope = _freshness_envelope()
    evidence_context = _evidence_context(freshness_envelope)
    monitoring_state = _monitoring_state(freshness_envelope, evidence_context)
    alert_event = _alert_event(freshness_envelope, evidence_context, monitoring_state)

    monitoring_projection = project_monitoring_state(monitoring_state)
    alert_projection = project_alert_event(alert_event)
    recommendation_projection = project_recommendation_block(_recommendation_block(freshness_envelope, evidence_context))
    options_projection = project_options_profile(_options_profile(freshness_envelope, evidence_context))

    assert isinstance(monitoring_projection, DashboardMonitoringStateProjection)
    assert isinstance(alert_projection, DashboardAlertEventProjection)
    assert isinstance(recommendation_projection, DashboardRecommendationBlockProjection)
    assert isinstance(options_projection, DashboardOptionsProfileProjection)
    assert not hasattr(alert_projection, "severity")
    assert not hasattr(alert_projection, "trigger")
    assert not hasattr(monitoring_projection, "current_conditions")
    assert not hasattr(options_projection, "contract_snapshots")


def test_dashboard_shell_model_carries_projection_bundle_through() -> None:
    freshness_envelope = _freshness_envelope()
    evidence_context = _evidence_context(freshness_envelope)
    bundle = build_dashboard_projection_bundle(
        follow_up_questions=[_follow_up_question(freshness_envelope, evidence_context)],
        follow_up_answers=[_follow_up_answer(freshness_envelope, evidence_context)],
        recommendation_blocks=[_recommendation_block(freshness_envelope, evidence_context)],
        options_profiles=[_options_profile(freshness_envelope, evidence_context)],
        monitoring_states=[_monitoring_state(freshness_envelope, evidence_context)],
        alert_events=[_alert_event(freshness_envelope, evidence_context, _monitoring_state(freshness_envelope, evidence_context))],
    )

    shell_model = build_dashboard_shell_model(
        health_summary={},
        evidence_summary={},
        eligibility_view={},
        diagnostics_bundle={"health_manager_present": False, "registry": {}},
        projection_bundle=bundle,
    )

    assert shell_model["projection_bundle"]["alert_events"][0]["alert_id"] == "alert-1"
