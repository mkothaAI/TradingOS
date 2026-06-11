from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

from backend.schemas import (
    EntryBias,
    EntryPlan,
    EvidenceContext,
    FollowUpTarget,
    FollowUpTargetKind,
    FreshnessEnvelope,
    FreshnessLabel,
    InvalidationPlan,
    MonitoringPlan,
    RecommendationBlock,
    RecommendationBlockType,
    RecommendationStatus,
    RiskPlan,
    TickerAnalysisPackage,
)
from backend.schemas.shared import SourceLink


@pytest.fixture

def freshness_envelope() -> FreshnessEnvelope:
    return FreshnessEnvelope(
        freshness_label=FreshnessLabel.SNAPSHOT,
        evidence_timestamp=datetime(2026, 5, 25, 12, 0, tzinfo=timezone.utc),
        received_at=datetime(2026, 5, 25, 12, 1, tzinfo=timezone.utc),
        staleness_seconds=60,
    )


@pytest.fixture

def evidence_context(freshness_envelope: FreshnessEnvelope) -> EvidenceContext:
    return EvidenceContext(
        ticker="AAPL",
        analysis_id="analysis-42",
        verdict_ref="verdict-42",
        evidence_ids=["e-1"],
        source_links=[SourceLink(rule_id="rule-42", file="analysis.py")],
        primary_topics=["entry", "risk"],
        freshness=freshness_envelope,
        provenance_summary="analysis snapshot",
    )


@pytest.fixture

def recommendation_block(evidence_context: EvidenceContext, freshness_envelope: FreshnessEnvelope) -> RecommendationBlock:
    entry_plan = EntryPlan(
        entry_bias=EntryBias.LONG,
        timing_window="next session",
        capital_allocation=10.0,
        entry_conditions=["breakout above resistance"],
        entry_triggers=["close above pivot"],
        entry_rationale="Momentum and structure are aligned.",
        freshness=freshness_envelope,
        evidence_context=evidence_context,
    )
    risk_plan = RiskPlan(
        risk_level="moderate",
        stop_loss="below prior swing low",
        risk_conditions=["volume remains supportive"],
        risk_notes="Risk is contained by the stop placement.",
        freshness=freshness_envelope,
        evidence_context=evidence_context,
    )
    invalidation_plan = InvalidationPlan(
        invalidation_level="medium",
        invalidation_conditions=["breaks below support"],
        invalidation_message="The thesis fails if support breaks.",
        reassessment_needed=True,
        freshness=freshness_envelope,
        evidence_context=evidence_context,
    )
    monitoring_plan = MonitoringPlan(
        monitoring_level="standard",
        monitoring_conditions=["watch follow-through"],
        review_frequency="daily",
        watch_notes="Track whether the move holds through the next session.",
        freshness=freshness_envelope,
        evidence_context=evidence_context,
    )

    return RecommendationBlock(
        block_id="block-1",
        block_type=RecommendationBlockType.ENTRY,
        headline="Entry setup",
        summary="The setup remains constructive with explicit risk controls.",
        status=RecommendationStatus.SUPPORTIVE,
        evidence_context=evidence_context,
        freshness=freshness_envelope,
        entry_plan=entry_plan,
        risk_plan=risk_plan,
        invalidation_plan=invalidation_plan,
        monitoring_plan=monitoring_plan,
        supporting_rule_ids=["rule-42"],
    )


def test_recommendation_package_uses_shared_evidence_and_freshness(
    evidence_context: EvidenceContext,
    freshness_envelope: FreshnessEnvelope,
    recommendation_block: RecommendationBlock,
) -> None:
    target = FollowUpTarget(
        target_kind=FollowUpTargetKind.ADVISORY_AGENT,
        target_name="market_structure",
        display_name="Market Structure",
    )
    package = TickerAnalysisPackage(
        analysis_id="analysis-42",
        ticker="AAPL",
        as_of_date=date(2026, 5, 25),
        generated_at=datetime(2026, 5, 25, 12, 5, tzinfo=timezone.utc),
        symbolic_verdict_ref="verdict-42",
        evidence_context=evidence_context,
        freshness=freshness_envelope,
        recommendation_blocks=[recommendation_block],
        target_context=target,
        primary_recommendation="constructive",
    )

    assert package.recommendation_blocks[0].entry_plan.entry_bias == EntryBias.LONG
    assert package.target_context.is_authoritative is False
    assert package.freshness.freshness_label == FreshnessLabel.SNAPSHOT


def test_recommendation_block_requires_a_plan_subobject(
    evidence_context: EvidenceContext,
    freshness_envelope: FreshnessEnvelope,
) -> None:
    with pytest.raises(ValueError, match="at least one plan sub-object"):
        RecommendationBlock(
            block_id="block-2",
            block_type=RecommendationBlockType.RISK,
            headline="Risk only",
            summary="Missing plan payloads should fail.",
            status=RecommendationStatus.CAUTIONARY,
            evidence_context=evidence_context,
            freshness=freshness_envelope,
        )


def test_ticker_analysis_package_requires_blocks(
    evidence_context: EvidenceContext,
    freshness_envelope: FreshnessEnvelope,
) -> None:
    with pytest.raises(ValueError, match="recommendation_blocks must be provided"):
        TickerAnalysisPackage(
            analysis_id="analysis-99",
            ticker="AAPL",
            as_of_date=date(2026, 5, 25),
            generated_at=datetime(2026, 5, 25, 12, 5, tzinfo=timezone.utc),
            symbolic_verdict_ref="verdict-99",
            evidence_context=evidence_context,
            freshness=freshness_envelope,
        )
