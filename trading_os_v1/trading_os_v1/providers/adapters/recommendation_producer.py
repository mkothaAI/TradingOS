from __future__ import annotations

from datetime import datetime
from typing import Sequence

from backend.schemas.decision_models import (
    EntryBias,
    EntryPlan,
    RecommendationBlock,
    RecommendationBlockType,
    RecommendationStatus,
    TickerAnalysisPackage,
)
from backend.schemas.models_responses import DecisionResponse
from backend.schemas.shared import EvidenceContext, FreshnessEnvelope

from backend.engines.recommendation.producer import (
    build_recommendation_analysis_package as build_upstream_recommendation_analysis_package,
    produce_recommendation_blocks as produce_upstream_recommendation_blocks,
)


def build_recommendation_analysis_package(
    freshness: FreshnessEnvelope,
    evidence_context: EvidenceContext,
    *,
    generated_at: datetime | None = None,
) -> TickerAnalysisPackage:
    """Build a domain-first recommendation analysis package.

    This is the upstream producer boundary for recommendation-family domain objects.
    It returns authoritative schema models and avoids any dashboard-specific shapes.
    """
    generated_at = generated_at or freshness.received_at
    entry_plan = EntryPlan(
        entry_bias=EntryBias.LONG,
        timing_window="next_session",
        capital_allocation=5.0,
        entry_conditions=["price above MA"],
        entry_triggers=["ma_cross"],
        entry_rationale="Momentum looks favorable.",
        freshness=freshness,
        evidence_context=evidence_context,
    )
    block = RecommendationBlock(
        block_id="block-runtime-1",
        block_type=RecommendationBlockType.ENTRY,
        headline="Entry setup",
        summary="Runtime recommendation block from producer",
        status=RecommendationStatus.SUPPORTIVE,
        evidence_context=evidence_context,
        freshness=freshness,
        entry_plan=entry_plan,
    )
    return TickerAnalysisPackage(
        analysis_id=evidence_context.analysis_id,
        ticker=evidence_context.ticker,
        as_of_date=generated_at.date(),
        generated_at=generated_at,
        symbolic_verdict_ref=evidence_context.verdict_ref,
        evidence_context=evidence_context,
        freshness=freshness,
        recommendation_blocks=[block],
        primary_recommendation="constructive",
        analysis_summary="Domain-first recommendation package.",
        confidence_label="moderate",
    )


def build_recommendation_analysis_package_from_decision_response(
    decision_response: DecisionResponse,
    freshness: FreshnessEnvelope,
    evidence_context: EvidenceContext,
    *,
    generated_at: datetime | None = None,
) -> TickerAnalysisPackage:
    """Bridge a typed decision response into the upstream recommendation producer."""
    return build_upstream_recommendation_analysis_package(
        decision_response,
        freshness,
        evidence_context,
        produced_at=generated_at,
    )


def produce_recommendation_blocks(
    freshness: FreshnessEnvelope,
    evidence_context: EvidenceContext,
    *,
    generated_at: datetime | None = None,
) -> Sequence[RecommendationBlock]:
    """Emit recommendation blocks from the domain-first analysis package."""
    package = build_recommendation_analysis_package(
        freshness,
        evidence_context,
        generated_at=generated_at,
    )
    return tuple(package.recommendation_blocks)


def produce_recommendation_blocks_from_decision_response(
    decision_response: DecisionResponse,
    freshness: FreshnessEnvelope,
    evidence_context: EvidenceContext,
    *,
    generated_at: datetime | None = None,
) -> Sequence[RecommendationBlock]:
    """Bridge typed decision output into recommendation blocks via the upstream producer."""
    return produce_upstream_recommendation_blocks(
        decision_response,
        freshness,
        evidence_context,
        produced_at=generated_at,
    )
