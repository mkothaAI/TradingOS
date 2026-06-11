from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.schemas.decision_models import OptionsProfile
from backend.schemas.shared import EvidenceContext, FreshnessEnvelope, FreshnessLabel, SourceLink
from trading_os_v1.providers.adapters.options_producer import build_options_profiles


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


def test_options_producer_emits_authoritative_models() -> None:
    freshness_envelope = _freshness_envelope()
    evidence_context = _evidence_context(freshness_envelope)

    profiles = build_options_profiles(freshness_envelope, evidence_context)

    assert isinstance(profiles[0], OptionsProfile)
    assert profiles[0].profile_id == "options-runtime-1"
    assert profiles[0].contract_snapshots[0].contract_id == "contract-runtime-1"


def test_options_producer_returns_domain_only_payloads() -> None:
    freshness_envelope = _freshness_envelope()
    evidence_context = _evidence_context(freshness_envelope)

    profiles = build_options_profiles(freshness_envelope, evidence_context)

    assert not hasattr(profiles[0], "quote_watch_panel")
    assert not hasattr(profiles[0], "row_severity")
