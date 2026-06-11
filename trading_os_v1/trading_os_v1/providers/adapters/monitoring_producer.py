from __future__ import annotations

from datetime import datetime
from typing import Sequence

from backend.schemas.decision_models import (
    MonitoringCondition,
    MonitoringConditionType,
    MonitoringState,
    MonitoringStateStatus,
)
from backend.schemas.shared import EvidenceContext, FreshnessEnvelope


def build_monitoring_states(
    freshness: FreshnessEnvelope,
    evidence_context: EvidenceContext,
    *,
    produced_at: datetime | None = None,
) -> Sequence[MonitoringState]:
    """Build the authoritative monitoring domain bundle.

    This producer emits domain models only and avoids any dashboard/view shapes.
    It is the upstream boundary for monitoring-family objects until a real
    monitoring engine is wired in.
    """
    produced_at = produced_at or freshness.received_at
    condition = MonitoringCondition(
        condition_id="cond-runtime-1",
        condition_type=MonitoringConditionType.THESIS_BREAKAGE,
        condition_name="support break",
        condition_description="Price closes below support.",
        trigger_basis="daily close below support",
        freshness=freshness,
        evidence_context=evidence_context,
    )
    state = MonitoringState(
        state_id="state-runtime-1",
        context_id="ctx-runtime-1",
        ticker=evidence_context.ticker,
        symbolic_verdict_ref=evidence_context.verdict_ref,
        status=MonitoringStateStatus.WATCHING,
        last_checked_at=produced_at,
        active_condition_ids=[condition.condition_id],
        resolved_condition_ids=[],
        current_conditions=[condition],
        state_summary="watch list elevated",
        freshness=freshness,
        evidence_context=evidence_context,
    )
    return (state,)
