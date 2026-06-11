from __future__ import annotations

from datetime import datetime
from typing import Sequence

from backend.schemas.decision_models import (
    AlertEvent,
    AlertRoutingHint,
    AlertSeverity,
    AlertSeverityCode,
    AlertSourceKind,
    AlertTrigger,
    AlertTriggerType,
)
from backend.schemas.shared import EvidenceContext, FreshnessEnvelope


def build_alert_events(
    freshness: FreshnessEnvelope,
    evidence_context: EvidenceContext,
    *,
    produced_at: datetime | None = None,
) -> Sequence[AlertEvent]:
    """Build the authoritative alert domain bundle.

    This producer emits domain models only and avoids any dashboard/view shapes.
    It is the upstream boundary for alert-family objects until a real alert
    engine is wired in.
    """
    produced_at = produced_at or freshness.received_at
    alert = AlertEvent(
        alert_id="alert-runtime-1",
        ticker=evidence_context.ticker,
        symbolic_verdict_ref=evidence_context.verdict_ref,
        source_kind=AlertSourceKind.MONITORING_STATE,
        source_id="state-runtime-1",
        alert_type="watch_condition_triggered",
        severity=AlertSeverity(
            severity_code=AlertSeverityCode.HIGH,
            severity_label="high",
            severity_rank=3,
            escalation_needed=True,
            freshness=freshness,
        ),
        trigger=AlertTrigger(
            trigger_id="trigger-runtime-1",
            condition_id="cond-runtime-1",
            trigger_type=AlertTriggerType.THRESHOLD_BREACH,
            trigger_basis="daily close crossed below support threshold",
            evidence_context=evidence_context,
            freshness=freshness,
        ),
        routing_hint=AlertRoutingHint(
            hint_id="hint-runtime-1",
            priority=1,
            audience="analyst",
            urgency="immediate",
            freshness=freshness,
        ),
        summary="Support broke and review is needed.",
        observed_at=produced_at,
        evidence_context=evidence_context,
        freshness=freshness,
        requires_review=True,
    )
    return (alert,)
