from __future__ import annotations

from typing import Sequence

from backend.schemas.decision_models import FollowUpAnswer, FollowUpQuestion
from backend.schemas.shared import FreshnessEnvelope, EvidenceContext

from .follow_up_producer import build_follow_up_bundle


def get_runtime_follow_ups(
    freshness: FreshnessEnvelope, evidence_context: EvidenceContext, now=None
) -> tuple[Sequence[FollowUpQuestion], Sequence[FollowUpAnswer]]:
    """Bridge the dashboard runtime to the follow-up producer."""
    return build_follow_up_bundle(freshness, evidence_context, produced_at=now)
