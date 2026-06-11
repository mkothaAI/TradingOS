from __future__ import annotations

from datetime import datetime, timezone

from trading_os_v1.providers.evidence_summaries import correlate_health_and_evidence, summarize_local_evidence
from trading_os_v1.providers.eligibility import (
    classify_provider_eligibility,
    summarize_provider_eligibility,
)
from trading_os_v1.providers.health import ProviderHealthManager
from trading_os_v1.providers.health_summaries import summarize_health
from trading_os_v1.providers.local_evidence_store import LocalEvidenceStore
from trading_os_v1.providers.registry import ProviderBinding, ProviderRegistry
from trading_os_v1.providers.schemas import ProviderCapability, ProviderMeta


UTC_NOW = datetime(2024, 1, 15, 15, 30, tzinfo=timezone.utc)


def _evidence_bucket(*, raw_count: int, normalized_count: int, total_count: int | None = None) -> dict[str, int]:
    bucket = {
        "raw_count": raw_count,
        "normalized_count": normalized_count,
        "total_count": total_count if total_count is not None else raw_count + normalized_count,
    }
    return bucket


def test_healthy_provider_with_complete_evidence_is_eligible() -> None:
    verdict = classify_provider_eligibility(
        provider_name="tiingo",
        capability=ProviderCapability.MARKET_DATA.value,
        health_status={"status": "healthy", "last_error_code": None},
        evidence_status=_evidence_bucket(raw_count=2, normalized_count=2),
    )

    assert verdict.health_state == "healthy"
    assert verdict.eligibility == "eligible"
    assert verdict.classification_code == "HEALTHY_ELIGIBLE"
    assert verdict.reason_codes == ("HEALTH_OK", "EVIDENCE_COMPLETE")


def test_degraded_provider_with_complete_evidence_is_eligible() -> None:
    verdict = classify_provider_eligibility(
        provider_name="twelvedata",
        capability=ProviderCapability.REALTIME_STREAM.value,
        health_status={"status": "degraded", "last_error_code": "TIMEOUT"},
        evidence_status=_evidence_bucket(raw_count=1, normalized_count=1),
    )

    assert verdict.health_state == "degraded"
    assert verdict.eligibility == "eligible"
    assert verdict.classification_code == "DEGRADED_EVIDENCE_ELIGIBLE"
    assert verdict.last_error_code == "TIMEOUT"


def test_terminal_provider_is_not_eligible() -> None:
    verdict = classify_provider_eligibility(
        provider_name="tiingo",
        capability=ProviderCapability.MARKET_DATA.value,
        health_status={"status": "down", "last_error_code": "AUTH"},
        evidence_status=_evidence_bucket(raw_count=1, normalized_count=1),
    )

    assert verdict.health_state == "terminal"
    assert verdict.eligibility == "not_eligible"
    assert verdict.classification_code == "TERMINAL_AUTH_NOT_ELIGIBLE"
    assert "HEALTH_ERROR_AUTH" in verdict.reason_codes


def test_disabled_provider_is_terminal_even_with_evidence() -> None:
    verdict = classify_provider_eligibility(
        provider_name="fallback_news",
        capability=ProviderCapability.NEWS.value,
        health_status={"status": "disabled", "last_error_code": None},
        evidence_status=_evidence_bucket(raw_count=1, normalized_count=1),
    )

    assert verdict.health_state == "terminal"
    assert verdict.eligibility == "not_eligible"
    assert verdict.classification_code == "TERMINAL_DISABLED_NOT_ELIGIBLE"
    assert verdict.reason_codes == ("HEALTH_DISABLED",)


def test_partial_or_missing_evidence_is_not_eligible() -> None:
    verdict = classify_provider_eligibility(
        provider_name="tiingo",
        capability=ProviderCapability.MARKET_DATA.value,
        health_status={"status": "healthy", "last_error_code": None},
        evidence_status=_evidence_bucket(raw_count=1, normalized_count=0),
    )

    assert verdict.health_state == "degraded"
    assert verdict.eligibility == "not_eligible"
    assert verdict.classification_code == "DEGRADED_PARTIAL_EVIDENCE_NOT_ELIGIBLE"
    assert "MISSING_NORMALIZED_EVIDENCE" in verdict.reason_codes


def test_summary_join_over_health_and_evidence_is_deterministic(tmp_path) -> None:
    store = LocalEvidenceStore(tmp_path)
    manager = ProviderHealthManager()
    registry = ProviderRegistry(manager)

    registry.register(
        ProviderBinding(
            capability=ProviderCapability.MARKET_DATA,
            provider_name="fake_market_primary",
            factory=lambda: object(),
            priority=0,
        )
    )
    registry.register(
        ProviderBinding(
            capability=ProviderCapability.NEWS,
            provider_name="fake_news_primary",
            factory=lambda: object(),
            priority=0,
        )
    )

    manager.record_success("fake_market_primary", ProviderCapability.MARKET_DATA, latency_ms=10.0, now=UTC_NOW)
    manager.record_failure("fake_news_primary", ProviderCapability.NEWS, error_code="RATE_LIMIT", error_message="slow", now=UTC_NOW)

    import asyncio

    raw_id = asyncio.run(
        store.put_raw(
            capability=ProviderCapability.MARKET_DATA.value,
            provider_name="fake_market_primary",
            symbol="AAPL",
            fetched_at=UTC_NOW,
            payload={"last": 100.0},
            meta=ProviderMeta(provider_name="fake_market_primary", received_at=UTC_NOW),
        )
    )
    asyncio.run(
        store.put_normalized(
            capability=ProviderCapability.MARKET_DATA.value,
            provider_name="fake_market_primary",
            symbol="AAPL",
            fetched_at=UTC_NOW,
            normalized_payload={"last": 100.0},
            raw_evidence_id=raw_id,
        )
    )

    health_summary = summarize_health(registry)
    evidence_summary = summarize_local_evidence(tmp_path)
    correlated = correlate_health_and_evidence(health_summary, evidence_summary)
    verdicts = summarize_provider_eligibility(health_summary, evidence_summary)

    assert correlated["fake_market_primary"][ProviderCapability.MARKET_DATA.value]["health_status"] == "healthy"
    assert verdicts["fake_market_primary"][ProviderCapability.MARKET_DATA.value].classification_code == "HEALTHY_ELIGIBLE"
    assert verdicts["fake_news_primary"][ProviderCapability.NEWS.value].classification_code == "DEGRADED_NO_EVIDENCE_NOT_ELIGIBLE"