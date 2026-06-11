from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import pytest

from trading_os_v1.providers.evidence_summaries import summarize_local_evidence
from trading_os_v1.providers.health import ProviderHealthManager
from trading_os_v1.providers.registry import ProviderBinding, ProviderRegistry
from trading_os_v1.providers.schemas import ProviderCapability


@dataclass
class DummyProvider:
    name: str


def make_registry() -> ProviderRegistry:
    return ProviderRegistry(ProviderHealthManager())


def test_registry_resolves_primary() -> None:
    registry = make_registry()
    registry.register(
        ProviderBinding(
            capability=ProviderCapability.NEWS,
            provider_name="primary_news",
            factory=lambda: DummyProvider("primary_news"),
            priority=0,
        )
    )
    registry.register(
        ProviderBinding(
            capability=ProviderCapability.NEWS,
            provider_name="fallback_news",
            factory=lambda: DummyProvider("fallback_news"),
            priority=10,
        )
    )

    selected = registry.resolve(ProviderCapability.NEWS)
    assert selected.name == "primary_news"


def test_registry_falls_back_when_primary_disabled() -> None:
    registry = make_registry()
    registry.register(
        ProviderBinding(
            capability=ProviderCapability.FUNDAMENTALS,
            provider_name="primary_fundamentals",
            factory=lambda: DummyProvider("primary_fundamentals"),
            priority=0,
            enabled=False,
        )
    )
    registry.register(
        ProviderBinding(
            capability=ProviderCapability.FUNDAMENTALS,
            provider_name="fallback_fundamentals",
            factory=lambda: DummyProvider("fallback_fundamentals"),
            priority=10,
        )
    )

    selected = registry.resolve(ProviderCapability.FUNDAMENTALS)
    assert selected.name == "fallback_fundamentals"


def test_registry_skips_down_provider_when_health_known() -> None:
    registry = make_registry()
    registry.register(
        ProviderBinding(
            capability=ProviderCapability.EVENT,
            provider_name="primary_event",
            factory=lambda: DummyProvider("primary_event"),
            priority=0,
        )
    )
    registry.register(
        ProviderBinding(
            capability=ProviderCapability.EVENT,
            provider_name="fallback_event",
            factory=lambda: DummyProvider("fallback_event"),
            priority=10,
        )
    )
    registry.set_health(
        registry._health.record_failure(
            "primary_event",
            ProviderCapability.EVENT,
            error_code="AUTH",
            error_message="unauthorized",
            now=datetime(2024, 1, 15, 15, 30),
        )
    )

    selected = registry.resolve(ProviderCapability.EVENT)
    assert selected.name == "fallback_event"


def test_registry_deterministic_priority_order() -> None:
    registry = make_registry()
    registry.register(
        ProviderBinding(
            capability=ProviderCapability.MARKET_DATA,
            provider_name="b_provider",
            factory=lambda: DummyProvider("b_provider"),
            priority=5,
        )
    )
    registry.register(
        ProviderBinding(
            capability=ProviderCapability.MARKET_DATA,
            provider_name="a_provider",
            factory=lambda: DummyProvider("a_provider"),
            priority=5,
        )
    )

    resolved = registry.resolve_all(ProviderCapability.MARKET_DATA)
    assert [provider.name for provider in resolved] == ["a_provider", "b_provider"]


def test_registry_unknown_capability_raises() -> None:
    registry = make_registry()
    with pytest.raises(KeyError):
        registry.resolve(ProviderCapability.REALTIME_STREAM)


def test_registry_health_updates_resolution() -> None:
    registry = make_registry()
    registry.register(
        ProviderBinding(
            capability=ProviderCapability.NEWS,
            provider_name="primary_news",
            factory=lambda: DummyProvider("primary_news"),
            priority=0,
        )
    )
    registry.register(
        ProviderBinding(
            capability=ProviderCapability.NEWS,
            provider_name="fallback_news",
            factory=lambda: DummyProvider("fallback_news"),
            priority=10,
        )
    )

    selected_before = registry.resolve(ProviderCapability.NEWS)
    assert selected_before.name == "primary_news"

    registry.set_health(
        registry._health.mark_degraded(
            "primary_news",
            ProviderCapability.NEWS,
            reason="slower than expected",
            now=datetime(2024, 1, 15, 15, 30),
        )
    )
    selected_after = registry.resolve(ProviderCapability.NEWS)
    assert selected_after.name == "primary_news"


def test_registry_can_expose_provider_eligibility_view(tmp_path) -> None:
    registry = make_registry()
    registry.register(
        ProviderBinding(
            capability=ProviderCapability.MARKET_DATA,
            provider_name="primary_market",
            factory=lambda: DummyProvider("primary_market"),
            priority=0,
        )
    )
    registry.set_health(
        registry._health.record_success(
            "primary_market",
            ProviderCapability.MARKET_DATA,
            latency_ms=12.0,
            now=datetime(2024, 1, 15, 15, 30),
        )
    )

    import asyncio

    from trading_os_v1.providers.local_evidence_store import LocalEvidenceStore
    from trading_os_v1.providers.schemas import ProviderMeta

    store = LocalEvidenceStore(tmp_path)
    raw_id = asyncio.run(
        store.put_raw(
            capability=ProviderCapability.MARKET_DATA.value,
            provider_name="primary_market",
            symbol="AAPL",
            fetched_at=datetime(2024, 1, 15, 15, 30),
            payload={"last": 100.0},
            meta=ProviderMeta(provider_name="primary_market", received_at=datetime(2024, 1, 15, 15, 30)),
        )
    )
    asyncio.run(
        store.put_normalized(
            capability=ProviderCapability.MARKET_DATA.value,
            provider_name="primary_market",
            symbol="AAPL",
            fetched_at=datetime(2024, 1, 15, 15, 30),
            normalized_payload={"last": 100.0},
            raw_evidence_id=raw_id,
        )
    )

    eligibility_view = registry.provider_eligibility_view(summarize_local_evidence(store))

    verdict = eligibility_view["primary_market"][ProviderCapability.MARKET_DATA.value]
    assert verdict.classification_code == "HEALTHY_ELIGIBLE"
    assert verdict.eligibility == "eligible"