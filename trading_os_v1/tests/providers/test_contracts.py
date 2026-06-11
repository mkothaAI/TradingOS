from __future__ import annotations

from datetime import datetime
import asyncio

from trading_os_v1.providers.base import (
    EventProvider,
    FundamentalsProvider,
    MarketDataProvider,
    NewsProvider,
    RealtimeStreamProvider,
)
from trading_os_v1.providers.evidence_store import EvidenceStore
from trading_os_v1.providers.health import ProviderHealthManager
from trading_os_v1.providers.schemas import (
    CompanyFundamentals,
    EarningsEvent,
    NewsItem,
    PriceBar,
    ProviderCapability,
    ProviderMeta,
    QuoteSnapshot,
)


class FakeEvidenceStore:
    def __init__(self) -> None:
        self.raw = {}
        self.normalized = {}
        self._counter = 0

    async def put_raw(self, *, capability, provider_name, symbol, fetched_at, payload, meta) -> str:
        self._counter += 1
        evidence_id = f"raw-{self._counter}"
        self.raw[evidence_id] = {
            "capability": capability,
            "provider_name": provider_name,
            "symbol": symbol,
            "fetched_at": fetched_at,
            "payload": payload,
            "meta": meta.model_dump(),
        }
        return evidence_id

    async def put_normalized(self, *, capability, provider_name, symbol, fetched_at, normalized_payload, raw_evidence_id) -> str:
        self._counter += 1
        evidence_id = f"normalized-{self._counter}"
        self.normalized[evidence_id] = {
            "capability": capability,
            "provider_name": provider_name,
            "symbol": symbol,
            "fetched_at": fetched_at,
            "normalized_payload": normalized_payload,
            "raw_evidence_id": raw_evidence_id,
        }
        return evidence_id

    async def get_raw(self, evidence_id: str):
        return self.raw.get(evidence_id)

    async def get_normalized(self, evidence_id: str):
        return self.normalized.get(evidence_id)


class FakeMarketDataProvider:
    provider_name = "fake_market"
    provider_capability = ProviderCapability.MARKET_DATA

    async def get_quote(self, symbol: str, as_of: datetime | None = None) -> QuoteSnapshot:
        meta = ProviderMeta(provider_name=self.provider_name, received_at=datetime(2024, 1, 15, 15, 30))
        return QuoteSnapshot(symbol=symbol, as_of=as_of or datetime(2024, 1, 15, 15, 30), last=100.0, meta=meta)

    async def get_bars(self, symbol: str, start: datetime, end: datetime, timeframe: str) -> list[PriceBar]:
        meta = ProviderMeta(provider_name=self.provider_name, received_at=datetime(2024, 1, 15, 15, 30))
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


class FakeRealtimeProvider:
    provider_name = "fake_realtime"
    provider_capability = ProviderCapability.REALTIME_STREAM

    async def stream_quotes(self, symbols):
        if False:
            yield None

    async def stream_bars(self, symbols, timeframe):
        if False:
            yield None

    async def close(self) -> None:
        return None


class FakeNewsProvider:
    provider_name = "fake_news"
    provider_capability = ProviderCapability.NEWS

    async def fetch_news(self, symbols, start, end, limit: int = 100) -> list[NewsItem]:
        meta = ProviderMeta(provider_name=self.provider_name, received_at=datetime(2024, 1, 15, 15, 30))
        return [
            NewsItem(
                news_id="news-1",
                published_at=start,
                source_name="Example Wire",
                title="Example headline",
                symbols=list(symbols),
                meta=meta,
            )
        ]


class FakeEventProvider:
    provider_name = "fake_event"
    provider_capability = ProviderCapability.EVENT

    async def fetch_earnings_events(self, symbols, start, end) -> list[EarningsEvent]:
        meta = ProviderMeta(provider_name=self.provider_name, received_at=datetime(2024, 1, 15, 15, 30))
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


class FakeFundamentalsProvider:
    provider_name = "fake_fundamentals"
    provider_capability = ProviderCapability.FUNDAMENTALS

    async def get_company_fundamentals(self, symbol: str, as_of: datetime | None = None) -> CompanyFundamentals:
        meta = ProviderMeta(provider_name=self.provider_name, received_at=datetime(2024, 1, 15, 15, 30))
        return CompanyFundamentals(symbol=symbol, as_of=as_of or datetime(2024, 1, 15, 15, 30), market_cap=100.0, meta=meta)


def test_schema_round_trips() -> None:
    meta = ProviderMeta(provider_name="fake", received_at=datetime(2024, 1, 15, 15, 30))
    quote = QuoteSnapshot(symbol="AAPL", as_of=datetime(2024, 1, 15, 15, 30), last=100.0, meta=meta)
    restored = QuoteSnapshot.model_validate(quote.model_dump())
    assert restored == quote

    bar = PriceBar(
        symbol="AAPL",
        timeframe="1d",
        start_at=datetime(2024, 1, 15, 9, 30),
        end_at=datetime(2024, 1, 15, 16, 0),
        open=99.0,
        high=101.0,
        low=98.0,
        close=100.0,
        volume=1000,
        meta=meta,
    )
    assert PriceBar.model_validate(bar.model_dump()) == bar

    news = NewsItem(
        news_id="news-1",
        published_at=datetime(2024, 1, 15, 10, 0),
        source_name="Example",
        title="Headline",
        meta=meta,
    )
    assert NewsItem.model_validate(news.model_dump()) == news

    event = EarningsEvent(symbol="AAPL", event_type="earnings", event_date=datetime(2024, 1, 15), meta=meta)
    assert EarningsEvent.model_validate(event.model_dump()) == event

    fundamentals = CompanyFundamentals(symbol="AAPL", as_of=datetime(2024, 1, 15), market_cap=100.0, meta=meta)
    assert CompanyFundamentals.model_validate(fundamentals.model_dump()) == fundamentals


def test_provider_protocols_are_satisfied() -> None:
    assert isinstance(FakeMarketDataProvider(), MarketDataProvider)
    assert isinstance(FakeRealtimeProvider(), RealtimeStreamProvider)
    assert isinstance(FakeNewsProvider(), NewsProvider)
    assert isinstance(FakeEventProvider(), EventProvider)
    assert isinstance(FakeFundamentalsProvider(), FundamentalsProvider)


def test_provider_capability_enum_values() -> None:
    assert ProviderCapability.MARKET_DATA.value == "market_data"
    assert ProviderCapability.NEWS.value == "news"


def test_health_record_success_and_failure() -> None:
    manager = ProviderHealthManager()
    fixed_now = datetime(2024, 1, 15, 15, 30)
    success = manager.record_success("fmp", ProviderCapability.FUNDAMENTALS, latency_ms=12.5, quota_remaining=99, now=fixed_now)
    assert success.status == "healthy"
    assert success.last_success_at == fixed_now
    assert success.quota_remaining == 99

    failure = manager.record_failure("fmp", ProviderCapability.FUNDAMENTALS, error_code="RATE_LIMIT", error_message="quota exceeded", now=fixed_now)
    assert failure.status == "degraded"
    assert failure.quota_remaining == 0
    assert failure.last_error_code == "RATE_LIMIT"


def test_evidence_store_contract_exercised() -> None:
    store = FakeEvidenceStore()
    meta = ProviderMeta(provider_name="fake_news", received_at=datetime(2024, 1, 15, 15, 30))

    async def exercise() -> None:
        raw_id = await store.put_raw(
            capability=ProviderCapability.NEWS.value,
            provider_name="fake_news",
            symbol="AAPL",
            fetched_at=datetime(2024, 1, 15, 15, 30),
            payload={"headline": "Example"},
            meta=meta,
        )
        normalized_id = await store.put_normalized(
            capability=ProviderCapability.NEWS.value,
            provider_name="fake_news",
            symbol="AAPL",
            fetched_at=datetime(2024, 1, 15, 15, 30),
            normalized_payload={"news_id": "news-1"},
            raw_evidence_id=raw_id,
        )
        assert await store.get_raw(raw_id)
        assert await store.get_normalized(normalized_id)

    asyncio.run(exercise())