from __future__ import annotations

from datetime import datetime
from typing import Sequence, Tuple

from backend.schemas.decision_models import (
    FollowUpAnswer,
    FollowUpAnswerType,
    FollowUpQuestion,
    FollowUpTarget,
    FollowUpTargetKind,
)
from backend.schemas.shared import EvidenceContext, FreshnessEnvelope


def build_follow_up_bundle(
    freshness: FreshnessEnvelope,
    evidence_context: EvidenceContext,
    *,
    produced_at: datetime | None = None,
) -> Tuple[Sequence[FollowUpQuestion], Sequence[FollowUpAnswer]]:
    """Build the authoritative follow-up domain bundle.

    This producer emits domain models only and does not depend on dashboard
    shapes or transport concerns.
    """
    produced_at = produced_at or freshness.received_at
    target = FollowUpTarget(
        target_kind=FollowUpTargetKind.ADVISORY_AGENT,
        target_name="market_structure",
        display_name="Market Structure",
    )
    question = FollowUpQuestion(
        question_id="fuq-runtime-1",
        thread_id="thread-runtime-1",
        ticker=evidence_context.ticker,
        target=target,
        question_text="Is the setup still intact?",
        asked_at=produced_at,
        as_of_date=produced_at.date(),
        evidence_context=evidence_context,
        follow_up_mode="watch_and_wait",
    )
    answer = FollowUpAnswer(
        answer_id="fua-runtime-1",
        question_id=question.question_id,
        ticker=evidence_context.ticker,
        target=target,
        answer_text="The setup remains intact for now.",
        answer_type=FollowUpAnswerType.ADVISORY,
        generated_at=produced_at,
        as_of_date=produced_at.date(),
        evidence_context=evidence_context,
        freshness=freshness,
        supporting_rule_ids=["rule-runtime-1"],
    )
    return ( (question,), (answer,) )
