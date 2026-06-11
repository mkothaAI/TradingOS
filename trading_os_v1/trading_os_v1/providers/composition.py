from __future__ import annotations

from datetime import datetime
from tempfile import TemporaryDirectory
from typing import Sequence

from trading_os_v1.providers.adapters.polling_realtime import PollingRealtimeAdapter
from trading_os_v1.providers.diagnostics import build_provider_diagnostic_bundle
from trading_os_v1.providers.evidence_summaries import correlate_health_and_evidence, summarize_local_evidence
from trading_os_v1.providers.local_evidence_store import LocalEvidenceStore
from trading_os_v1.providers.health_summaries import summarize_health
from trading_os_v1.providers.registry import ProviderBinding, ProviderRegistry
from trading_os_v1.providers.schemas import (
    CompanyFundamentals,
    EarningsEvent,
    NewsItem,
    PriceBar,
    ProviderCapability,
    ProviderMeta,
    QuoteSnapshot,
)


_FIXED_NOW = datetime(2024, 1, 15, 15, 30)


class _EvidenceWritingMarketDataProvider:
    def __init__(self, provider, evidence_store: LocalEvidenceStore | None) -> None:
        self._provider = provider
        self._evidence_store = evidence_store
        self.provider_name = provider.provider_name
        self.provider_capability = provider.provider_capability

    async def _persist(self, *, capability: ProviderCapability, symbol: str | None, fetched_at: datetime, payload: dict, meta: ProviderMeta) -> None:
        if self._evidence_store is None:
            return
        raw_id = await self._evidence_store.put_raw(
            capability=capability.value,
            provider_name=self.provider_name,
            symbol=symbol,
            fetched_at=fetched_at,
            payload=payload,
            meta=meta,
        )
        await self._evidence_store.put_normalized(
            capability=capability.value,
            provider_name=self.provider_name,
            symbol=symbol,
            fetched_at=fetched_at,
            normalized_payload=payload,
            raw_evidence_id=raw_id,
        )

    async def get_quote(self, symbol: str, as_of: datetime | None = None) -> QuoteSnapshot:
        quote = await self._provider.get_quote(symbol, as_of=as_of)
        await self._persist(
            capability=ProviderCapability.MARKET_DATA,
            symbol=quote.symbol,
            fetched_at=quote.as_of,
            payload=quote.model_dump(mode="json"),
            meta=quote.meta,
        )
        return quote

    async def get_bars(self, symbol: str, start: datetime, end: datetime, timeframe: str) -> list[PriceBar]:
        bars = await self._provider.get_bars(symbol, start=start, end=end, timeframe=timeframe)
        for bar in bars:
            await self._persist(
                capability=ProviderCapability.MARKET_DATA,
                symbol=bar.symbol,
                fetched_at=bar.end_at,
                payload=bar.model_dump(mode="json"),
                meta=bar.meta,
            )
        return bars


class _EvidenceWritingNewsProvider:
    def __init__(self, provider, evidence_store: LocalEvidenceStore | None) -> None:
        self._provider = provider
        self._evidence_store = evidence_store
        self.provider_name = provider.provider_name
        self.provider_capability = provider.provider_capability

    async def fetch_news(self, symbols: Sequence[str], start: datetime, end: datetime, limit: int = 100) -> list[NewsItem]:
        news_items = await self._provider.fetch_news(symbols, start=start, end=end, limit=limit)
        for item in news_items:
            if self._evidence_store is None:
                continue
            raw_id = await self._evidence_store.put_raw(
                capability=ProviderCapability.NEWS.value,
                provider_name=self.provider_name,
                symbol=item.symbols[0] if item.symbols else None,
                fetched_at=item.published_at,
                payload=item.model_dump(mode="json"),
                meta=item.meta,
            )
            await self._evidence_store.put_normalized(
                capability=ProviderCapability.NEWS.value,
                provider_name=self.provider_name,
                symbol=item.symbols[0] if item.symbols else None,
                fetched_at=item.published_at,
                normalized_payload=item.model_dump(mode="json"),
                raw_evidence_id=raw_id,
            )
        return news_items


class _EvidenceWritingEventProvider:
    def __init__(self, provider, evidence_store: LocalEvidenceStore | None) -> None:
        self._provider = provider
        self._evidence_store = evidence_store
        self.provider_name = provider.provider_name
        self.provider_capability = provider.provider_capability

    async def fetch_earnings_events(self, symbols: Sequence[str], start: datetime, end: datetime) -> list[EarningsEvent]:
        events = await self._provider.fetch_earnings_events(symbols, start=start, end=end)
        for event in events:
            if self._evidence_store is None:
                continue
            raw_id = await self._evidence_store.put_raw(
                capability=ProviderCapability.EVENT.value,
                provider_name=self.provider_name,
                symbol=event.symbol,
                fetched_at=event.event_date,
                payload=event.model_dump(mode="json"),
                meta=event.meta,
            )
            await self._evidence_store.put_normalized(
                capability=ProviderCapability.EVENT.value,
                provider_name=self.provider_name,
                symbol=event.symbol,
                fetched_at=event.event_date,
                normalized_payload=event.model_dump(mode="json"),
                raw_evidence_id=raw_id,
            )
        return events


class _EvidenceWritingFundamentalsProvider:
    def __init__(self, provider, evidence_store: LocalEvidenceStore | None) -> None:
        self._provider = provider
        self._evidence_store = evidence_store
        self.provider_name = provider.provider_name
        self.provider_capability = provider.provider_capability

    async def get_company_fundamentals(self, symbol: str, as_of: datetime | None = None) -> CompanyFundamentals:
        fundamentals = await self._provider.get_company_fundamentals(symbol, as_of=as_of)
        if self._evidence_store is not None:
            raw_id = await self._evidence_store.put_raw(
                capability=ProviderCapability.FUNDAMENTALS.value,
                provider_name=self.provider_name,
                symbol=fundamentals.symbol,
                fetched_at=fundamentals.as_of,
                payload=fundamentals.model_dump(mode="json"),
                meta=fundamentals.meta,
            )
            await self._evidence_store.put_normalized(
                capability=ProviderCapability.FUNDAMENTALS.value,
                provider_name=self.provider_name,
                symbol=fundamentals.symbol,
                fetched_at=fundamentals.as_of,
                normalized_payload=fundamentals.model_dump(mode="json"),
                raw_evidence_id=raw_id,
            )
        return fundamentals


class _FakeMarketDataProvider:
    provider_name = "fake_market_primary"
    provider_capability = ProviderCapability.MARKET_DATA

    async def get_quote(self, symbol: str, as_of: datetime | None = None) -> QuoteSnapshot:
        meta = ProviderMeta(provider_name=self.provider_name, received_at=_FIXED_NOW)
        return QuoteSnapshot(symbol=symbol, as_of=as_of or _FIXED_NOW, last=100.0, mid=100.0, meta=meta)

    async def get_bars(self, symbol: str, start: datetime, end: datetime, timeframe: str) -> list[PriceBar]:
        meta = ProviderMeta(provider_name=self.provider_name, received_at=_FIXED_NOW)
        return [
            PriceBar(
                symbol=symbol,
                timeframe=timeframe,
                start_at=start,
                end_at=end,
                open=99.0,
                high=101.0,
                low=98.0,
                close=100.0,
                volume=1000,
                meta=meta,
            )
        ]


class _FakeFallbackMarketDataProvider(_FakeMarketDataProvider):
    provider_name = "fake_market_fallback"


class _FakeNewsProvider:
    provider_name = "fake_news_primary"
    provider_capability = ProviderCapability.NEWS

    async def fetch_news(self, symbols: Sequence[str], start: datetime, end: datetime, limit: int = 100) -> list[NewsItem]:
        meta = ProviderMeta(provider_name=self.provider_name, received_at=_FIXED_NOW)
        return [
            NewsItem(
                news_id="news-1",
                published_at=start,
                source_name="Fake Wire",
                title=f"{symbols[0]} headline",
                symbols=list(symbols),
                meta=meta,
            )
        ]


class _FakeFallbackNewsProvider(_FakeNewsProvider):
    provider_name = "fake_news_fallback"


class _FakeEventProvider:
    provider_name = "fake_event_primary"
    provider_capability = ProviderCapability.EVENT

    async def fetch_earnings_events(self, symbols: Sequence[str], start: datetime, end: datetime) -> list[EarningsEvent]:
        meta = ProviderMeta(provider_name=self.provider_name, received_at=_FIXED_NOW)
        return [
            EarningsEvent(
                symbol=symbols[0],
                event_type="earnings",
                event_date=start,
                fiscal_year=2024,
                fiscal_quarter=1,
                meta=meta,
            )
        ]


class _FakeFallbackEventProvider(_FakeEventProvider):
    provider_name = "fake_event_fallback"


class _FakeFundamentalsProvider:
    provider_name = "fake_fundamentals_primary"
    provider_capability = ProviderCapability.FUNDAMENTALS

    async def get_company_fundamentals(self, symbol: str, as_of: datetime | None = None) -> CompanyFundamentals:
        meta = ProviderMeta(provider_name=self.provider_name, received_at=_FIXED_NOW)
        return CompanyFundamentals(symbol=symbol, as_of=as_of or _FIXED_NOW, company_name="Example Corp", market_cap=123.0, meta=meta)


class _FakeFallbackFundamentalsProvider(_FakeFundamentalsProvider):
    provider_name = "fake_fundamentals_fallback"


def build_test_provider_registry(
    *,
    symbols: Sequence[str] | None = None,
    polling_interval_seconds: float = 0.0,
    evidence_store: LocalEvidenceStore | None = None,
) -> ProviderRegistry:
    symbols = list(symbols or ["AAPL", "MSFT"])
    registry = ProviderRegistry()

    market_primary = _EvidenceWritingMarketDataProvider(_FakeMarketDataProvider(), evidence_store)
    market_fallback = _EvidenceWritingMarketDataProvider(_FakeFallbackMarketDataProvider(), evidence_store)
    news_primary = _EvidenceWritingNewsProvider(_FakeNewsProvider(), evidence_store)
    news_fallback = _EvidenceWritingNewsProvider(_FakeFallbackNewsProvider(), evidence_store)
    event_primary = _EvidenceWritingEventProvider(_FakeEventProvider(), evidence_store)
    event_fallback = _EvidenceWritingEventProvider(_FakeFallbackEventProvider(), evidence_store)
    fundamentals_primary = _EvidenceWritingFundamentalsProvider(_FakeFundamentalsProvider(), evidence_store)
    fundamentals_fallback = _EvidenceWritingFundamentalsProvider(_FakeFallbackFundamentalsProvider(), evidence_store)

    def register(capability: ProviderCapability, provider_name: str, factory, priority: int) -> None:
        registry.register(
            ProviderBinding(
                capability=capability,
                provider_name=provider_name,
                factory=factory,
                priority=priority,
            )
        )

    register(ProviderCapability.MARKET_DATA, market_primary.provider_name, lambda: market_primary, priority=0)
    register(ProviderCapability.MARKET_DATA, market_fallback.provider_name, lambda: market_fallback, priority=10)

    register(ProviderCapability.NEWS, news_primary.provider_name, lambda: news_primary, priority=0)
    register(ProviderCapability.NEWS, news_fallback.provider_name, lambda: news_fallback, priority=10)

    register(ProviderCapability.EVENT, event_primary.provider_name, lambda: event_primary, priority=0)
    register(ProviderCapability.EVENT, event_fallback.provider_name, lambda: event_fallback, priority=10)

    register(ProviderCapability.FUNDAMENTALS, fundamentals_primary.provider_name, lambda: fundamentals_primary, priority=0)
    register(ProviderCapability.FUNDAMENTALS, fundamentals_fallback.provider_name, lambda: fundamentals_fallback, priority=10)

    realtime_provider = PollingRealtimeAdapter(
        market_data_provider=market_primary,
        symbols=symbols,
        polling_interval_seconds=polling_interval_seconds,
    )
    register(ProviderCapability.REALTIME_STREAM, "polling_realtime", lambda: realtime_provider, priority=0)

    return registry


def build_test_provider_registry_with_health_summary(
    *,
    symbols: Sequence[str] | None = None,
    polling_interval_seconds: float = 0.0,
    evidence_store: LocalEvidenceStore | None = None,
) -> tuple[ProviderRegistry, dict[str, dict]]:
    registry = build_test_provider_registry(
        symbols=symbols,
        polling_interval_seconds=polling_interval_seconds,
        evidence_store=evidence_store,
    )
    return registry, summarize_health(registry)


def build_test_provider_registry_with_diagnostics(
    *,
    symbols: Sequence[str] | None = None,
    polling_interval_seconds: float = 0.0,
    evidence_store: LocalEvidenceStore | None = None,
) -> tuple[ProviderRegistry, dict[str, dict], dict[str, dict], dict[str, dict]]:
    registry = build_test_provider_registry(
        symbols=symbols,
        polling_interval_seconds=polling_interval_seconds,
        evidence_store=evidence_store,
    )
    health_summary = summarize_health(registry)
    evidence_summary = summarize_local_evidence(evidence_store or ".") if evidence_store is not None else {}
    correlated = correlate_health_and_evidence(health_summary, evidence_summary)
    return registry, health_summary, evidence_summary, correlated


def build_test_provider_diagnostic_bundle(
    *,
    symbols: Sequence[str] | None = None,
    polling_interval_seconds: float = 0.0,
    evidence_store: LocalEvidenceStore | None = None,
) -> dict:
    with TemporaryDirectory() as temp_dir:
        store = evidence_store or LocalEvidenceStore(temp_dir)
        registry = build_test_provider_registry(
            symbols=symbols,
            polling_interval_seconds=polling_interval_seconds,
            evidence_store=store,
        )
        return build_provider_diagnostic_bundle(registry, registry._health, store, temp_dir=temp_dir)