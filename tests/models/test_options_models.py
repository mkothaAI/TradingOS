from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

from backend.schemas import (
    EvidenceContext,
    FreshnessEnvelope,
    FreshnessLabel,
    GreeksSnapshot,
    LiquidityLabel,
    LiquiditySnapshot,
    OptionContractSnapshot,
    OptionContractType,
    OptionsProfile,
    SpreadQualityLabel,
    SpreadQualitySnapshot,
)
from backend.schemas.shared import SourceLink


@pytest.fixture
def freshness_envelope() -> FreshnessEnvelope:
    return FreshnessEnvelope(
        freshness_label=FreshnessLabel.DELAYED,
        evidence_timestamp=datetime(2026, 5, 25, 12, 0, tzinfo=timezone.utc),
        received_at=datetime(2026, 5, 25, 12, 4, tzinfo=timezone.utc),
        delay_seconds=240,
        staleness_seconds=240,
        delay_reason="provider lag",
    )


@pytest.fixture
def evidence_context(freshness_envelope: FreshnessEnvelope) -> EvidenceContext:
    return EvidenceContext(
        ticker="AAPL",
        analysis_id="options-analysis-1",
        verdict_ref="verdict-1",
        evidence_ids=["ev-options-1"],
        source_links=[SourceLink(rule_id="rule-options-1", file="options.py")],
        primary_topics=["options", "liquidity"],
        freshness=freshness_envelope,
        provenance_summary="normalized options snapshot",
    )


@pytest.fixture
def contract_snapshot(freshness_envelope: FreshnessEnvelope, evidence_context: EvidenceContext) -> OptionContractSnapshot:
    return OptionContractSnapshot(
        contract_id="AAPL-20260619-200C",
        underlying_ticker="AAPL",
        contract_type=OptionContractType.CALL,
        expiry=date(2026, 6, 19),
        strike=200.0,
        exchange="OPRA",
        currency="USD",
        bid=4.9,
        ask=5.1,
        mid_price=5.0,
        open_interest=1200,
        volume=340,
        contract_size=100,
        freshness=freshness_envelope,
        evidence_context=evidence_context,
    )


@pytest.fixture
def options_profile(
    freshness_envelope: FreshnessEnvelope,
    evidence_context: EvidenceContext,
    contract_snapshot: OptionContractSnapshot,
) -> OptionsProfile:
    greeks_snapshot = GreeksSnapshot(
        snapshot_id="greeks-1",
        contract_id=contract_snapshot.contract_id,
        underlying_ticker="AAPL",
        implied_volatility=0.42,
        delta=0.58,
        gamma=0.03,
        vega=0.11,
        iv_rank=54.0,
        freshness=freshness_envelope,
        evidence_context=evidence_context,
    )
    liquidity_snapshot = LiquiditySnapshot(
        snapshot_id="liq-1",
        contract_id=contract_snapshot.contract_id,
        underlying_ticker="AAPL",
        bid_size=15,
        ask_size=18,
        spread=0.2,
        spread_pct=0.04,
        open_interest=1200,
        volume=340,
        average_daily_volume=500.0,
        liquidity_label=LiquidityLabel.ADEQUATE,
        freshness=freshness_envelope,
        evidence_context=evidence_context,
    )
    spread_quality_snapshot = SpreadQualitySnapshot(
        snapshot_id="spread-1",
        contract_id=contract_snapshot.contract_id,
        underlying_ticker="AAPL",
        bid=4.9,
        ask=5.1,
        mid_price=5.0,
        spread=0.2,
        spread_pct=0.04,
        quality_label=SpreadQualityLabel.ACCEPTABLE,
        quality_notes="tight enough for analysis",
        freshness=freshness_envelope,
        evidence_context=evidence_context,
    )
    return OptionsProfile(
        profile_id="profile-1",
        ticker="AAPL",
        as_of_date=date(2026, 5, 25),
        generated_at=datetime(2026, 5, 25, 12, 6, tzinfo=timezone.utc),
        symbolic_verdict_ref="verdict-1",
        evidence_context=evidence_context,
        freshness=freshness_envelope,
        contract_snapshots=[contract_snapshot],
        greeks_snapshots=[greeks_snapshot],
        liquidity_snapshots=[liquidity_snapshot],
        spread_quality_snapshots=[spread_quality_snapshot],
        profile_summary="Directional call structure remains under review.",
        thesis_fit="advisory",
        contract_count=1,
    )


def test_options_profile_uses_shared_freshness_and_evidence(options_profile: OptionsProfile) -> None:
    assert options_profile.freshness.freshness_label == FreshnessLabel.DELAYED
    assert options_profile.evidence_context.source_links[0].rule_id == "rule-options-1"
    assert options_profile.contract_snapshots[0].contract_type == OptionContractType.CALL


def test_options_snapshots_remain_separate_and_cross_referenced(options_profile: OptionsProfile) -> None:
    contract_id = options_profile.contract_snapshots[0].contract_id
    assert options_profile.greeks_snapshots[0].contract_id == contract_id
    assert options_profile.liquidity_snapshots[0].contract_id == contract_id
    assert options_profile.spread_quality_snapshots[0].contract_id == contract_id
    assert options_profile.contract_count == 1


def test_options_profile_rejects_unknown_snapshot_reference(
    freshness_envelope: FreshnessEnvelope,
    evidence_context: EvidenceContext,
    contract_snapshot: OptionContractSnapshot,
) -> None:
    bad_greeks = GreeksSnapshot(
        snapshot_id="greeks-bad",
        contract_id="OTHER-CONTRACT",
        underlying_ticker="AAPL",
        delta=0.5,
        freshness=freshness_envelope,
        evidence_context=evidence_context,
    )

    with pytest.raises(ValueError, match="greeks_snapshots must reference a contract snapshot"):
        OptionsProfile(
            profile_id="profile-bad",
            ticker="AAPL",
            as_of_date=date(2026, 5, 25),
            generated_at=datetime(2026, 5, 25, 12, 6, tzinfo=timezone.utc),
            symbolic_verdict_ref="verdict-1",
            evidence_context=evidence_context,
            freshness=freshness_envelope,
            contract_snapshots=[contract_snapshot],
            greeks_snapshots=[bad_greeks],
        )


def test_option_contract_snapshot_rejects_invalid_price_bounds(
    freshness_envelope: FreshnessEnvelope,
    evidence_context: EvidenceContext,
) -> None:
    with pytest.raises(ValueError, match="bid must not exceed ask"):
        OptionContractSnapshot(
            contract_id="AAPL-20260619-200C",
            underlying_ticker="AAPL",
            contract_type=OptionContractType.CALL,
            expiry=date(2026, 6, 19),
            strike=200.0,
            bid=5.2,
            ask=5.1,
            freshness=freshness_envelope,
            evidence_context=evidence_context,
        )
