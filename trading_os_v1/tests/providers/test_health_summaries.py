from __future__ import annotations

from datetime import datetime

from trading_os_v1.providers.composition import build_test_provider_registry, build_test_provider_registry_with_health_summary
from trading_os_v1.providers.health import ProviderHealthManager
from trading_os_v1.providers.health_summaries import summarize_health
from trading_os_v1.providers.registry import ProviderBinding, ProviderRegistry
from trading_os_v1.providers.schemas import ProviderCapability


def test_summarize_health_groups_by_provider_and_capability() -> None:
    manager = ProviderHealthManager()
    registry = ProviderRegistry(manager)

    registry.register(
        ProviderBinding(
            capability=ProviderCapability.NEWS,
            provider_name="news_primary",
            factory=lambda: object(),
            priority=0,
        )
    )
    registry.register(
        ProviderBinding(
            capability=ProviderCapability.FUNDAMENTALS,
            provider_name="fundamentals_primary",
            factory=lambda: object(),
            priority=0,
        )
    )

    manager.record_success("news_primary", ProviderCapability.NEWS, latency_ms=10.0, quota_remaining=99, now=datetime(2024, 1, 15, 15, 30))
    manager.record_failure("fundamentals_primary", ProviderCapability.FUNDAMENTALS, error_code="TIMEOUT", error_message="slow", now=datetime(2024, 1, 15, 15, 31))

    summary = summarize_health(registry, capabilities=[ProviderCapability.NEWS, ProviderCapability.FUNDAMENTALS])

    assert summary[ProviderCapability.NEWS.value]["providers"]["news_primary"]["status"] == "healthy"
    assert summary[ProviderCapability.FUNDAMENTALS.value]["providers"]["fundamentals_primary"]["status"] == "degraded"


def test_summarize_health_worst_status_rollup_is_correct() -> None:
    manager = ProviderHealthManager()
    registry = ProviderRegistry(manager)

    registry.register(
        ProviderBinding(
            capability=ProviderCapability.NEWS,
            provider_name="news_primary",
            factory=lambda: object(),
            priority=0,
        )
    )
    registry.register(
        ProviderBinding(
            capability=ProviderCapability.NEWS,
            provider_name="news_fallback",
            factory=lambda: object(),
            priority=10,
        )
    )

    manager.record_success("news_primary", ProviderCapability.NEWS, latency_ms=10.0, now=datetime(2024, 1, 15, 15, 30))
    manager.record_failure("news_fallback", ProviderCapability.NEWS, error_code="AUTH", error_message="down", now=datetime(2024, 1, 15, 15, 31))

    summary = summarize_health(registry, capabilities=[ProviderCapability.NEWS])
    assert summary[ProviderCapability.NEWS.value]["capability_status"] == "down"


def test_summarize_health_includes_disabled_and_degraded_states() -> None:
    manager = ProviderHealthManager()
    registry = ProviderRegistry(manager)

    registry.register(
        ProviderBinding(
            capability=ProviderCapability.EVENT,
            provider_name="event_primary",
            factory=lambda: object(),
            priority=0,
        )
    )
    registry.register(
        ProviderBinding(
            capability=ProviderCapability.EVENT,
            provider_name="event_disabled",
            factory=lambda: object(),
            priority=10,
            enabled=False,
        )
    )

    manager.record_failure("event_primary", ProviderCapability.EVENT, error_code="RATE_LIMIT", error_message="quota", now=datetime(2024, 1, 15, 15, 32))

    summary = summarize_health(registry, capabilities=[ProviderCapability.EVENT])
    assert summary[ProviderCapability.EVENT.value]["providers"]["event_primary"]["status"] == "degraded"
    assert summary[ProviderCapability.EVENT.value]["providers"]["event_disabled"]["status"] == "disabled"
    assert summary[ProviderCapability.EVENT.value]["capability_status"] == "disabled"


def test_composed_registry_can_return_health_summary() -> None:
    registry, summary = build_test_provider_registry_with_health_summary()
    assert summary[ProviderCapability.MARKET_DATA.value]["providers"]["fake_market_primary"]["status"] is None
    assert registry.resolve(ProviderCapability.MARKET_DATA).provider_name == "fake_market_primary"


def test_summarize_health_accepts_health_manager_directly() -> None:
    manager = ProviderHealthManager()
    manager.record_success("direct_news", ProviderCapability.NEWS, latency_ms=12.0, now=datetime(2024, 1, 15, 15, 30))

    summary = summarize_health(manager, capabilities=[ProviderCapability.NEWS])
    assert summary[ProviderCapability.NEWS.value]["capability_status"] is None