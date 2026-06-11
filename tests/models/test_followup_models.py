from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

from backend.schemas import (
    EvidenceContext,
    FreshnessEnvelope,
    FreshnessLabel,
    FollowUpAnswer,
    FollowUpAnswerType,
    FollowUpQuestion,
    FollowUpTarget,
    FollowUpTargetKind,
)
from backend.schemas.shared import SourceLink


@pytest.fixture
def freshness_envelope() -> FreshnessEnvelope:
    return FreshnessEnvelope(
        freshness_label=FreshnessLabel.REAL_TIME,
        evidence_timestamp=datetime(2026, 5, 25, 12, 0, tzinfo=timezone.utc),
        received_at=datetime(2026, 5, 25, 12, 0, 30, tzinfo=timezone.utc),
        last_updated_at=datetime(2026, 5, 25, 12, 1, tzinfo=timezone.utc),
        delay_seconds=30,
        staleness_seconds=0,
        delay_reason=None,
    )


@pytest.fixture
def evidence_context(freshness_envelope: FreshnessEnvelope) -> EvidenceContext:
    return EvidenceContext(
        ticker="AAPL",
        analysis_id="analysis-1",
        verdict_ref="verdict-1",
        evidence_ids=["ev-1"],
        source_links=[SourceLink(rule_id="rule-1", file="file.py", line_range="1-10")],
        primary_topics=["monitoring"],
        freshness=freshness_envelope,
        evidence_window_start=datetime(2026, 5, 25, 11, 0, tzinfo=timezone.utc),
        evidence_window_end=datetime(2026, 5, 25, 12, 0, tzinfo=timezone.utc),
        provenance_summary="normalized from provider evidence",
    )


def test_freshness_envelope_requires_utc_datetimes(freshness_envelope: FreshnessEnvelope) -> None:
    assert freshness_envelope.freshness_label == FreshnessLabel.REAL_TIME
    assert freshness_envelope.received_at.tzinfo == timezone.utc


def test_evidence_context_requires_evidence_sources(evidence_context: EvidenceContext) -> None:
    assert evidence_context.source_links[0].rule_id == "rule-1"


def test_follow_up_models_preserve_advisory_boundary(evidence_context: EvidenceContext, freshness_envelope: FreshnessEnvelope) -> None:
    target = FollowUpTarget(
        target_kind=FollowUpTargetKind.ADVISORY_AGENT,
        target_name="monitoring_watchtower",
        display_name="Monitoring Watchtower",
        topic_tags=["monitoring"],
    )
    question = FollowUpQuestion(
        question_id="q-1",
        ticker="AAPL",
        target=target,
        question_text="What changed in the monitoring case?",
        asked_at=datetime(2026, 5, 25, 12, 2, tzinfo=timezone.utc),
        as_of_date=date(2026, 5, 25),
        evidence_context=evidence_context,
    )
    answer = FollowUpAnswer(
        answer_id="a-1",
        question_id=question.question_id,
        ticker="AAPL",
        target=target,
        answer_text="The alert remains advisory and grounded in the current evidence.",
        answer_type=FollowUpAnswerType.ADVISORY,
        generated_at=datetime(2026, 5, 25, 12, 3, tzinfo=timezone.utc),
        as_of_date=date(2026, 5, 25),
        evidence_context=evidence_context,
        freshness=freshness_envelope,
        supporting_rule_ids=["rule-1"],
    )

    assert question.target.is_authoritative is False
    assert answer.answer_type == FollowUpAnswerType.ADVISORY
    assert answer.target.target_kind == FollowUpTargetKind.ADVISORY_AGENT


def test_follow_up_target_rejects_authority_override() -> None:
    with pytest.raises(ValueError, match="advisory-only"):
        FollowUpTarget(
            target_kind=FollowUpTargetKind.SYNTHESIZED_VERDICT,
            target_name="verdict_synthesis",
            is_authoritative=True,
        )
