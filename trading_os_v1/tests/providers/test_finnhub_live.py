from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from trading_os_v1.providers.adapters.finnhub import FinnhubConfig, FinnhubEventAdapter, FinnhubNewsAdapter
from trading_os_v1.providers.evidence_summaries import summarize_local_evidence
from trading_os_v1.providers.health import ProviderHealthManager
from trading_os_v1.providers.health_summaries import summarize_health
from trading_os_v1.providers.local_evidence_store import LocalEvidenceStore
from trading_os_v1.providers.registry import ProviderBinding, ProviderRegistry
from trading_os_v1.providers.schemas import ProviderCapability, NewsItem, EarningsEvent


def _resolve_live_config() -> FinnhubConfig:
    import os

    api_key = os.getenv("FINNHUB_API_KEY") or os.getenv("FINNHUB_TOKEN") or os.getenv("FINNHUB_API_TOKEN")
    if not api_key:
        pytest.skip("Finnhub API key is not available in the environment")
    return FinnhubConfig(api_key=api_key, base_url="https://finnhub.io/api/v1")


@pytest.mark.asyncio
async def test_finnhub_live_news_and_earnings_round_trip(tmp_path) -> None:
    config = _resolve_live_config()
    evidence_store = LocalEvidenceStore(tmp_path)
    health_manager = ProviderHealthManager()
    registry = ProviderRegistry(health_manager)

    news_adapter = FinnhubNewsAdapter(
        config=config,
        evidence_store=evidence_store,
        health_manager=health_manager,
    )
    event_adapter = FinnhubEventAdapter(
        config=config,
        evidence_store=evidence_store,
        health_manager=health_manager,
    )

    registry.register(
        ProviderBinding(
            capability=ProviderCapability.NEWS,
            provider_name=news_adapter.provider_name,
            factory=lambda: news_adapter,
            priority=0,
        )
    )
    registry.register(
        ProviderBinding(
            capability=ProviderCapability.EVENT,
            provider_name=event_adapter.provider_name,
            factory=lambda: event_adapter,
            priority=0,
        )
    )

    news_provider = registry.resolve(ProviderCapability.NEWS)
    event_provider = registry.resolve(ProviderCapability.EVENT)

    news_items = await news_provider.fetch_news(
        ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL"],
        start=datetime.now(timezone.utc) - timedelta(days=1),
        end=datetime.now(timezone.utc),
        limit=1,
    )
    earnings_events = await event_provider.fetch_earnings_events(
        ["AAPL"],
        start=datetime.now(timezone.utc) - timedelta(days=240),
        end=datetime.now(timezone.utc) + timedelta(days=30),
    )

    if not news_items or not earnings_events:
        pytest.skip("Finnhub live data is unavailable for this run")

    assert news_items, "expected at least one live Finnhub news item"
    assert earnings_events, "expected at least one live Finnhub earnings event"

    assert isinstance(news_items[0], NewsItem)
    assert isinstance(earnings_events[0], EarningsEvent)
    assert news_items[0].meta.provider_name == news_adapter.provider_name
    assert earnings_events[0].meta.provider_name == event_adapter.provider_name
    assert news_items[0].symbols or news_items[0].title
    assert earnings_events[0].symbol == "AAPL"

    evidence_summary = summarize_local_evidence(evidence_store)
    health_summary = summarize_health(registry)

    assert evidence_summary[news_adapter.provider_name][ProviderCapability.NEWS.value]["raw_count"] >= 1
    assert evidence_summary[event_adapter.provider_name][ProviderCapability.EVENT.value]["raw_count"] >= 1
    assert health_summary[ProviderCapability.NEWS.value]["providers"][news_adapter.provider_name]["status"] == "healthy"
    assert health_summary[ProviderCapability.EVENT.value]["providers"][event_adapter.provider_name]["status"] == "healthy"
