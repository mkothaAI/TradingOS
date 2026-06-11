from __future__ import annotations

from datetime import datetime

import pytest

from trading_os_v1.providers.adapters.finnhub import FinnhubAdapter
from trading_os_v1.providers.schemas import ProviderCapability


def test_finnhub_requires_api_key() -> None:
    with pytest.raises(ValueError):
        FinnhubAdapter(api_key="")


def test_finnhub_maps_news_payload_to_news_item() -> None:
    adapter = FinnhubAdapter(api_key="test-key", base_url="https://example.invalid", config={"timeout_seconds": 2})
    payload = {
        "id": "news-1",
        "datetime": 1705330800,
        "source": "Finnhub",
        "headline": "Apple reports results",
        "summary": "Quarterly update",
        "url": "https://example.com/story",
        "symbols": ["AAPL"],
        "language": "en",
        "author": "Reporter",
        "sentiment_score": 0.75,
        "received_at": datetime(2024, 1, 15, 15, 31),
    }

    item = adapter.map_news_payload_to_news_item(payload)

    assert item.news_id == "news-1"
    assert item.source_name == "Finnhub"
    assert item.title == "Apple reports results"
    assert item.symbols == ["AAPL"]
    assert item.meta.provider_name == "finnhub"
    assert item.meta.received_at == datetime(2024, 1, 15, 15, 31)


def test_finnhub_maps_earnings_payload_to_event() -> None:
    adapter = FinnhubAdapter(api_key="test-key")
    payload = {
        "symbol": "AAPL",
        "date": "2024-01-31T00:00:00",
        "time": "amc",
        "fiscal_year": 2024,
        "fiscal_quarter": 1,
        "eps_estimate": 2.1,
        "eps_actual": 2.25,
        "revenue_estimate": 100.0,
        "revenue_actual": 101.5,
        "status": "reported",
    }

    event = adapter.map_earnings_payload_to_event(payload)

    assert event.symbol == "AAPL"
    assert event.event_type == "earnings"
    assert event.fiscal_quarter == 1
    assert event.meta.provider_name == "finnhub"


def test_finnhub_capability_is_news() -> None:
    adapter = FinnhubAdapter(api_key="test-key")
    assert adapter.provider_capability == ProviderCapability.NEWS