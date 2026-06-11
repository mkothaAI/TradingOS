from __future__ import annotations

from datetime import datetime, timezone

import pytest

from backend.schemas import (
    AlertEvent,
    AlertRoutingHint,
    AlertSeverity,
    AlertSeverityCode,
    AlertSourceKind,
    AlertTrigger,
    AlertTriggerType,
    EvidenceContext,
    FreshnessEnvelope,
    FreshnessLabel,
    MonitoringCondition,
    MonitoringConditionType,
    MonitoringState,
    MonitoringStateStatus,
    PostEntryContext,
    ThesisBreakageEvent,
    ThesisBreakageType,
)
from backend.schemas.shared import SourceLink


@pytest.fixture

def freshness_envelope() -> FreshnessEnvelope:
    return FreshnessEnvelope(
        freshness_label=FreshnessLabel.REAL_TIME,
        evidence_timestamp=datetime(2026, 5, 25, 13, 0, tzinfo=timezone.utc),
        received_at=datetime(2026, 5, 25, 13, 0, 12, tzinfo=timezone.utc),
        delay_seconds=12,
        staleness_seconds=0,
    )


@pytest.fixture

def evidence_context(freshness_envelope: FreshnessEnvelope) -> EvidenceContext:
    return EvidenceContext(
        ticker="AAPL",
        analysis_id="analysis-alert-1",
        verdict_ref="verdict-alert-1",
        evidence_ids=["ev-alert-1"],
        source_links=[SourceLink(rule_id="rule-alert-1", file="alerts.py")],
        primary_topics=["alerts", "monitoring"],
        freshness=freshness_envelope,
        provenance_summary="alert evidence",
    )


@pytest.fixture

def monitoring_condition(freshness_envelope: FreshnessEnvelope, evidence_context: EvidenceContext) -> MonitoringCondition:
    return MonitoringCondition(
        condition_id="cond-alert-1",
        condition_type=MonitoringConditionType.THESIS_BREAKAGE,
        condition_name="support break",
        condition_description="Price closes below support",
        trigger_basis="daily close below support",
        threshold="195",
        comparison_operator="<=",
        severity_hint="high",
        freshness=freshness_envelope,
        evidence_context=evidence_context,
    )


@pytest.fixture

def monitoring_state(
    freshness_envelope: FreshnessEnvelope,
    evidence_context: EvidenceContext,
    monitoring_condition: MonitoringCondition,
) -> MonitoringState:
    return MonitoringState(
        state_id="state-alert-1",
        context_id="ctx-alert-1",
        ticker="AAPL",
        symbolic_verdict_ref="verdict-alert-1",
        status=MonitoringStateStatus.THESIS_AT_RISK,
        last_checked_at=datetime(2026, 5, 25, 13, 1, tzinfo=timezone.utc),
        active_condition_ids=[monitoring_condition.condition_id],
        current_conditions=[monitoring_condition],
        freshness=freshness_envelope,
        evidence_context=evidence_context,
    )


@pytest.fixture

def thesis_breakage_event(
    freshness_envelope: FreshnessEnvelope,
    evidence_context: EvidenceContext,
    monitoring_state: MonitoringState,
) -> ThesisBreakageEvent:
    return ThesisBreakageEvent(
        event_id="event-alert-1",
        state_id=monitoring_state.state_id,
        context_id=monitoring_state.context_id,
        ticker=monitoring_state.ticker,
        symbolic_verdict_ref=monitoring_state.symbolic_verdict_ref,
        condition_id=monitoring_state.current_conditions[0].condition_id,
        breakage_type=ThesisBreakageType.THESIS_BREAKAGE,
        observed_at=datetime(2026, 5, 25, 13, 2, tzinfo=timezone.utc),
        evidence_context=evidence_context,
        freshness=freshness_envelope,
        summary="support broke and the thesis is at risk",
        requires_reassessment=True,
    )


@pytest.fixture

def alert_trigger(
    freshness_envelope: FreshnessEnvelope,
    evidence_context: EvidenceContext,
    monitoring_condition: MonitoringCondition,
) -> AlertTrigger:
    return AlertTrigger(
        trigger_id="trigger-alert-1",
        condition_id=monitoring_condition.condition_id,
        trigger_type=AlertTriggerType.THRESHOLD_BREACH,
        trigger_basis="daily close crossed below the support threshold",
        trigger_value="194.80",
        threshold=monitoring_condition.threshold,
        comparison_operator=monitoring_condition.comparison_operator,
        evidence_context=evidence_context,
        freshness=freshness_envelope,
    )


@pytest.fixture

def alert_severity(freshness_envelope: FreshnessEnvelope) -> AlertSeverity:
    return AlertSeverity(
        severity_code=AlertSeverityCode.HIGH,
        severity_label="high",
        severity_rank=3,
        escalation_needed=True,
        freshness=freshness_envelope,
    )


def test_alert_event_links_monitoring_sources_without_collapsing_boundaries(
    freshness_envelope: FreshnessEnvelope,
    evidence_context: EvidenceContext,
    monitoring_state: MonitoringState,
    thesis_breakage_event: ThesisBreakageEvent,
    alert_trigger: AlertTrigger,
    alert_severity: AlertSeverity,
) -> None:
    alert = AlertEvent(
        alert_id="alert-1",
        ticker=monitoring_state.ticker,
        symbolic_verdict_ref=monitoring_state.symbolic_verdict_ref,
        source_kind=AlertSourceKind.MONITORING_STATE,
        source_id=monitoring_state.state_id,
        alert_type="watch_condition_triggered",
        severity=alert_severity,
        trigger=alert_trigger,
        routing_hint=AlertRoutingHint(
            hint_id="hint-1",
            priority=1,
            audience="analyst",
            urgency="immediate",
            dedupe_key="AAPL:cond-alert-1",
            suppression_hint="group repeated alerts",
            display_hint="surface in review queue",
        ),
        summary="Support broke and review is needed.",
        observed_at=datetime(2026, 5, 25, 13, 3, tzinfo=timezone.utc),
        evidence_context=evidence_context,
        freshness=freshness_envelope,
        requires_review=True,
    )

    assert alert.source_id == monitoring_state.state_id
    assert alert.trigger.condition_id == monitoring_state.current_conditions[0].condition_id
    assert thesis_breakage_event.state_id == monitoring_state.state_id
    assert alert.requires_review is True
    assert alert.severity.severity_code == AlertSeverityCode.HIGH


def test_alert_event_requires_utc_observed_at(
    freshness_envelope: FreshnessEnvelope,
    evidence_context: EvidenceContext,
    alert_trigger: AlertTrigger,
    alert_severity: AlertSeverity,
) -> None:
    with pytest.raises(ValueError, match="observed_at must be UTC-aware"):
        AlertEvent(
            alert_id="alert-bad",
            ticker="AAPL",
            symbolic_verdict_ref="verdict-alert-1",
            source_kind=AlertSourceKind.THESIS_BREAKAGE_EVENT,
            source_id="event-alert-1",
            alert_type="thesis_breakage",
            severity=alert_severity,
            trigger=alert_trigger,
            summary="bad timestamp",
            observed_at=datetime(2026, 5, 25, 13, 3),
            evidence_context=evidence_context,
            freshness=freshness_envelope,
            requires_review=True,
        )


def test_alert_trigger_requires_condition_id(
    freshness_envelope: FreshnessEnvelope,
    evidence_context: EvidenceContext,
) -> None:
    with pytest.raises(ValueError, match="condition_id"):
        AlertTrigger(
            trigger_id="trigger-bad",
            condition_id="",
            trigger_type=AlertTriggerType.STATE_CHANGED,
            trigger_basis="state changed",
            evidence_context=evidence_context,
            freshness=freshness_envelope,
        )


def test_alert_routing_hint_remains_advisory_only() -> None:
    hint = AlertRoutingHint(
        hint_id="hint-2",
        audience="review_queue",
        urgency="soon",
        suppression_hint="group duplicates",
        display_hint="show in analyst queue",
    )

    assert hint.hint_id == "hint-2"
    assert hint.freshness is None
