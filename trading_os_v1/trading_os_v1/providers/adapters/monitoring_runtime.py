from __future__ import annotations

from typing import Sequence, Tuple

from backend.schemas.decision_models import MonitoringState
from backend.schemas.shared import FreshnessEnvelope, EvidenceContext

from .monitoring_producer import build_monitoring_states


def get_runtime_monitoring_states(
    freshness: FreshnessEnvelope, evidence_context: EvidenceContext, now=None
) -> Sequence[MonitoringState]:
    """Bridge the dashboard runtime to the monitoring producer."""
    return build_monitoring_states(freshness, evidence_context, produced_at=now)
