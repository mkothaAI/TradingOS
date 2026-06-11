from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any, Optional

import asyncio
import json
from datetime import datetime, timedelta, timezone

from trading_os_v1.providers.config import classify_provider_error, normalize_provider_config
from trading_os_v1.providers.base import MarketDataProvider
from trading_os_v1.providers.evidence_provenance import (
    attach_provider_evidence_provenance,
    build_provider_evidence_provenance,
)
from trading_os_v1.providers.schemas import (
    NormalizedProviderEvidenceRecord,
    ProviderCapability,
    PriceBar,
    ProviderMeta,
    QuoteSnapshot,
    RawProviderEvidenceRecord,
)
import httpx
import websockets


@dataclass
class TwelveDataConfig:
    api_key: str
    base_url: str = "https://api.twelvedata.com"
    timeout_seconds: int = 30
    max_retries: int = 2
    retry_delay_seconds: float = 0.05

    def __post_init__(self) -> None:
        normalized = normalize_provider_config(
            explicit={
                "api_key": self.api_key,
                "base_url": self.base_url,
                "timeout_seconds": self.timeout_seconds,
                "max_retries": self.max_retries,
                "retry_delay_seconds": self.retry_delay_seconds,
            },
            env_map={
                "api_key": ("TWELVEDATA_API_KEY", "TWELVE_DATA_API_KEY"),
                "base_url": "TWELVEDATA_BASE_URL",
            },
            defaults={
                "base_url": "https://api.twelvedata.com",
                "timeout_seconds": 30,
                "max_retries": 2,
                "retry_delay_seconds": 0.05,
            },
            required=("api_key",),
        )
        self.api_key = str(normalized["api_key"])
        self.base_url = str(normalized["base_url"])
        self.timeout_seconds = int(normalized["timeout_seconds"])
        self.max_retries = int(normalized["max_retries"])
        self.retry_delay_seconds = float(normalized["retry_delay_seconds"])


@dataclass
class TwelveDataRealtimeConfig:
    api_key: str
    websocket_url: str = "wss://ws.twelvedata.com/v1/quotes/price?apikey=<KEY>"
    timeout_seconds: int = 30
    heartbeat_seconds: int = 15
    reconnect_initial_backoff_seconds: float = 0.25
    reconnect_max_backoff_seconds: float = 4.0
    reconnect_max_attempts: Optional[int] = None

    def __post_init__(self) -> None:
        normalized = normalize_provider_config(
            explicit={
                "api_key": self.api_key,
                "websocket_url": self.websocket_url,
                "timeout_seconds": self.timeout_seconds,
                "heartbeat_seconds": self.heartbeat_seconds,
                "reconnect_initial_backoff_seconds": self.reconnect_initial_backoff_seconds,
                "reconnect_max_backoff_seconds": self.reconnect_max_backoff_seconds,
                "reconnect_max_attempts": self.reconnect_max_attempts,
            },
            env_map={
                "api_key": ("TWELVEDATA_API_KEY", "TWELVE_DATA_API_KEY"),
                "websocket_url": "TWELVEDATA_WEBSOCKET_URL",
            },
            defaults={
                "websocket_url": "wss://ws.twelvedata.com/v1/quotes/price?apikey=<KEY>",
                "timeout_seconds": 30,
                "heartbeat_seconds": 15,
                "reconnect_initial_backoff_seconds": 0.25,
                "reconnect_max_backoff_seconds": 4.0,
            },
            required=("api_key",),
        )
        self.api_key = str(normalized["api_key"])
        self.websocket_url = str(normalized["websocket_url"])
        self.timeout_seconds = int(normalized["timeout_seconds"])
        self.heartbeat_seconds = int(normalized["heartbeat_seconds"])
        self.reconnect_initial_backoff_seconds = float(normalized["reconnect_initial_backoff_seconds"])
        self.reconnect_max_backoff_seconds = float(normalized["reconnect_max_backoff_seconds"])
        self.reconnect_max_attempts = normalized.get("reconnect_max_attempts")


@dataclass(frozen=True)
class QuoteWatchFrame:
    symbol: str
    feed_status: str
    quote: QuoteSnapshot | None = None
    last_successful_update_at: datetime | None = None
    last_error: str | None = None
    reconnect_attempts: int = 0
    reconnect_backoff_seconds: float | None = None


class TwelveDataIntradayAdapter:
    """Minimal Twelve Data adapter skeleton.

    This file provides only the minimal surface area so tests can import
    and discover expected symbols. Implementation is intentionally
    absent and will raise NotImplementedError where behavior is required.
    """

    provider_name = "twelvedata"
    provider_capability = ProviderCapability.MARKET_DATA

    def __init__(self, config: TwelveDataConfig, evidence_store: Optional[Any] = None, health_manager: Optional[Any] = None, http_client: Optional[Any] = None):
        self.config = config
        self.evidence_store = evidence_store
        self.health_manager = health_manager
        self.http_client = http_client

    async def _maybe_await(self, result):
        if asyncio.iscoroutine(result):
            return await result
        return result

    def _parse_dt(self, value: str) -> datetime:
        if value is None:
            raise ValueError("missing datetime")
        # Twelve Data often returns 'YYYY-MM-DD HH:MM:SS' without timezone
        return datetime.fromisoformat(value)

    async def fetch_price_bars(self, symbol: str, start: str, end: str, timeframe: str = "1min"):
        max_retries = int(getattr(self.config, "max_retries", 2) or 2)
        retry_delay = float(getattr(self.config, "retry_delay_seconds", 0.05) or 0.05)
        attempt = 0
        url = f"{self.config.base_url.rstrip('/')}/time_series"
        params = {"symbol": symbol, "interval": timeframe, "start_date": start, "end_date": end, "format": "JSON", "apikey": self.config.api_key}

        for attempt in range(1, max_retries + 1):
            try:
                if self.http_client is not None:
                    resp = await self.http_client.get(url, params=params)
                else:
                    async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
                        resp = await client.get(url, params=params)

                status = getattr(resp, "status_code", None)
                json_coro = resp.json()
                payload = await json_coro if asyncio.iscoroutine(json_coro) else json_coro

                # persist raw evidence once per fetch
                fetched_at = datetime.now(timezone.utc)
                meta = ProviderMeta(provider_name=self.provider_name, provider_version=None, source_id=symbol, raw_hash=None, received_at=fetched_at, is_delayed=False)
                raw_id = None
                if self.evidence_store is not None:
                    try:
                        raw_result = self.evidence_store.put_raw(capability=self.provider_capability.value, provider_name=self.provider_name, symbol=symbol, fetched_at=fetched_at, payload=payload, meta=meta)
                        raw_id = await self._maybe_await(raw_result)
                    except Exception:
                        raw_id = None

                raw_record = None
                if raw_id is not None:
                    raw_record = RawProviderEvidenceRecord(
                        evidence_id=raw_id,
                        provider_name=self.provider_name,
                        capability=self.provider_capability,
                        symbol=symbol,
                        source_id=symbol,
                        fetched_at=fetched_at,
                        payload=payload if isinstance(payload, dict) else {"payload": payload},
                        meta=meta,
                    )

                classification = classify_provider_error(http_status=status, payload=payload)

                # auth errors
                if classification.disposition == "terminal_auth":
                    if self.health_manager is not None:
                        try:
                            self.health_manager.record_failure(self.provider_name, self.provider_capability, error_code=classification.error_code, error_message=str(payload))
                        except Exception:
                            pass
                    raise Exception("authentication failed")

                if classification.retryable and status is not None:
                    if self.health_manager is not None:
                        try:
                            if hasattr(self.health_manager, "record_degraded"):
                                self.health_manager.record_degraded(self.provider_name, self.provider_capability, reason=classification.error_code.lower())
                            elif hasattr(self.health_manager, "mark_degraded"):
                                self.health_manager.mark_degraded(self.provider_name, self.provider_capability, reason=classification.error_code.lower())
                        except Exception:
                            pass
                    await asyncio.sleep(retry_delay)
                    continue

                values = None
                if isinstance(payload, dict) and "values" in payload:
                    values = payload.get("values")
                elif isinstance(payload, list):
                    values = payload
                else:
                    values = []

                bars = []
                degraded_flag = False
                for row in (values or []):
                    try:
                        dt = self._parse_dt(row.get("datetime")) if isinstance(row, dict) else None
                        if dt is None:
                            raise ValueError("missing datetime in row")
                        start_at = dt
                        # naive mapping: assume timeframe like '1min' -> 1 minute
                        end_at = start_at + timedelta(minutes=1 if timeframe.endswith("min") else 0)
                        pb = PriceBar(
                            symbol=symbol,
                            timeframe=timeframe,
                            start_at=start_at,
                            end_at=end_at,
                            open=float(row.get("open")),
                            high=float(row.get("high")),
                            low=float(row.get("low")),
                            close=float(row.get("close")),
                            volume=float(row.get("volume")) if row.get("volume") is not None else None,
                            meta=meta,
                        )

                        returned = SimpleNamespace(**pb.model_dump(mode="python"))
                        try:
                            setattr(returned, "provider", self.provider_name)
                        except Exception:
                            pass
                        normalized_payload = pb.model_dump(mode="json")
                        normalized_id = None
                        if self.evidence_store is not None:
                            try:
                                if raw_id is not None:
                                    normalized_result = self.evidence_store.put_normalized(
                                        capability=self.provider_capability.value,
                                        provider_name=self.provider_name,
                                        symbol=symbol,
                                        fetched_at=fetched_at,
                                        normalized_payload=normalized_payload,
                                        raw_evidence_id=raw_id,
                                    )
                                    candidate_normalized_id = await self._maybe_await(normalized_result)
                                    if isinstance(candidate_normalized_id, str) and candidate_normalized_id:
                                        normalized_id = candidate_normalized_id
                            except Exception:
                                pass

                        if raw_record is not None:
                            normalized_record = None
                            if normalized_id is not None:
                                normalized_record = NormalizedProviderEvidenceRecord(
                                    evidence_id=normalized_id,
                                    provider_name=self.provider_name,
                                    capability=self.provider_capability,
                                    symbol=symbol,
                                    source_id=symbol,
                                    fetched_at=fetched_at,
                                    normalized_payload=normalized_payload,
                                    raw_evidence_id=raw_id,
                                )
                            provenance = build_provider_evidence_provenance(raw_record, normalized_record)
                            attach_provider_evidence_provenance(returned, provenance)
                            setattr(returned, "evidence_id", raw_id)
                        bars.append(returned)
                    except Exception as e:
                        degraded_flag = True
                        if self.health_manager is not None:
                            try:
                                if hasattr(self.health_manager, "record_degraded"):
                                    self.health_manager.record_degraded(self.provider_name, self.provider_capability, reason=str(e))
                                elif hasattr(self.health_manager, "mark_degraded"):
                                    self.health_manager.mark_degraded(self.provider_name, self.provider_capability, reason=str(e))
                            except Exception:
                                pass
                        continue

                if self.health_manager is not None:
                    try:
                        self.health_manager.record_success(self.provider_name, self.provider_capability, latency_ms=1.0, quota_remaining=None)
                    except Exception:
                        pass

                return bars

            except Exception as error:
                if "authentication failed" in str(error).lower():
                    raise
                if attempt == max_retries:
                    # attempt to persist error raw
                    try:
                        if self.evidence_store is not None:
                            await self._maybe_await(self.evidence_store.put_raw(capability=self.provider_capability.value, provider_name=self.provider_name, symbol=symbol, fetched_at=datetime.now(timezone.utc), payload={"error": str(error)}, meta=ProviderMeta(provider_name=self.provider_name, received_at=datetime.now(timezone.utc))))
                    except Exception:
                        pass
                    if self.health_manager is not None:
                        try:
                            classified_error = classify_provider_error(error=error, message=str(error))
                            self.health_manager.record_failure(
                                self.provider_name,
                                self.provider_capability,
                                error_code=classified_error.error_code,
                                error_message=str(error),
                            )
                        except Exception:
                            pass
                    raise
                # else retry

        # exhausted
        if self.health_manager is not None:
            try:
                self.health_manager.record_failure(self.provider_name, self.provider_capability, error_code="RetryExhausted", error_message="exhausted retries")
            except Exception:
                pass
        raise Exception("unhandled twelvedata fetch error")

    async def get_bars(self, symbol: str, start: str, end: str, timeframe: str = "1min"):
        # Alias used by tests — intentionally unimplemented placeholder
        return await self.fetch_price_bars(symbol=symbol, start=start, end=end, timeframe=timeframe)

    async def get_provider_meta(self):
        return SimpleNamespace(provider=self.provider_name, base_url=self.config.base_url)

    async def close(self):
        return None


class TwelveDataMarketDataProvider(MarketDataProvider):
    """Market-data protocol wrapper around the external Twelve Data intraday adapter."""

    provider_name = "twelvedata"
    provider_capability = ProviderCapability.MARKET_DATA

    def __init__(
        self,
        config: TwelveDataConfig,
        evidence_store: Optional[Any] = None,
        health_manager: Optional[Any] = None,
        http_client: Optional[Any] = None,
    ) -> None:
        self._adapter = TwelveDataIntradayAdapter(
            config=config,
            evidence_store=evidence_store,
            health_manager=health_manager,
            http_client=http_client,
        )

    def _coerce_price_bar(self, bar: Any) -> PriceBar:
        payload = bar.model_dump(mode="python") if hasattr(bar, "model_dump") else dict(vars(bar))
        meta = payload.get("meta")
        if not isinstance(meta, ProviderMeta):
            meta = ProviderMeta(**meta) if isinstance(meta, dict) else ProviderMeta(provider_name=self.provider_name, received_at=datetime.now(timezone.utc))
        return PriceBar(
            symbol=str(payload.get("symbol") or ""),
            timeframe=str(payload.get("timeframe") or "1min"),
            start_at=payload.get("start_at"),
            end_at=payload.get("end_at"),
            open=float(payload.get("open")),
            high=float(payload.get("high")),
            low=float(payload.get("low")),
            close=float(payload.get("close")),
            volume=payload.get("volume"),
            vwap=payload.get("vwap"),
            adjusted=bool(payload.get("adjusted", False)),
            split_factor=payload.get("split_factor"),
            dividend_factor=payload.get("dividend_factor"),
            meta=meta,
        )

    async def get_bars(self, symbol: str, start: datetime, end: datetime, timeframe: str) -> list[PriceBar]:
        bars = await self._adapter.get_bars(
            symbol,
            start=start.date().isoformat(),
            end=end.date().isoformat(),
            timeframe=timeframe,
        )
        return [self._coerce_price_bar(bar) for bar in bars]

    async def get_quote(self, symbol: str, as_of: datetime | None = None) -> QuoteSnapshot:
        end = as_of or datetime.now(timezone.utc)
        start = end - timedelta(days=1)
        bars = await self.get_bars(symbol, start=start, end=end, timeframe="1min")
        if not bars:
            raise ValueError(f"no market bars available for {symbol}")
        last_bar = bars[-1]
        quote_meta = ProviderMeta(provider_name=self.provider_name, source_id=symbol, received_at=end)
        return QuoteSnapshot(
            symbol=symbol,
            as_of=end,
            last=last_bar.close,
            mid=last_bar.close,
            currency=None,
            exchange=None,
            meta=quote_meta,
        )


class TwelveDataRealtimeAdapter:
    provider_name = "twelvedata_realtime"
    provider_capability = ProviderCapability.REALTIME_STREAM

    def __init__(
        self,
        config: TwelveDataRealtimeConfig,
        evidence_store: Optional[Any] = None,
        health_manager: Optional[Any] = None,
        websocket_client_factory: Optional[Any] = None,
    ) -> None:
        self.config = config
        self.evidence_store = evidence_store
        self.health_manager = health_manager
        self.websocket_client_factory = websocket_client_factory
        self._active_symbols: set[str] = set()
        self._closed = False
        self._socket: Any | None = None

    def _resolve_websocket_url(self) -> str:
        websocket_url = str(getattr(self.config, "websocket_url", "wss://ws.twelvedata.com/v1/quotes/price?apikey=<KEY>"))
        api_key = str(getattr(self.config, "api_key", "") or "")
        return websocket_url.replace("<KEY>", api_key) if api_key else websocket_url

    async def _maybe_await(self, result):
        if asyncio.iscoroutine(result):
            return await result
        return result

    async def _persist_raw_message(self, message: dict[str, Any], symbol: str | None = None) -> str | None:
        if self.evidence_store is None:
            return None
        fetched_at = datetime.now(timezone.utc)
        meta = ProviderMeta(provider_name=self.provider_name, provider_version=None, source_id=symbol, raw_hash=None, received_at=fetched_at, is_delayed=False)
        raw_result = self.evidence_store.put_raw(
            capability=self.provider_capability.value,
            provider_name=self.provider_name,
            symbol=symbol,
            fetched_at=fetched_at,
            payload=message,
            meta=meta,
        )
        return await self._maybe_await(raw_result)

    async def _persist_quote(self, quote: QuoteSnapshot | Any, raw_evidence_id: str | None) -> str | None:
        if self.evidence_store is None:
            return None
        fetched_at = getattr(getattr(quote, "meta", None), "received_at", datetime.now(timezone.utc))
        normalized_payload = quote.model_dump(mode="json") if hasattr(quote, "model_dump") else dict(quote)
        if raw_evidence_id is None:
            return None
        normalized_result = self.evidence_store.put_normalized(
            capability=self.provider_capability.value,
            provider_name=self.provider_name,
            symbol=getattr(quote, "symbol", None),
            fetched_at=fetched_at,
            normalized_payload=normalized_payload,
            raw_evidence_id=raw_evidence_id,
        )
        return await self._maybe_await(normalized_result)

    def _parse_price_message(self, message: dict[str, Any]) -> QuoteSnapshot:
        symbol = str(message.get("symbol") or "")
        price_value = message.get("price")
        if price_value is None:
            raise ValueError("missing price")
        timestamp_value = message.get("timestamp") or message.get("datetime") or message.get("time")
        if isinstance(timestamp_value, str):
            timestamp_value = timestamp_value.replace("Z", "+00:00")
            as_of = datetime.fromisoformat(timestamp_value)
        elif isinstance(timestamp_value, (int, float)):
            as_of = datetime.fromtimestamp(timestamp_value, tz=timezone.utc)
        else:
            as_of = datetime.now(timezone.utc)

        meta = ProviderMeta(
            provider_name=self.provider_name,
            provider_version=None,
            source_id=symbol or None,
            raw_hash=None,
            received_at=datetime.now(timezone.utc),
            is_delayed=bool(message.get("is_delayed", False)),
        )
        return QuoteSnapshot(
            symbol=symbol,
            as_of=as_of,
            last=float(price_value),
            currency=message.get("currency"),
            exchange=message.get("exchange"),
            meta=meta,
        )

    def _is_terminal_auth_message(self, message: dict[str, Any]) -> bool:
        classification = classify_provider_error(
            http_status=int(message.get("code")) if str(message.get("code") or "").isdigit() else None,
            payload=message,
            message=str(message.get("message") or message.get("error") or ""),
        )
        return classification.disposition == "terminal_auth"

    async def _send_control(self, websocket: Any, action: str, symbols) -> None:
        if websocket is None:
            return
        joined_symbols = ",".join(sorted([str(symbol) for symbol in symbols if str(symbol)]))
        payload = {"action": action, "params": {"symbols": joined_symbols}}
        send_result = websocket.send(json.dumps(payload))
        await self._maybe_await(send_result)

    async def subscribe(self, symbols):
        self._active_symbols.update(symbols)
        if self._socket is not None:
            await self._send_control(self._socket, "subscribe", symbols)
        return None

    async def unsubscribe(self, symbols):
        for symbol in symbols:
            self._active_symbols.discard(symbol)
        if self._socket is not None:
            await self._send_control(self._socket, "unsubscribe", symbols)
        return None

    async def reset(self):
        self._active_symbols.clear()
        if self._socket is not None:
            await self._send_control(self._socket, "reset", [])
        return None

    async def stream_quotes(self, symbols):
        self._active_symbols.update(symbols)
        websocket_url = self._resolve_websocket_url()
        websocket_factory = self.websocket_client_factory or websockets.connect
        backoff_seconds = float(getattr(self.config, "reconnect_initial_backoff_seconds", 0.25) or 0.25)
        max_backoff_seconds = float(getattr(self.config, "reconnect_max_backoff_seconds", 4.0) or 4.0)
        max_attempts = getattr(self.config, "reconnect_max_attempts", None)
        if max_attempts is None:
            max_attempts = 3
        reconnect_attempts = 0

        while not self._closed:
            try:
                connection = websocket_factory(websocket_url)
                websocket = await connection if asyncio.iscoroutine(connection) else connection
                self._socket = websocket
                entered = False
                try:
                    await websocket.__aenter__()
                except Exception as error:
                    reconnect_attempts += 1
                    if max_attempts is not None and reconnect_attempts > int(max_attempts):
                        if self.health_manager is not None and hasattr(self.health_manager, "record_failure"):
                            self.health_manager.record_failure(
                                self.provider_name,
                                self.provider_capability,
                                error_code=type(error).__name__.upper(),
                                error_message=str(error),
                                now=datetime.now(timezone.utc),
                            )
                        raise
                    if self.health_manager is not None and hasattr(self.health_manager, "record_degraded"):
                        self.health_manager.record_degraded(self.provider_name, self.provider_capability, reason=str(error))
                    await asyncio.sleep(min(backoff_seconds, max_backoff_seconds))
                    backoff_seconds = min(backoff_seconds * 2.0, max_backoff_seconds)
                    continue
                entered = True
                await self._send_control(websocket, "subscribe", self._active_symbols)
                while not self._closed:
                    try:
                        raw_message = await asyncio.wait_for(websocket.recv(), timeout=float(getattr(self.config, "timeout_seconds", 30) or 30))
                    except asyncio.TimeoutError as error:
                        if self.health_manager is not None and hasattr(self.health_manager, "record_degraded"):
                            self.health_manager.record_degraded(self.provider_name, self.provider_capability, reason="timeout")
                        raise error

                    if isinstance(raw_message, bytes):
                        raw_message = raw_message.decode("utf-8")

                    try:
                        message = json.loads(raw_message)
                    except Exception as error:
                        if self.health_manager is not None and hasattr(self.health_manager, "record_degraded"):
                            self.health_manager.record_degraded(self.provider_name, self.provider_capability, reason=str(error))
                        await self._persist_raw_message({"error": "malformed_json", "raw": raw_message})
                        continue

                    message_type = str(message.get("type") or message.get("event") or "").lower()
                    if message_type in {"subscribe", "subscribe-status", "heartbeat"}:
                        await self._persist_raw_message(message)
                        continue

                    if self._is_terminal_auth_message(message):
                        await self._persist_raw_message(message)
                        if self.health_manager is not None and hasattr(self.health_manager, "record_failure"):
                            self.health_manager.record_failure(
                                self.provider_name,
                                self.provider_capability,
                                error_code="AUTH",
                                error_message=str(message.get("message") or message.get("error") or "websocket auth failure"),
                                now=datetime.now(timezone.utc),
                            )
                        raise Exception("twelvedata websocket authentication failed")

                    if message_type == "price" or message.get("price") is not None:
                        raw_evidence_id = await self._persist_raw_message(message, symbol=str(message.get("symbol") or next(iter(self._active_symbols), None)))
                        try:
                            quote = self._parse_price_message(message)
                        except Exception as error:
                            if self.health_manager is not None and hasattr(self.health_manager, "record_degraded"):
                                self.health_manager.record_degraded(self.provider_name, self.provider_capability, reason=str(error))
                            continue

                        normalized_id = await self._persist_quote(quote, raw_evidence_id)
                        if not isinstance(normalized_id, str) or not normalized_id:
                            normalized_id = None
                        if raw_evidence_id is not None:
                            raw_record = RawProviderEvidenceRecord(
                                evidence_id=raw_evidence_id,
                                provider_name=self.provider_name,
                                capability=self.provider_capability,
                                symbol=getattr(quote, "symbol", None),
                                source_id=getattr(quote, "symbol", None),
                                fetched_at=getattr(quote.meta, "received_at", datetime.now(timezone.utc)),
                                payload=message,
                                meta=quote.meta,
                            )
                            normalized_record = None
                            if normalized_id is not None:
                                normalized_record = NormalizedProviderEvidenceRecord(
                                    evidence_id=normalized_id,
                                    provider_name=self.provider_name,
                                    capability=self.provider_capability,
                                    symbol=getattr(quote, "symbol", None),
                                    source_id=getattr(quote, "symbol", None),
                                    fetched_at=getattr(quote.meta, "received_at", datetime.now(timezone.utc)),
                                    normalized_payload=quote.model_dump(mode="json"),
                                    raw_evidence_id=raw_evidence_id,
                                )
                            provenance = build_provider_evidence_provenance(raw_record, normalized_record)
                            attach_provider_evidence_provenance(quote, provenance)
                            object.__setattr__(quote, "evidence_id", raw_evidence_id)
                        if self.health_manager is not None and hasattr(self.health_manager, "record_success"):
                            self.health_manager.record_success(self.provider_name, self.provider_capability, latency_ms=1.0, quota_remaining=None, now=datetime.now(timezone.utc))
                        reconnect_attempts = 0
                        backoff_seconds = float(getattr(self.config, "reconnect_initial_backoff_seconds", 0.25) or 0.25)
                        yield quote
                        continue

                    await self._persist_raw_message(message)
                    if self.health_manager is not None and hasattr(self.health_manager, "record_degraded"):
                        self.health_manager.record_degraded(self.provider_name, self.provider_capability, reason="unsupported_message")
            except asyncio.TimeoutError as error:
                if self._closed:
                    break
                reconnect_attempts += 1
                if max_attempts is not None and reconnect_attempts > int(max_attempts):
                    if self.health_manager is not None and hasattr(self.health_manager, "record_failure"):
                        self.health_manager.record_failure(
                            self.provider_name,
                            self.provider_capability,
                            error_code="TIMEOUT",
                            error_message=str(error),
                            now=datetime.now(timezone.utc),
                        )
                    raise
                if self.health_manager is not None and hasattr(self.health_manager, "record_degraded"):
                    self.health_manager.record_degraded(self.provider_name, self.provider_capability, reason="timeout")
                await asyncio.sleep(min(backoff_seconds, max_backoff_seconds))
                backoff_seconds = min(backoff_seconds * 2.0, max_backoff_seconds)
                continue
            except Exception as error:
                if self._is_terminal_auth_message({"message": str(error), "error": str(error), "code": "401"}):
                    raise
                if self._closed:
                    break
                reconnect_attempts += 1
                if max_attempts is not None and reconnect_attempts > int(max_attempts):
                    if self.health_manager is not None and hasattr(self.health_manager, "record_failure"):
                        self.health_manager.record_failure(
                            self.provider_name,
                            self.provider_capability,
                            error_code=type(error).__name__.upper(),
                            error_message=str(error),
                            now=datetime.now(timezone.utc),
                        )
                    raise
                if self.health_manager is not None and hasattr(self.health_manager, "record_degraded"):
                    self.health_manager.record_degraded(self.provider_name, self.provider_capability, reason=str(error))
                await asyncio.sleep(min(backoff_seconds, max_backoff_seconds))
                backoff_seconds = min(backoff_seconds * 2.0, max_backoff_seconds)
                continue
            finally:
                if 'entered' in locals() and entered and hasattr(websocket, "__aexit__"):
                    await websocket.__aexit__(None, None, None)
                self._socket = None

    async def stream_quote_watch(self, symbols):
        active_symbols = list(symbols) or list(self._active_symbols) or [""]
        primary_symbol = str(active_symbols[0] or "")
        self._active_symbols.update(active_symbols)
        websocket_url = self._resolve_websocket_url()
        websocket_factory = self.websocket_client_factory or websockets.connect
        backoff_seconds = float(getattr(self.config, "reconnect_initial_backoff_seconds", 0.25) or 0.25)
        max_backoff_seconds = float(getattr(self.config, "reconnect_max_backoff_seconds", 4.0) or 4.0)
        max_attempts = getattr(self.config, "reconnect_max_attempts", None)
        if max_attempts is None:
            max_attempts = 3
        reconnect_attempts = 0
        last_successful_update_at: datetime | None = None

        while not self._closed:
            try:
                connection = websocket_factory(websocket_url)
                websocket = await connection if asyncio.iscoroutine(connection) else connection
                self._socket = websocket
                entered = False
                try:
                    await websocket.__aenter__()
                except Exception as error:
                    reconnect_attempts += 1
                    if reconnect_attempts > int(max_attempts):
                        if self.health_manager is not None and hasattr(self.health_manager, "record_failure"):
                            self.health_manager.record_failure(
                                self.provider_name,
                                self.provider_capability,
                                error_code=type(error).__name__.upper(),
                                error_message=str(error),
                                now=datetime.now(timezone.utc),
                            )
                        yield QuoteWatchFrame(
                            symbol=primary_symbol,
                            feed_status="disconnected",
                            quote=None,
                            last_successful_update_at=last_successful_update_at,
                            last_error=str(error),
                            reconnect_attempts=reconnect_attempts,
                            reconnect_backoff_seconds=None,
                        )
                        break
                    if self.health_manager is not None and hasattr(self.health_manager, "record_degraded"):
                        self.health_manager.record_degraded(self.provider_name, self.provider_capability, reason=str(error))
                    yield QuoteWatchFrame(
                        symbol=primary_symbol,
                        feed_status="reconnecting",
                        quote=None,
                        last_successful_update_at=last_successful_update_at,
                        last_error=str(error),
                        reconnect_attempts=reconnect_attempts,
                        reconnect_backoff_seconds=backoff_seconds,
                    )
                    await asyncio.sleep(min(backoff_seconds, max_backoff_seconds))
                    backoff_seconds = min(backoff_seconds * 2.0, max_backoff_seconds)
                    continue
                entered = True
                await self._send_control(websocket, "subscribe", self._active_symbols)
                while not self._closed:
                    try:
                        raw_message = await asyncio.wait_for(websocket.recv(), timeout=float(getattr(self.config, "timeout_seconds", 30) or 30))
                    except asyncio.TimeoutError as error:
                        reconnect_attempts += 1
                        if reconnect_attempts > int(max_attempts):
                            if self.health_manager is not None and hasattr(self.health_manager, "record_failure"):
                                self.health_manager.record_failure(
                                    self.provider_name,
                                    self.provider_capability,
                                    error_code="TIMEOUT",
                                    error_message=str(error),
                                    now=datetime.now(timezone.utc),
                                )
                            yield QuoteWatchFrame(
                                symbol=primary_symbol,
                                feed_status="disconnected",
                                quote=None,
                                last_successful_update_at=last_successful_update_at,
                                last_error=str(error),
                                reconnect_attempts=reconnect_attempts,
                                reconnect_backoff_seconds=None,
                            )
                            return
                        if self.health_manager is not None and hasattr(self.health_manager, "record_degraded"):
                            self.health_manager.record_degraded(self.provider_name, self.provider_capability, reason="timeout")
                        yield QuoteWatchFrame(
                            symbol=primary_symbol,
                            feed_status="reconnecting",
                            quote=None,
                            last_successful_update_at=last_successful_update_at,
                            last_error=str(error),
                            reconnect_attempts=reconnect_attempts,
                            reconnect_backoff_seconds=backoff_seconds,
                        )
                        await asyncio.sleep(min(backoff_seconds, max_backoff_seconds))
                        backoff_seconds = min(backoff_seconds * 2.0, max_backoff_seconds)
                        break

                    if isinstance(raw_message, bytes):
                        raw_message = raw_message.decode("utf-8")

                    try:
                        message = json.loads(raw_message)
                    except Exception as error:
                        if self.health_manager is not None and hasattr(self.health_manager, "record_degraded"):
                            self.health_manager.record_degraded(self.provider_name, self.provider_capability, reason=str(error))
                        await self._persist_raw_message({"error": "malformed_json", "raw": raw_message})
                        yield QuoteWatchFrame(
                            symbol=primary_symbol,
                            feed_status="stale",
                            quote=None,
                            last_successful_update_at=last_successful_update_at,
                            last_error=str(error),
                            reconnect_attempts=reconnect_attempts,
                            reconnect_backoff_seconds=backoff_seconds,
                        )
                        continue

                    message_type = str(message.get("type") or message.get("event") or "").lower()
                    if message_type in {"subscribe", "subscribe-status", "heartbeat"}:
                        await self._persist_raw_message(message)
                        continue

                    if self._is_terminal_auth_message(message):
                        await self._persist_raw_message(message)
                        if self.health_manager is not None and hasattr(self.health_manager, "record_failure"):
                            self.health_manager.record_failure(
                                self.provider_name,
                                self.provider_capability,
                                error_code="AUTH",
                                error_message=str(message.get("message") or message.get("error") or "websocket auth failure"),
                                now=datetime.now(timezone.utc),
                            )
                        yield QuoteWatchFrame(
                            symbol=primary_symbol,
                            feed_status="disconnected",
                            quote=None,
                            last_successful_update_at=last_successful_update_at,
                            last_error=str(message.get("message") or message.get("error") or "websocket auth failure"),
                            reconnect_attempts=reconnect_attempts,
                            reconnect_backoff_seconds=None,
                        )
                        raise Exception("twelvedata websocket authentication failed")

                    if message_type == "price" or message.get("price") is not None:
                        raw_evidence_id = await self._persist_raw_message(message, symbol=str(message.get("symbol") or next(iter(self._active_symbols), None)))
                        try:
                            quote = self._parse_price_message(message)
                        except Exception as error:
                            if self.health_manager is not None and hasattr(self.health_manager, "record_degraded"):
                                self.health_manager.record_degraded(self.provider_name, self.provider_capability, reason=str(error))
                            yield QuoteWatchFrame(
                                symbol=primary_symbol,
                                feed_status="stale",
                                quote=None,
                                last_successful_update_at=last_successful_update_at,
                                last_error=str(error),
                                reconnect_attempts=reconnect_attempts,
                                reconnect_backoff_seconds=backoff_seconds,
                            )
                            continue

                        normalized_id = await self._persist_quote(quote, raw_evidence_id)
                        if not isinstance(normalized_id, str) or not normalized_id:
                            normalized_id = None
                        if raw_evidence_id is not None:
                            raw_record = RawProviderEvidenceRecord(
                                evidence_id=raw_evidence_id,
                                provider_name=self.provider_name,
                                capability=self.provider_capability,
                                symbol=getattr(quote, "symbol", None),
                                source_id=getattr(quote, "symbol", None),
                                fetched_at=getattr(quote.meta, "received_at", datetime.now(timezone.utc)),
                                payload=message,
                                meta=quote.meta,
                            )
                            normalized_record = None
                            if normalized_id is not None:
                                normalized_record = NormalizedProviderEvidenceRecord(
                                    evidence_id=normalized_id,
                                    provider_name=self.provider_name,
                                    capability=self.provider_capability,
                                    symbol=getattr(quote, "symbol", None),
                                    source_id=getattr(quote, "symbol", None),
                                    fetched_at=getattr(quote.meta, "received_at", datetime.now(timezone.utc)),
                                    normalized_payload=quote.model_dump(mode="json"),
                                    raw_evidence_id=raw_evidence_id,
                                )
                            provenance = build_provider_evidence_provenance(raw_record, normalized_record)
                            attach_provider_evidence_provenance(quote, provenance)
                            object.__setattr__(quote, "evidence_id", raw_evidence_id)
                        if self.health_manager is not None and hasattr(self.health_manager, "record_success"):
                            self.health_manager.record_success(self.provider_name, self.provider_capability, latency_ms=1.0, quota_remaining=None, now=datetime.now(timezone.utc))
                        reconnect_attempts = 0
                        backoff_seconds = float(getattr(self.config, "reconnect_initial_backoff_seconds", 0.25) or 0.25)
                        last_successful_update_at = getattr(getattr(quote, "meta", None), "received_at", None) or getattr(quote, "as_of", None)
                        yield QuoteWatchFrame(
                            symbol=getattr(quote, "symbol", primary_symbol) or primary_symbol,
                            feed_status="live",
                            quote=quote,
                            last_successful_update_at=last_successful_update_at,
                            last_error=None,
                            reconnect_attempts=0,
                            reconnect_backoff_seconds=None,
                        )
                        continue

                    await self._persist_raw_message(message)
                    if self.health_manager is not None and hasattr(self.health_manager, "record_degraded"):
                        self.health_manager.record_degraded(self.provider_name, self.provider_capability, reason="unsupported_message")
                    yield QuoteWatchFrame(
                        symbol=primary_symbol,
                        feed_status="stale",
                        quote=None,
                        last_successful_update_at=last_successful_update_at,
                        last_error="unsupported_message",
                        reconnect_attempts=reconnect_attempts,
                        reconnect_backoff_seconds=backoff_seconds,
                    )
                else:
                    continue
            except Exception as error:
                if self._closed:
                    break
                reconnect_attempts += 1
                if max_attempts is not None and reconnect_attempts > int(max_attempts):
                    if self.health_manager is not None and hasattr(self.health_manager, "record_failure"):
                        self.health_manager.record_failure(
                            self.provider_name,
                            self.provider_capability,
                            error_code=type(error).__name__.upper(),
                            error_message=str(error),
                            now=datetime.now(timezone.utc),
                        )
                    yield QuoteWatchFrame(
                        symbol=primary_symbol,
                        feed_status="disconnected",
                        quote=None,
                        last_successful_update_at=last_successful_update_at,
                        last_error=str(error),
                        reconnect_attempts=reconnect_attempts,
                        reconnect_backoff_seconds=None,
                    )
                    return
                if self.health_manager is not None and hasattr(self.health_manager, "record_degraded"):
                    self.health_manager.record_degraded(self.provider_name, self.provider_capability, reason=str(error))
                yield QuoteWatchFrame(
                    symbol=primary_symbol,
                    feed_status="reconnecting",
                    quote=None,
                    last_successful_update_at=last_successful_update_at,
                    last_error=str(error),
                    reconnect_attempts=reconnect_attempts,
                    reconnect_backoff_seconds=backoff_seconds,
                )
                await asyncio.sleep(min(backoff_seconds, max_backoff_seconds))
                backoff_seconds = min(backoff_seconds * 2.0, max_backoff_seconds)
                continue
            finally:
                if 'entered' in locals() and entered and hasattr(websocket, "__aexit__"):
                    await websocket.__aexit__(None, None, None)
                self._socket = None

    async def close(self):
        self._closed = True
        socket = self._socket
        self._socket = None
        if socket is not None and hasattr(socket, "close"):
            close_result = socket.close()
            await self._maybe_await(close_result)
        return None
