from __future__ import annotations

import asyncio
import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

import httpx
import websockets

from trading_os_v1.providers.base import EventProvider, NewsProvider
from trading_os_v1.providers.evidence_store import EvidenceStore
from trading_os_v1.providers.health import ProviderHealthManager
from trading_os_v1.providers.schemas import EarningsEvent, NewsItem, ProviderCapability, ProviderMeta


_DEFAULT_REST_BASE_URL = "https://finnhub.io/api/v1"
_DEFAULT_WEBSOCKET_URL = "wss://ws.finnhub.io"
_FINNHUB_ENV_KEYS = ("FINNHUB_API_KEY", "FINNHUB_TOKEN", "FINNHUB_API_TOKEN")


@dataclass(frozen=True)
class FinnhubConfig:
    api_key: str
    base_url: str | None = None
    test_url: str | None = None


def resolve_finnhub_api_key(
    config: FinnhubConfig | Mapping[str, Any] | None = None,
    *,
    api_key: str | None = None,
) -> str:
    candidate = api_key or ""
    if isinstance(config, FinnhubConfig):
        candidate = candidate or config.api_key
    elif isinstance(config, Mapping):
        candidate = candidate or str(config.get("api_key") or "")
    if candidate.strip():
        return candidate.strip()

    for env_key in _FINNHUB_ENV_KEYS:
        env_value = os.getenv(env_key, "").strip()
        if env_value:
            return env_value
    raise ValueError("Finnhub api_key is required")


def _resolve_base_url(config: FinnhubConfig | Mapping[str, Any] | None, base_url: str | None) -> str:
    if isinstance(config, FinnhubConfig):
        return config.test_url or config.base_url or base_url or _DEFAULT_REST_BASE_URL
    if isinstance(config, Mapping):
        return str(config.get("test_url") or config.get("base_url") or base_url or _DEFAULT_REST_BASE_URL)
    return base_url or _DEFAULT_REST_BASE_URL


def _resolve_websocket_url(config: FinnhubConfig | Mapping[str, Any] | None) -> str:
    if isinstance(config, FinnhubConfig):
        candidate = config.test_url or _DEFAULT_WEBSOCKET_URL
    elif isinstance(config, Mapping):
        candidate = str(config.get("test_url") or _DEFAULT_WEBSOCKET_URL)
    else:
        candidate = _DEFAULT_WEBSOCKET_URL
    if candidate.startswith("http://"):
        return candidate.replace("http://", "ws://", 1)
    if candidate.startswith("https://"):
        return candidate.replace("https://", "wss://", 1)
    return candidate


def _parse_datetime_value(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc)
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    raise ValueError("expected datetime-compatible value")


def _split_related_symbols(payload: Mapping[str, Any]) -> list[str]:
    symbols = payload.get("symbols")
    if isinstance(symbols, str):
        return [symbol.strip() for symbol in symbols.split(",") if symbol.strip()]
    if isinstance(symbols, Sequence):
        return [str(symbol).strip() for symbol in symbols if str(symbol).strip()]

    related = payload.get("related")
    if isinstance(related, str):
        return [symbol.strip() for symbol in related.split(",") if symbol.strip()]
    return []


def _parse_earnings_date(payload: Mapping[str, Any]) -> datetime:
    date_value = payload.get("date") or payload.get("event_date")
    if date_value is None:
        raise ValueError("earnings payload must include date/event_date")
    return _parse_datetime_value(date_value)


class FinnhubAdapter(NewsProvider, EventProvider):
    provider_name = "finnhub"
    provider_capability = ProviderCapability.NEWS

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        config: FinnhubConfig | Mapping[str, Any] | None = None,
        evidence_store: EvidenceStore | None = None,
        health_manager: ProviderHealthManager | None = None,
    ) -> None:
        if api_key is not None and not api_key.strip():
            raise ValueError("Finnhub api_key is required")
        self.live_config = self._coerce_config(api_key=api_key, base_url=base_url, config=config)
        self.api_key = resolve_finnhub_api_key(self.live_config)
        self.base_url = _resolve_base_url(self.live_config, base_url)
        self.websocket_url = _resolve_websocket_url(self.live_config)
        self.config = dict(config or {}) if isinstance(config, Mapping) else {}
        self.evidence_store = evidence_store
        self.health_manager = health_manager

    @staticmethod
    def _coerce_config(
        *,
        api_key: str | None,
        base_url: str | None,
        config: FinnhubConfig | Mapping[str, Any] | None,
    ) -> FinnhubConfig | Mapping[str, Any]:
        if isinstance(config, FinnhubConfig):
            return config
        if isinstance(config, Mapping):
            return FinnhubConfig(
                api_key=str(config.get("api_key") or api_key or ""),
                base_url=str(config.get("base_url") or base_url) if (config.get("base_url") or base_url) else None,
                test_url=str(config.get("test_url")) if config.get("test_url") else None,
            )
        return FinnhubConfig(api_key=str(api_key or ""), base_url=base_url)

    @staticmethod
    def map_news_payload_to_news_item(payload: Mapping[str, Any], provider_name: str = "finnhub") -> NewsItem:
        published_at = payload.get("datetime") or payload.get("published_at")
        if published_at is None:
            raise ValueError("news payload must include datetime/published_at")
        published_at_dt = _parse_datetime_value(published_at)

        meta = ProviderMeta(
            provider_name=provider_name,
            provider_version=payload.get("provider_version"),
            source_id=str(payload.get("id") or payload.get("urlId") or payload.get("source_id") or ""),
            raw_hash=payload.get("raw_hash"),
            received_at=_parse_datetime_value(payload.get("received_at") or published_at_dt),
            is_delayed=bool(payload.get("is_delayed", False)),
        )
        symbols = _split_related_symbols(payload)
        return NewsItem(
            news_id=str(payload.get("id") or payload.get("urlId") or payload.get("news_id") or payload.get("headline", "")),
            published_at=published_at_dt,
            source_name=str(payload.get("source") or payload.get("source_name") or "finnhub"),
            title=str(payload.get("headline") or payload.get("title") or ""),
            summary=payload.get("summary") or payload.get("description"),
            url=payload.get("url"),
            symbols=symbols,
            language=payload.get("language"),
            author=payload.get("author"),
            sentiment_score=payload.get("sentiment_score"),
            meta=meta,
        )

    @staticmethod
    def map_earnings_payload_to_event(payload: Mapping[str, Any], provider_name: str = "finnhub") -> EarningsEvent:
        event_date = _parse_earnings_date(payload)

        meta = ProviderMeta(
            provider_name=provider_name,
            provider_version=payload.get("provider_version"),
            source_id=str(payload.get("id") or payload.get("source_id") or payload.get("symbol") or ""),
            raw_hash=payload.get("raw_hash"),
            received_at=_parse_datetime_value(payload.get("received_at") or event_date),
            is_delayed=bool(payload.get("is_delayed", False)),
        )
        return EarningsEvent(
            symbol=str(payload.get("symbol") or payload.get("ticker") or ""),
            event_type="earnings",
            event_date=event_date,
            timezone=payload.get("timezone"),
            fiscal_year=payload.get("fiscal_year") or payload.get("year"),
            fiscal_quarter=payload.get("fiscal_quarter") or payload.get("quarter"),
            event_time=payload.get("hour") or payload.get("time"),
            eps_estimate=payload.get("eps_estimate"),
            eps_actual=payload.get("eps_actual"),
            revenue_estimate=payload.get("revenue_estimate"),
            revenue_actual=payload.get("revenue_actual"),
            guidance_text=payload.get("guidance_text"),
            status=payload.get("status"),
            meta=meta,
        )

    def _record_success(self, capability: ProviderCapability, latency_ms: float) -> None:
        if self.health_manager is None:
            return
        self.health_manager.record_success(
            self.provider_name,
            capability,
            latency_ms=latency_ms,
            now=datetime.now(timezone.utc),
        )

    def _record_failure(self, capability: ProviderCapability, error: Exception) -> None:
        if self.health_manager is None:
            return
        error_code = type(error).__name__.upper()
        if isinstance(error, TimeoutError) or isinstance(error, asyncio.TimeoutError):
            error_code = "TIMEOUT"
        self.health_manager.record_failure(
            self.provider_name,
            capability,
            error_code=error_code,
            error_message=str(error),
            now=datetime.now(timezone.utc),
        )

    async def _persist_evidence(self, *, capability: ProviderCapability, payload: Mapping[str, Any], item: NewsItem | EarningsEvent) -> None:
        if self.evidence_store is None:
            return
        fetched_at = item.published_at if isinstance(item, NewsItem) else item.event_date
        symbol = item.symbols[0] if isinstance(item, NewsItem) and item.symbols else item.symbol if isinstance(item, EarningsEvent) else None
        raw_evidence_id = await self.evidence_store.put_raw(
            capability=capability.value,
            provider_name=self.provider_name,
            symbol=symbol,
            fetched_at=fetched_at,
            payload=dict(payload),
            meta=item.meta,
        )
        await self.evidence_store.put_normalized(
            capability=capability.value,
            provider_name=self.provider_name,
            symbol=symbol,
            fetched_at=fetched_at,
            normalized_payload=item.model_dump(mode="json"),
            raw_evidence_id=raw_evidence_id,
        )

    async def fetch_news(
        self,
        symbols: Sequence[str],
        start: datetime,
        end: datetime,
        limit: int = 100,
    ) -> list[NewsItem]:
        raise NotImplementedError("FinnhubAdapter Phase 19 live news is implemented on FinnhubNewsAdapter")

    async def fetch_earnings_events(
        self,
        symbols: Sequence[str],
        start: datetime,
        end: datetime,
    ) -> list[EarningsEvent]:
        raise NotImplementedError("FinnhubAdapter Phase 19 live earnings is implemented on FinnhubEventAdapter")


class FinnhubNewsAdapter(FinnhubAdapter, NewsProvider):
    provider_name = "finnhub_news"
    provider_capability = ProviderCapability.NEWS

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        config: FinnhubConfig | Mapping[str, Any] | None = None,
        evidence_store: EvidenceStore | None = None,
        health_manager: ProviderHealthManager | None = None,
    ) -> None:
        super().__init__(api_key=api_key, base_url=base_url, config=config, evidence_store=evidence_store, health_manager=health_manager)

    async def fetch_news(
        self,
        symbols: Sequence[str],
        start: datetime,
        end: datetime,
        limit: int = 100,
    ) -> list[NewsItem]:
        del start, end
        started_at = time.perf_counter()
        collected: list[NewsItem] = []
        raw_limit = int(self.config.get("news_limit", limit) or limit)
        timeout_seconds = float(self.config.get("news_receive_timeout_seconds", self.config.get("timeout_seconds", 20.0)))
        websocket_uri = f"{self.websocket_url}?token={self.api_key}"

        try:
            async with websockets.connect(websocket_uri) as websocket:
                for symbol in symbols:
                    await websocket.send(json.dumps({"type": "subscribe-news", "symbol": symbol}))

                while len(collected) < raw_limit:
                    try:
                        raw_message = await asyncio.wait_for(websocket.recv(), timeout=timeout_seconds)
                    except asyncio.TimeoutError:
                        break

                    message = json.loads(raw_message)
                    if message.get("type") != "news":
                        continue

                    for raw_item in message.get("data", []):
                        item = self.map_news_payload_to_news_item(raw_item, provider_name=self.provider_name)
                        collected.append(item)
                        await self._persist_evidence(capability=ProviderCapability.NEWS, payload=raw_item, item=item)
                        if len(collected) >= raw_limit:
                            break

            latency_ms = (time.perf_counter() - started_at) * 1000.0
            if collected:
                self._record_success(ProviderCapability.NEWS, latency_ms=latency_ms)
            elif self.health_manager is not None:
                self.health_manager.mark_degraded(
                    self.provider_name,
                    ProviderCapability.NEWS,
                    reason="no live news delivered",
                    now=datetime.now(timezone.utc),
                )
            return collected
        except Exception as error:
            self._record_failure(ProviderCapability.NEWS, error)
            raise


class FinnhubEventAdapter(FinnhubAdapter, EventProvider):
    provider_name = "finnhub_events"
    provider_capability = ProviderCapability.EVENT

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        config: FinnhubConfig | Mapping[str, Any] | None = None,
        evidence_store: EvidenceStore | None = None,
        health_manager: ProviderHealthManager | None = None,
    ) -> None:
        super().__init__(api_key=api_key, base_url=base_url, config=config, evidence_store=evidence_store, health_manager=health_manager)

    async def fetch_earnings_events(
        self,
        symbols: Sequence[str],
        start: datetime,
        end: datetime,
    ) -> list[EarningsEvent]:
        started_at = time.perf_counter()
        params: dict[str, Any] = {
            "from": start.date().isoformat(),
            "to": end.date().isoformat(),
        }
        if symbols:
            params["symbol"] = symbols[0]

        try:
            async with httpx.AsyncClient(
                base_url=self.base_url,
                timeout=float(self.config.get("timeout_seconds", 20.0)),
                headers={"X-Finnhub-Token": self.api_key},
            ) as client:
                response = await client.get("/calendar/earnings", params=params)
                response.raise_for_status()
                payload = response.json()

            earnings_payloads = payload.get("earningsCalendar") or []
            events: list[EarningsEvent] = []
            for raw_item in earnings_payloads:
                event = self.map_earnings_payload_to_event(raw_item, provider_name=self.provider_name)
                events.append(event)
                await self._persist_evidence(capability=ProviderCapability.EVENT, payload=raw_item, item=event)

            latency_ms = (time.perf_counter() - started_at) * 1000.0
            if events:
                self._record_success(ProviderCapability.EVENT, latency_ms=latency_ms)
            elif self.health_manager is not None:
                self.health_manager.mark_degraded(
                    self.provider_name,
                    ProviderCapability.EVENT,
                    reason="no earnings events returned",
                    now=datetime.now(timezone.utc),
                )
            return events
        except Exception as error:
            self._record_failure(ProviderCapability.EVENT, error)
            raise