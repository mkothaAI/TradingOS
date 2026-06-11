from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

from backend.schemas import (
    EvidenceContext,
    FreshnessEnvelope,
    FreshnessLabel,
    MonitoringCondition,
    MonitoringConditionType,
    MonitoringState,
    MonitoringStateStatus,
    PostEntryContext,
    PositionSide,
    ThesisBreakageEvent,
    ThesisBreakageType,
)
from backend.schemas.shared import SourceLink


@pytest.fixture
def freshness_envelope() -> FreshnessEnvelope:
    return FreshnessEnvelope(
        freshness_label=FreshnessLabel.REAL_TIME,
        evidence_timestamp=datetime(2026, 5, 25, 12, 0, tzinfo=timezone.utc),
        received_at=datetime(2026, 5, 25, 12, 0, 15, tzinfo=timezone.utc),
        delay_seconds=15,
        staleness_seconds=0,
    )


@pytest.fixture
def evidence_context(freshness_envelope: FreshnessEnvelope) -> EvidenceContext:
    return EvidenceContext(
        ticker="AAPL",
        analysis_id="analysis-monitor-1",
        verdict_ref="verdict-1",
        evidence_ids=["ev-monitor-1"],
        source_links=[SourceLink(rule_id="rule-monitor-1", file="monitoring.py")],
        primary_topics=["monitoring", "thesis-breakage"],
        freshness=freshness_envelope,
        provenance_summary="active-case evidence",
    )


@pytest.fixture
def post_entry_context(freshness_envelope: FreshnessEnvelope, evidence_context: EvidenceContext) -> PostEntryContext:
    return PostEntryContext(
        context_id="ctx-1",
        analysis_id="analysis-monitor-1",
        ticker="AAPL",
        symbolic_verdict_ref="verdict-1",
        entry_timestamp=datetime(2026, 5, 25, 12, 5, tzinfo=timezone.utc),
        entry_price=200.0,
        position_side=PositionSide.LONG,
        planned_hold_time="2 weeks",
        capital_at_risk=1000.0,
        evidence_context=evidence_context,
        freshness=freshness_envelope,
    )


@pytest.fixture
def monitoring_condition(freshness_envelope: FreshnessEnvelope, evidence_context: EvidenceContext) -> MonitoringCondition:
    return MonitoringCondition(
        condition_id="cond-1",
        condition_type=MonitoringConditionType.THESIS_BREAKAGE,
        condition_name="break thesis",
        condition_description="Price closes below support",
        trigger_basis="daily close below support",
        threshold="support at 195",
        comparison_operator="<",
        severity_hint="high",
        freshness=freshness_envelope,
        evidence_context=evidence_context,
    )


@pytest.fixture
def monitoring_state(
    freshness_envelope: FreshnessEnvelope,
    evidence_context: EvidenceContext,
    post_entry_context: PostEntryContext,
    monitoring_condition: MonitoringCondition,
) -> MonitoringState:
    return MonitoringState(
        state_id="state-1",
        context_id=post_entry_context.context_id,
        ticker="AAPL",
        symbolic_verdict_ref="verdict-1",
        status=MonitoringStateStatus.WATCHING,
        last_checked_at=datetime(2026, 5, 25, 12, 6, tzinfo=timezone.utc),
        active_condition_ids=[monitoring_condition.condition_id],
        current_conditions=[monitoring_condition],
        state_summary="case remains under watch",
        freshness=freshness_envelope,
        evidence_context=evidence_context,
    )


def test_post_entry_context_requires_utc_entry_timestamp(post_entry_context: PostEntryContext) -> None:
    assert post_entry_context.position_side == PositionSide.LONG
    assert post_entry_context.entry_timestamp.tzinfo == timezone.utc


def test_monitoring_state_references_current_conditions(monitoring_state: MonitoringState) -> None:
    assert monitoring_state.current_conditions[0].condition_type == MonitoringConditionType.THESIS_BREAKAGE
    assert monitoring_state.active_condition_ids == ["cond-1"]


def test_monitoring_state_rejects_unknown_active_condition(
    freshness_envelope: FreshnessEnvelope,
    evidence_context: EvidenceContext,
    monitoring_condition: MonitoringCondition,
) -> None:
    with pytest.raises(ValueError, match="active_condition_ids must reference current_conditions"):
        MonitoringState(
            state_id="state-bad",
            context_id="ctx-1",
            ticker="AAPL",
            symbolic_verdict_ref="verdict-1",
            status=MonitoringStateStatus.WATCHING,
            last_checked_at=datetime(2026, 5, 25, 12, 6, tzinfo=timezone.utc),
            active_condition_ids=["missing-condition"],
            current_conditions=[monitoring_condition],
            freshness=freshness_envelope,
            evidence_context=evidence_context,
        )


def test_thesis_breakage_event_requires_state_and_condition_alignment(
    freshness_envelope: FreshnessEnvelope,
    evidence_context: EvidenceContext,
    monitoring_state: MonitoringState,
) -> None:
    event = ThesisBreakageEvent(
        event_id="event-1",
        state_id=monitoring_state.state_id,
        context_id=monitoring_state.context_id,
        ticker="AAPL",
        symbolic_verdict_ref="verdict-1",
        condition_id=monitoring_state.current_conditions[0].condition_id,
        breakage_type=ThesisBreakageType.THESIS_BREAKAGE,
        observed_at=datetime(2026, 5, 25, 12, 7, tzinfo=timezone.utc),
        evidence_context=evidence_context,
        freshness=freshness_envelope,
        summary="support broke intraday",
        requires_reassessment=True,
    )

    assert event.state_id == monitoring_state.state_id
    assert event.breakage_type == ThesisBreakageType.THESIS_BREAKAGE
    assert event.requires_reassessment is True


def test_thesis_breakage_event_requires_utc_observation(
    freshness_envelope: FreshnessEnvelope,
    evidence_context: EvidenceContext,
) -> None:
    with pytest.raises(ValueError, match="observed_at must be UTC-aware"):
        ThesisBreakageEvent(
            event_id="event-bad",
            state_id="state-1",
            context_id="ctx-1",
            ticker="AAPL",
            symbolic_verdict_ref="verdict-1",
            condition_id="cond-1",
            breakage_type=ThesisBreakageType.THESIS_BREAKAGE,
            observed_at=datetime(2026, 5, 25, 12, 7),
            evidence_context=evidence_context,
            freshness=freshness_envelope,
            requires_reassessment=True,
        )
