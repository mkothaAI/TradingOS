from __future__ import annotations

from datetime import datetime
from typing import AsyncIterator, Protocol, Sequence, runtime_checkable

from .schemas import CompanyFundamentals, EarningsEvent, NewsItem, PriceBar, ProviderCapability, QuoteSnapshot


@runtime_checkable
class MarketDataProvider(Protocol):
    provider_name: str
    provider_capability: ProviderCapability

    async def get_quote(self, symbol: str, as_of: datetime | None = None) -> QuoteSnapshot: ...

    async def get_bars(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
        timeframe: str,
    ) -> list[PriceBar]: ...


@runtime_checkable
class RealtimeStreamProvider(Protocol):
    provider_name: str
    provider_capability: ProviderCapability

    async def stream_quotes(self, symbols: Sequence[str]) -> AsyncIterator[QuoteSnapshot]: ...

    async def stream_bars(self, symbols: Sequence[str], timeframe: str) -> AsyncIterator[PriceBar]: ...

    async def close(self) -> None: ...


@runtime_checkable
class NewsProvider(Protocol):
    provider_name: str
    provider_capability: ProviderCapability

    async def fetch_news(
        self,
        symbols: Sequence[str],
        start: datetime,
        end: datetime,
        limit: int = 100,
    ) -> list[NewsItem]: ...


@runtime_checkable
class EventProvider(Protocol):
    provider_name: str
    provider_capability: ProviderCapability

    async def fetch_earnings_events(
        self,
        symbols: Sequence[str],
        start: datetime,
        end: datetime,
    ) -> list[EarningsEvent]: ...


@runtime_checkable
class FundamentalsProvider(Protocol):
    provider_name: str
    provider_capability: ProviderCapability

    async def get_company_fundamentals(
        self,
        symbol: str,
        as_of: datetime | None = None,
    ) -> CompanyFundamentals: ...