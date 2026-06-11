from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Sequence

from trading_os_v1.providers.base import MarketDataProvider, RealtimeStreamProvider
from trading_os_v1.providers.schemas import PriceBar, ProviderCapability, QuoteSnapshot


class PollingRealtimeAdapter(RealtimeStreamProvider):
    provider_name = "polling_realtime"
    provider_capability = ProviderCapability.REALTIME_STREAM

    def __init__(
        self,
        market_data_provider: MarketDataProvider,
        symbols: Sequence[str],
        polling_interval_seconds: float = 1.0,
    ) -> None:
        self.market_data_provider = market_data_provider
        self.symbols = list(symbols)
        self.polling_interval_seconds = polling_interval_seconds
        self._closed = False

    async def stream_quotes(self, symbols: Sequence[str]) -> QuoteSnapshot:
        active_symbols = list(symbols) or list(self.symbols)
        while not self._closed:
            for symbol in active_symbols:
                quote = await self.market_data_provider.get_quote(symbol)
                yield quote
            if self.polling_interval_seconds > 0:
                await asyncio.sleep(self.polling_interval_seconds)

    async def stream_bars(self, symbols: Sequence[str], timeframe: str):
        active_symbols = list(symbols) or list(self.symbols)
        while not self._closed:
            for symbol in active_symbols:
                bars = await self.market_data_provider.get_bars(
                    symbol,
                    start=datetime.utcnow(),
                    end=datetime.utcnow(),
                    timeframe=timeframe,
                )
                for bar in bars:
                    yield bar
            if self.polling_interval_seconds > 0:
                await asyncio.sleep(self.polling_interval_seconds)

    async def close(self) -> None:
        self._closed = True