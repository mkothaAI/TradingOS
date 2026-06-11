from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.schemas.decision_models import DecisionItem, TickerAnalysisPackage
from backend.schemas.models_responses import DecisionResponse
from backend.schemas.shared import EvidenceContext, FreshnessEnvelope, FreshnessLabel, RequestMeta, SourceLink, SizeInfo
from trading_os_v1.providers.adapters.recommendation_producer import (
    build_recommendation_analysis_package,
    build_recommendation_analysis_package_from_decision_response,
    produce_recommendation_blocks,
    produce_recommendation_blocks_from_decision_response,
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


def test_recommendation_producer_emits_authoritative_package() -> None:
    freshness_envelope = _freshness_envelope()
    evidence_context = _evidence_context(freshness_envelope)

    package = build_recommendation_analysis_package(freshness_envelope, evidence_context)

    assert isinstance(package, TickerAnalysisPackage)
    assert package.analysis_id == "analysis-transport-1"
    assert package.recommendation_blocks[0].block_id == "block-runtime-1"
    assert package.primary_recommendation == "constructive"


def test_recommendation_producer_bridges_blocks_without_dashboard_shapes() -> None:
    freshness_envelope = _freshness_envelope()
    evidence_context = _evidence_context(freshness_envelope)

    blocks = produce_recommendation_blocks(freshness_envelope, evidence_context)

    assert blocks[0].headline == "Entry setup"
    assert not hasattr(blocks[0], "row_severity")


def test_recommendation_bridge_consumes_decision_response_cleanly() -> None:
    freshness_envelope = _freshness_envelope()
    evidence_context = _evidence_context(freshness_envelope)
    decision_response = DecisionResponse(
        meta=RequestMeta(request_id="req-1", as_of_date=datetime(2026, 5, 25, tzinfo=timezone.utc).date()),
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

    package = build_recommendation_analysis_package_from_decision_response(
        decision_response,
        freshness_envelope,
        evidence_context,
    )
    blocks = produce_recommendation_blocks_from_decision_response(
        decision_response,
        freshness_envelope,
        evidence_context,
    )

    assert isinstance(package, TickerAnalysisPackage)
    assert package.primary_recommendation == "constructive"
    assert blocks[0].block_id == "rec-aapl-entry"
