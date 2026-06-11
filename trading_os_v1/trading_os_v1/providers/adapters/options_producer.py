from __future__ import annotations

from datetime import datetime
from typing import Sequence

from backend.schemas.decision_models import OptionContractSnapshot, OptionContractType, OptionsProfile
from backend.schemas.shared import EvidenceContext, FreshnessEnvelope


def build_options_profiles(
    freshness: FreshnessEnvelope,
    evidence_context: EvidenceContext,
    *,
    produced_at: datetime | None = None,
) -> Sequence[OptionsProfile]:
    """Build the authoritative options domain bundle.

    This producer emits domain models only and avoids any dashboard/view shapes.
    It is intentionally small and serves as the upstream boundary for options-family
    objects until a real options engine is wired in.
    """
    produced_at = produced_at or freshness.received_at
    contract = OptionContractSnapshot(
        contract_id="contract-runtime-1",
        underlying_ticker=evidence_context.ticker,
        contract_type=OptionContractType.CALL,
        expiry=produced_at.date(),
        strike=210.0,
        freshness=freshness,
        evidence_context=evidence_context,
    )
    profile = OptionsProfile(
        profile_id="options-runtime-1",
        ticker=evidence_context.ticker,
        as_of_date=produced_at.date(),
        generated_at=produced_at,
        symbolic_verdict_ref=evidence_context.verdict_ref,
        evidence_context=evidence_context,
        freshness=freshness,
        contract_snapshots=[contract],
        contract_count=1,
        profile_summary="Domain-first options profile.",
        thesis_fit="advisory",
    )
    return (profile,)
