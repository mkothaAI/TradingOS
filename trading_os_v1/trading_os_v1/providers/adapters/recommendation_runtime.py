from __future__ import annotations

from typing import Sequence

from backend.schemas.decision_models import RecommendationBlock
from backend.schemas.models_responses import DecisionResponse
from backend.schemas.shared import EvidenceContext, FreshnessEnvelope

from .recommendation_producer import (
    produce_recommendation_blocks,
    produce_recommendation_blocks_from_decision_response,
)


def get_runtime_recommendation_blocks(
    freshness: FreshnessEnvelope,
    evidence_context: EvidenceContext,
    now=None,
    decision_response: DecisionResponse | None = None,
) -> Sequence[RecommendationBlock]:
    """Bridge the dashboard runtime to the recommendation producer.

    Prefers a typed DecisionResponse when one is available, otherwise falls
    back to the sample-backed recommendation producer.
    """
    if decision_response is not None:
        return produce_recommendation_blocks_from_decision_response(
            decision_response,
            freshness,
            evidence_context,
            generated_at=now,
        )
    return produce_recommendation_blocks(freshness, evidence_context, generated_at=now)
