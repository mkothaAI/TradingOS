from __future__ import annotations

import asyncio
from datetime import datetime

import pytest

from trading_os_v1.providers.adapters.polling_realtime import PollingRealtimeAdapter
from trading_os_v1.providers.schemas import ProviderCapability, ProviderMeta, QuoteSnapshot


class FakeMarketDataProvider:
    provider_name = "fake_market"
    provider_capability = ProviderCapability.MARKET_DATA

    def __init__(self) -> None:
        self.calls = []

    async def get_quote(self, symbol: str, as_of: datetime | None = None) -> QuoteSnapshot:
        self.calls.append(symbol)
        meta = ProviderMeta(provider_name=self.provider_name, received_at=datetime(2024, 1, 15, 15, 30))
        return QuoteSnapshot(symbol=symbol, as_of=as_of or datetime(2024, 1, 15, 15, 30), last=100.0, meta=meta)

    async def get_bars(self, symbol: str, start: datetime, end: datetime, timeframe: str):
        raise NotImplementedError


@pytest.mark.asyncio
async def test_polling_realtime_yields_normalized_quotes() -> None:
    market = FakeMarketDataProvider()
    adapter = PollingRealtimeAdapter(market, symbols=["AAPL", "MSFT"], polling_interval_seconds=0)
    stream = adapter.stream_quotes(["AAPL", "MSFT"])

    first = await stream.__anext__()
    second = await stream.__anext__()

    assert first.symbol == "AAPL"
    assert second.symbol == "MSFT"
    assert isinstance(first, QuoteSnapshot)
    assert isinstance(second, QuoteSnapshot)
    assert market.calls == ["AAPL", "MSFT"]

    await adapter.close()
    with pytest.raises(StopAsyncIteration):
        await stream.__anext__()


@pytest.mark.asyncio
async def test_polling_realtime_stops_cleanly() -> None:
    market = FakeMarketDataProvider()
    adapter = PollingRealtimeAdapter(market, symbols=["AAPL"], polling_interval_seconds=0)
    stream = adapter.stream_quotes(["AAPL"])

    await stream.__anext__()
    await adapter.close()

    with pytest.raises(StopAsyncIteration):
        await stream.__anext__()


@pytest.mark.asyncio
async def test_polling_realtime_is_deterministic_with_fake_market_provider() -> None:
    market = FakeMarketDataProvider()
    adapter = PollingRealtimeAdapter(market, symbols=["AAPL"], polling_interval_seconds=0)
    stream = adapter.stream_quotes(["AAPL"])

    first = await stream.__anext__()
    second = await stream.__anext__()

    assert first.model_dump() == second.model_dump()
    await adapter.close()