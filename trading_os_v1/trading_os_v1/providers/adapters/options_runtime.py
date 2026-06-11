from __future__ import annotations

from typing import Sequence, Tuple

from backend.schemas.decision_models import OptionsProfile
from backend.schemas.shared import FreshnessEnvelope, EvidenceContext

from .options_producer import build_options_profiles


def get_runtime_options_profiles(
    freshness: FreshnessEnvelope, evidence_context: EvidenceContext, now=None
) -> Sequence[OptionsProfile]:
    """Bridge the dashboard runtime to the options producer."""
    return build_options_profiles(freshness, evidence_context, produced_at=now)
