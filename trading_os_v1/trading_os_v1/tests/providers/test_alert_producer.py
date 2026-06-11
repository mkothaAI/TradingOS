from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.schemas.decision_models import AlertEvent
from backend.schemas.shared import EvidenceContext, FreshnessEnvelope, FreshnessLabel, SourceLink
from trading_os_v1.providers.adapters.alert_producer import build_alert_events


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


def test_alert_producer_emits_authoritative_models() -> None:
    freshness_envelope = _freshness_envelope()
    evidence_context = _evidence_context(freshness_envelope)

    alerts = build_alert_events(freshness_envelope, evidence_context)

    assert isinstance(alerts[0], AlertEvent)
    assert alerts[0].alert_id == "alert-runtime-1"
    assert alerts[0].routing_hint is not None
    assert alerts[0].routing_hint.audience == "analyst"


def test_alert_producer_returns_domain_only_payloads() -> None:
    freshness_envelope = _freshness_envelope()
    evidence_context = _evidence_context(freshness_envelope)

    alerts = build_alert_events(freshness_envelope, evidence_context)

    assert not hasattr(alerts[0], "diagnostics_drawer")
    assert not hasattr(alerts[0], "quote_watch_panel")
