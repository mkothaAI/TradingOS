from __future__ import annotations

from typing import Sequence

from backend.schemas.decision_models import AlertEvent
from backend.schemas.shared import EvidenceContext, FreshnessEnvelope

from .alert_producer import build_alert_events


def get_runtime_alert_events(
    freshness: FreshnessEnvelope, evidence_context: EvidenceContext, now=None
) -> Sequence[AlertEvent]:
    """Bridge the dashboard runtime to the alert producer."""
    return build_alert_events(freshness, evidence_context, produced_at=now)
