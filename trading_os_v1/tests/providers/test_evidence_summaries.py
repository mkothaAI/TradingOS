from __future__ import annotations

from datetime import datetime

import pytest

from trading_os_v1.providers.composition import build_test_provider_registry_with_diagnostics
from trading_os_v1.providers.diagnostics import build_provider_diagnostic_bundle
from trading_os_v1.providers.evidence_summaries import (
    correlate_health_and_evidence,
    summarize_evidence_eligibility_view,
    summarize_local_evidence,
)
from trading_os_v1.providers.health import ProviderHealthManager
from trading_os_v1.providers.health_summaries import summarize_health
from trading_os_v1.providers.local_evidence_store import LocalEvidenceStore
from trading_os_v1.providers.registry import ProviderBinding, ProviderRegistry
from trading_os_v1.providers.schemas import ProviderCapability, ProviderMeta


def test_summarize_local_evidence_counts_ranges_and_linkage(tmp_path) -> None:
    store = LocalEvidenceStore(tmp_path)
    meta = ProviderMeta(provider_name="fake_news_primary", received_at=datetime(2024, 1, 15, 15, 30))

    raw_id_1 = __import__("asyncio").run(
        store.put_raw(
            capability=ProviderCapability.NEWS.value,
            provider_name="fake_news_primary",
            symbol="AAPL",
            fetched_at=datetime(2024, 1, 15, 15, 30),
            payload={"headline": "One"},
            meta=meta,
        )
    )
    __import__("asyncio").run(
        store.put_normalized(
            capability=ProviderCapability.NEWS.value,
            provider_name="fake_news_primary",
            symbol="AAPL",
            fetched_at=datetime(2024, 1, 15, 15, 30),
            normalized_payload={"headline": "One"},
            raw_evidence_id=raw_id_1,
        )
    )
    raw_id_2 = __import__("asyncio").run(
        store.put_raw(
            capability=ProviderCapability.NEWS.value,
            provider_name="fake_news_primary",
            symbol="AAPL",
            fetched_at=datetime(2024, 1, 15, 15, 31),
            payload={"headline": "Two"},
            meta=meta,
        )
    )

    summary = summarize_local_evidence(tmp_path)
    bucket = summary["fake_news_primary"][ProviderCapability.NEWS.value]

    assert bucket["raw_count"] == 2
    assert bucket["normalized_count"] == 1
    assert bucket["total_count"] == 3
    assert bucket["oldest_fetched_at"] == "2024-01-15T15:30:00"
    assert bucket["newest_fetched_at"] == "2024-01-15T15:31:00"
    assert raw_id_1 in bucket["raw_evidence_ids"]
    assert raw_id_2 in bucket["raw_evidence_ids"]


def test_correlate_health_with_evidence_rolls_up_counts(tmp_path) -> None:
    store = LocalEvidenceStore(tmp_path)
    registry = ProviderRegistry(ProviderHealthManager())

    registry.register(
        ProviderBinding(
            capability=ProviderCapability.NEWS,
            provider_name="fake_news_primary",
            factory=lambda: object(),
            priority=0,
        )
    )

    __import__("asyncio").run(
        store.put_raw(
            capability=ProviderCapability.NEWS.value,
            provider_name="fake_news_primary",
            symbol="AAPL",
            fetched_at=datetime(2024, 1, 15, 15, 30),
            payload={"headline": "One"},
            meta=ProviderMeta(provider_name="fake_news_primary", received_at=datetime(2024, 1, 15, 15, 30)),
        )
    )

    registry.set_health(
        registry._health.record_failure(
            "fake_news_primary",
            ProviderCapability.NEWS,
            error_code="TIMEOUT",
            error_message="slow",
            now=datetime(2024, 1, 15, 15, 31),
        )
    )

    health_summary = summarize_health(registry)
    evidence_summary = summarize_local_evidence(tmp_path)
    correlated = correlate_health_and_evidence(health_summary, evidence_summary)

    bucket = correlated["fake_news_primary"][ProviderCapability.NEWS.value]
    assert bucket["total_evidence_count"] == 1
    assert bucket["health_status"] == "degraded"
    assert bucket["degraded_or_down_evidence_count"] == 1


def test_health_and_evidence_summary_from_composed_setup(tmp_path) -> None:
    store = LocalEvidenceStore(tmp_path)
    registry, health_summary, evidence_summary, correlated = build_test_provider_registry_with_diagnostics(evidence_store=store)

    __import__("asyncio").run(registry.resolve(ProviderCapability.MARKET_DATA).get_quote("AAPL"))

    evidence_summary = summarize_local_evidence(store)
    correlated = correlate_health_and_evidence(health_summary, evidence_summary)

    assert registry.resolve(ProviderCapability.MARKET_DATA).provider_name == "fake_market_primary"
    assert evidence_summary["fake_market_primary"][ProviderCapability.MARKET_DATA.value]["raw_count"] == 1
    assert correlated["fake_market_primary"][ProviderCapability.MARKET_DATA.value]["total_evidence_count"] == 2


def test_correlate_health_with_evidence_accepts_disabled_health(tmp_path) -> None:
    store = LocalEvidenceStore(tmp_path)
    registry = ProviderRegistry(ProviderHealthManager())
    registry.register(
        ProviderBinding(
            capability=ProviderCapability.EVENT,
            provider_name="event_primary",
            factory=lambda: object(),
            priority=0,
        )
    )
    registry.set_health(
        registry._health.record_failure(
            "event_primary",
            ProviderCapability.EVENT,
            error_code="AUTH",
            error_message="down",
            now=datetime(2024, 1, 15, 15, 32),
        )
    )
    __import__("asyncio").run(
        store.put_raw(
            capability=ProviderCapability.EVENT.value,
            provider_name="event_primary",
            symbol="AAPL",
            fetched_at=datetime(2024, 1, 15, 15, 32),
            payload={"event": "earnings"},
            meta=ProviderMeta(provider_name="event_primary", received_at=datetime(2024, 1, 15, 15, 32)),
        )
    )

    health_summary = summarize_health(registry)
    evidence_summary = summarize_local_evidence(tmp_path)
    correlated = correlate_health_and_evidence(health_summary, evidence_summary)

    bucket = correlated["event_primary"][ProviderCapability.EVENT.value]
    assert bucket["health_status"] == "down"
    assert bucket["degraded_or_down_evidence_count"] == 1


def test_evidence_helper_round_trip_known_provider_state(tmp_path) -> None:
    store = LocalEvidenceStore(tmp_path)
    registry = ProviderRegistry(ProviderHealthManager())

    registry.register(
        ProviderBinding(
            capability=ProviderCapability.MARKET_DATA,
            provider_name="primary_market",
            factory=lambda: object(),
            priority=0,
        )
    )

    registry.set_health(
        registry._health.record_success(
            "primary_market",
            ProviderCapability.MARKET_DATA,
            latency_ms=9.0,
            now=datetime(2024, 1, 15, 15, 30),
        )
    )

    raw_id = __import__("asyncio").run(
        store.put_raw(
            capability=ProviderCapability.MARKET_DATA.value,
            provider_name="primary_market",
            symbol="AAPL",
            fetched_at=datetime(2024, 1, 15, 15, 30),
            payload={"last": 100.0},
            meta=ProviderMeta(provider_name="primary_market", received_at=datetime(2024, 1, 15, 15, 30)),
        )
    )
    __import__("asyncio").run(
        store.put_normalized(
            capability=ProviderCapability.MARKET_DATA.value,
            provider_name="primary_market",
            symbol="AAPL",
            fetched_at=datetime(2024, 1, 15, 15, 30),
            normalized_payload={"last": 100.0},
            raw_evidence_id=raw_id,
        )
    )

    health_summary = summarize_health(registry)
    verdicts = summarize_evidence_eligibility_view(health_summary, evidence_source=store)

    assert verdicts["primary_market"][ProviderCapability.MARKET_DATA.value].classification_code == "HEALTHY_ELIGIBLE"


def test_evidence_helper_matches_registry_and_diagnostics_views(tmp_path) -> None:
    store = LocalEvidenceStore(tmp_path)
    registry = ProviderRegistry(ProviderHealthManager())

    registry.register(
        ProviderBinding(
            capability=ProviderCapability.NEWS,
            provider_name="primary_news",
            factory=lambda: object(),
            priority=0,
        )
    )
    registry.set_health(
        registry._health.record_failure(
            "primary_news",
            ProviderCapability.NEWS,
            error_code="RATE_LIMIT",
            error_message="slow",
            now=datetime(2024, 1, 15, 15, 31),
        )
    )
    raw_id = __import__("asyncio").run(
        store.put_raw(
            capability=ProviderCapability.NEWS.value,
            provider_name="primary_news",
            symbol="AAPL",
            fetched_at=datetime(2024, 1, 15, 15, 31),
            payload={"headline": "One"},
            meta=ProviderMeta(provider_name="primary_news", received_at=datetime(2024, 1, 15, 15, 31)),
        )
    )
    __import__("asyncio").run(
        store.put_normalized(
            capability=ProviderCapability.NEWS.value,
            provider_name="primary_news",
            symbol="AAPL",
            fetched_at=datetime(2024, 1, 15, 15, 31),
            normalized_payload={"headline": "One"},
            raw_evidence_id=raw_id,
        )
    )

    health_summary = summarize_health(registry)
    evidence_summary = summarize_local_evidence(store)

    helper_view = summarize_evidence_eligibility_view(health_summary, evidence_summary=evidence_summary)
    registry_view = registry.provider_eligibility_view(evidence_summary)
    diagnostics_bundle = build_provider_diagnostic_bundle(registry, registry._health, store, temp_dir=str(tmp_path))

    helper_verdict = helper_view["primary_news"][ProviderCapability.NEWS.value]
    registry_verdict = registry_view["primary_news"][ProviderCapability.NEWS.value]
    diagnostics_verdict = diagnostics_bundle["eligibility"]["primary_news"][ProviderCapability.NEWS.value]

    assert helper_verdict.classification_code == registry_verdict.classification_code
    assert helper_verdict.classification_code == diagnostics_verdict.classification_code
    assert helper_verdict.eligibility == registry_verdict.eligibility
    assert helper_verdict.eligibility == diagnostics_verdict.eligibility


def test_evidence_helper_missing_or_malformed_inputs_fail_cleanly(tmp_path) -> None:
    with pytest.raises(ValueError, match="either evidence_source or evidence_summary must be provided"):
        summarize_evidence_eligibility_view({})

    with pytest.raises(TypeError, match="health_summary must be a dict"):
        summarize_evidence_eligibility_view([], evidence_source=tmp_path)

    with pytest.raises(TypeError, match="evidence_summary must be a dict when provided"):
        summarize_evidence_eligibility_view({}, evidence_summary=[])