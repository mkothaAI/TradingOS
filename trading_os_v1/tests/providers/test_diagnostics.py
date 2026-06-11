from __future__ import annotations

from datetime import datetime

import pytest

from trading_os_v1.providers.composition import build_test_provider_diagnostic_bundle, build_test_provider_registry
from trading_os_v1.providers.diagnostics import build_provider_diagnostic_bundle
from trading_os_v1.providers.evidence_summaries import summarize_local_evidence
from trading_os_v1.providers.health_summaries import summarize_health
from trading_os_v1.providers.eligibility import summarize_provider_eligibility
from trading_os_v1.providers.local_evidence_store import LocalEvidenceStore
from trading_os_v1.providers.schemas import ProviderCapability, ProviderMeta


@pytest.mark.asyncio
async def test_diagnostic_bundle_reports_registry_health_evidence_and_correlation(tmp_path) -> None:
    store = LocalEvidenceStore(tmp_path)
    registry = build_test_provider_registry(evidence_store=store)

    market = registry.resolve(ProviderCapability.MARKET_DATA)
    news = registry.resolve(ProviderCapability.NEWS)

    await market.get_quote("AAPL")
    await news.fetch_news(["AAPL"], start=datetime(2024, 1, 15, 15, 30), end=datetime(2024, 1, 15, 15, 31))

    registry.set_health(
        registry._health.record_success(
            "fake_market_primary",
            ProviderCapability.MARKET_DATA,
            latency_ms=12.0,
            quota_remaining=88,
            now=datetime(2024, 1, 15, 15, 32),
        )
    )
    registry.set_health(
        registry._health.record_failure(
            "fake_news_primary",
            ProviderCapability.NEWS,
            error_code="RATE_LIMIT",
            error_message="quota",
            now=datetime(2024, 1, 15, 15, 33),
        )
    )

    bundle = build_provider_diagnostic_bundle(registry, registry._health, store, temp_dir=str(tmp_path))

    assert bundle["registry"][ProviderCapability.MARKET_DATA.value][0]["provider_name"] == "fake_market_primary"
    assert bundle["health_summary"][ProviderCapability.MARKET_DATA.value]["providers"]["fake_market_primary"]["status"] == "healthy"
    assert bundle["health_summary"][ProviderCapability.NEWS.value]["providers"]["fake_news_primary"]["status"] == "degraded"
    assert bundle["evidence_summary"]["fake_market_primary"][ProviderCapability.MARKET_DATA.value]["raw_count"] == 1
    assert bundle["evidence_summary"]["fake_news_primary"][ProviderCapability.NEWS.value]["raw_count"] == 1
    assert bundle["correlation"]["fake_news_primary"][ProviderCapability.NEWS.value]["health_status"] == "degraded"
    assert bundle["correlation"]["fake_news_primary"][ProviderCapability.NEWS.value]["degraded_or_down_evidence_count"] == 2
    assert bundle["eligibility"]["fake_market_primary"][ProviderCapability.MARKET_DATA.value].classification_code == "HEALTHY_ELIGIBLE"
    assert bundle["eligibility"]["fake_news_primary"][ProviderCapability.NEWS.value].classification_code == "DEGRADED_EVIDENCE_ELIGIBLE"


def test_diagnostic_bundle_from_composition_helper(tmp_path) -> None:
    store = LocalEvidenceStore(tmp_path)
    bundle = build_test_provider_diagnostic_bundle(evidence_store=store)

    assert bundle["registry"][ProviderCapability.MARKET_DATA.value][0]["provider_name"] == "fake_market_primary"
    assert bundle["health_summary"][ProviderCapability.REALTIME_STREAM.value]["capability"] == ProviderCapability.REALTIME_STREAM.value


@pytest.mark.asyncio
async def test_diagnostic_bundle_is_read_only_and_deterministic(tmp_path) -> None:
    store = LocalEvidenceStore(tmp_path)
    meta = ProviderMeta(provider_name="fake_market_primary", received_at=datetime(2024, 1, 15, 15, 30))

    raw_id_1 = await store.put_raw(
        capability=ProviderCapability.MARKET_DATA.value,
        provider_name="fake_market_primary",
        symbol="AAPL",
        fetched_at=datetime(2024, 1, 15, 15, 30),
        payload={"last": 100.0},
        meta=meta,
    )
    await store.put_normalized(
        capability=ProviderCapability.MARKET_DATA.value,
        provider_name="fake_market_primary",
        symbol="AAPL",
        fetched_at=datetime(2024, 1, 15, 15, 30),
        normalized_payload={"last": 100.0},
        raw_evidence_id=raw_id_1,
    )
    raw_id_2 = await store.put_raw(
        capability=ProviderCapability.MARKET_DATA.value,
        provider_name="fake_market_primary",
        symbol="AAPL",
        fetched_at=datetime(2024, 1, 15, 15, 31),
        payload={"last": 101.0},
        meta=meta,
    )

    registry = build_test_provider_registry(evidence_store=store)
    health_summary = summarize_health(registry)
    evidence_summary = summarize_local_evidence(store)
    eligibility = summarize_provider_eligibility(health_summary, evidence_summary)
    bundle = build_provider_diagnostic_bundle(registry, registry._health, store, temp_dir=str(tmp_path))

    assert evidence_summary["fake_market_primary"][ProviderCapability.MARKET_DATA.value]["raw_count"] == 2
    assert evidence_summary["fake_market_primary"][ProviderCapability.MARKET_DATA.value]["newest_fetched_at"] == "2024-01-15T15:31:00"
    assert bundle["correlation"]["fake_market_primary"][ProviderCapability.MARKET_DATA.value]["total_evidence_count"] == 3
    assert bundle["correlation"]["fake_market_primary"][ProviderCapability.MARKET_DATA.value]["health_status"] == health_summary[ProviderCapability.MARKET_DATA.value]["providers"]["fake_market_primary"]["status"]
    assert raw_id_2 in evidence_summary["fake_market_primary"][ProviderCapability.MARKET_DATA.value]["raw_evidence_ids"]
    assert bundle["eligibility"]["fake_market_primary"][ProviderCapability.MARKET_DATA.value].classification_code == eligibility["fake_market_primary"][ProviderCapability.MARKET_DATA.value].classification_code
