from __future__ import annotations

from datetime import datetime
from typing import Sequence

from backend.schemas.decision_models import (
    EntryBias,
    EntryPlan,
    InvalidationPlan,
    MonitoringPlan,
    RecommendationBlock,
    RecommendationBlockType,
    RecommendationStatus,
    RiskPlan,
    TickerAnalysisPackage,
)
from backend.schemas.models_responses import DecisionResponse
from backend.schemas.shared import EvidenceContext, FreshnessEnvelope, SizeInfo


def _select_decision_item(decision_response: DecisionResponse, ticker: str):
    decision_item = (decision_response.decisions or {}).get(ticker)
    if decision_item is None:
        raise ValueError(f"No decision item found for ticker: {ticker}")
    return decision_item


def _entry_block(
    decision_item,
    freshness: FreshnessEnvelope,
    evidence_context: EvidenceContext,
) -> RecommendationBlock:
    size_info = decision_item.size_info
    entry_plan = EntryPlan(
        entry_bias=EntryBias.LONG,
        timing_window="next_session",
        capital_allocation=10.0,
        size_plan=size_info if isinstance(size_info, SizeInfo) else None,
        entry_conditions=["decision engine approved entry"],
        entry_triggers=list(decision_item.applied_rules or []) or ["decision_entry"],
        entry_rationale="Decision engine signaled a buy candidate.",
        freshness=freshness,
        evidence_context=evidence_context,
    )
    return RecommendationBlock(
        block_id=f"rec-{decision_item.ticker.lower()}-entry",
        block_type=RecommendationBlockType.ENTRY,
        headline="Entry setup",
        summary=f"Decision engine emitted {decision_item.decision}.",
        status=RecommendationStatus.SUPPORTIVE,
        evidence_context=evidence_context,
        freshness=freshness,
        entry_plan=entry_plan,
        supporting_rule_ids=list(decision_item.applied_rules or []),
    )


def _invalidation_block(
    decision_item,
    freshness: FreshnessEnvelope,
    evidence_context: EvidenceContext,
) -> RecommendationBlock:
    invalidation_plan = InvalidationPlan(
        invalidation_level="high",
        invalidation_conditions=["decision engine recommends exit"],
        invalidation_triggers=list(decision_item.reason_codes or []) or ["decision_exit"],
        invalidation_message="Decision engine flagged the position for exit or de-risking.",
        reassessment_needed=True,
        freshness=freshness,
        evidence_context=evidence_context,
    )
    return RecommendationBlock(
        block_id=f"rec-{decision_item.ticker.lower()}-exit",
        block_type=RecommendationBlockType.INVALIDATION,
        headline="Exit setup",
        summary=f"Decision engine emitted {decision_item.decision}.",
        status=RecommendationStatus.BLOCKING,
        evidence_context=evidence_context,
        freshness=freshness,
        invalidation_plan=invalidation_plan,
        supporting_rule_ids=list(decision_item.applied_rules or []),
    )


def _monitoring_block(
    decision_item,
    freshness: FreshnessEnvelope,
    evidence_context: EvidenceContext,
) -> RecommendationBlock:
    monitoring_plan = MonitoringPlan(
        monitoring_level="watch",
        monitoring_conditions=["decision engine indicates hold or no trade"],
        review_frequency="next session",
        alert_thresholds=list(decision_item.reason_codes or []),
        watch_notes="Continue monitoring until a stronger decision signal appears.",
        freshness=freshness,
        evidence_context=evidence_context,
    )
    status = RecommendationStatus.WATCHING if decision_item.decision == "HOLD" else RecommendationStatus.CAUTIONARY
    return RecommendationBlock(
        block_id=f"rec-{decision_item.ticker.lower()}-monitor",
        block_type=RecommendationBlockType.MONITORING,
        headline="Monitoring setup",
        summary=f"Decision engine emitted {decision_item.decision}.",
        status=status,
        evidence_context=evidence_context,
        freshness=freshness,
        monitoring_plan=monitoring_plan,
        supporting_rule_ids=list(decision_item.applied_rules or []),
    )


def build_recommendation_analysis_package(
    decision_response: DecisionResponse,
    freshness: FreshnessEnvelope,
    evidence_context: EvidenceContext,
    *,
    produced_at: datetime | None = None,
) -> TickerAnalysisPackage:
    """Build the authoritative recommendation analysis package from decision output.

    This is the upstream business-logic producer for recommendation-family objects.
    It consumes typed decision-engine output and emits domain models only.
    """
    produced_at = produced_at or freshness.received_at
    decision_item = _select_decision_item(decision_response, evidence_context.ticker)
    decision_token = str(decision_item.decision)

    if decision_token == "BUY_CANDIDATE":
        block = _entry_block(decision_item, freshness, evidence_context)
        primary_recommendation = "constructive"
        analysis_summary = "Decision engine confirmed an entry candidate."
        confidence_label = "moderate"
    elif decision_token in ("SELL_EXIT_CANDIDATE", "SELL_CANDIDATE"):
        block = _invalidation_block(decision_item, freshness, evidence_context)
        primary_recommendation = "de-risk"
        analysis_summary = "Decision engine recommended exit or invalidation review."
        confidence_label = "moderate"
    else:
        block = _monitoring_block(decision_item, freshness, evidence_context)
        primary_recommendation = "watch"
        analysis_summary = "Decision engine recommended monitoring rather than action."
        confidence_label = "low"

    return TickerAnalysisPackage(
        analysis_id=evidence_context.analysis_id,
        ticker=evidence_context.ticker,
        as_of_date=produced_at.date(),
        generated_at=produced_at,
        symbolic_verdict_ref=evidence_context.verdict_ref,
        evidence_context=evidence_context,
        freshness=freshness,
        recommendation_blocks=[block],
        primary_recommendation=primary_recommendation,
        analysis_summary=analysis_summary,
        confidence_label=confidence_label,
    )


def produce_recommendation_blocks(
    decision_response: DecisionResponse,
    freshness: FreshnessEnvelope,
    evidence_context: EvidenceContext,
    *,
    produced_at: datetime | None = None,
) -> Sequence[RecommendationBlock]:
    """Emit recommendation blocks from the authoritative recommendation package."""
    package = build_recommendation_analysis_package(
        decision_response,
        freshness,
        evidence_context,
        produced_at=produced_at,
    )
    return tuple(package.recommendation_blocks)
