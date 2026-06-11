from __future__ import annotations

import sys
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.engines.recommendation.producer import build_recommendation_analysis_package
from backend.schemas.decision_models import DecisionItem, EntryBias, SizeInfo
from backend.schemas.models_responses import DecisionResponse
from backend.schemas.shared import EvidenceContext, FreshnessEnvelope, FreshnessLabel, RequestMeta, SourceLink


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
        analysis_id="analysis-1",
        verdict_ref="verdict-1",
        evidence_ids=["ev-1"],
        source_links=[SourceLink(rule_id="rule-1", file="decision.py")],
        primary_topics=["recommendation"],
        freshness=freshness_envelope,
        provenance_summary="decision-engine output",
    )


def test_recommendation_engine_emits_authoritative_package() -> None:
    freshness_envelope = _freshness_envelope()
    evidence_context = _evidence_context(freshness_envelope)
    decision_response = DecisionResponse(
        meta=RequestMeta(request_id="req-1", as_of_date=date(2026, 5, 25)),
        status="OK",
        decisions={
            "AAPL": DecisionItem(
                ticker="AAPL",
                decision="BUY_CANDIDATE",
                size_info=SizeInfo(allowed_qty=10),
                reason_codes=["TECH_ENTRY"],
                applied_rules=["R1"],
            )
        },
        errors=[],
    )

    package = build_recommendation_analysis_package(decision_response, freshness_envelope, evidence_context)

    assert package.analysis_id == "analysis-1"
    assert package.primary_recommendation == "constructive"
    assert package.recommendation_blocks[0].block_type.value == "entry"
    assert package.recommendation_blocks[0].entry_plan.entry_bias == EntryBias.LONG


def test_recommendation_engine_maps_hold_to_monitoring() -> None:
    freshness_envelope = _freshness_envelope()
    evidence_context = _evidence_context(freshness_envelope)
    decision_response = DecisionResponse(
        meta=RequestMeta(request_id="req-2", as_of_date=date(2026, 5, 25)),
        status="OK",
        decisions={
            "AAPL": DecisionItem(
                ticker="AAPL",
                decision="HOLD",
                size_info=None,
                reason_codes=["NO_SIGNAL"],
                applied_rules=[],
            )
        },
        errors=[],
    )

    package = build_recommendation_analysis_package(decision_response, freshness_envelope, evidence_context)

    assert package.primary_recommendation == "watch"
    assert package.recommendation_blocks[0].block_type.value == "monitoring"
