from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from typing import Optional, Any
import asyncio
import httpx

from trading_os_v1.providers.config import classify_provider_error, normalize_provider_config
from trading_os_v1.providers.evidence_provenance import (
    attach_provider_evidence_provenance,
    build_provider_evidence_provenance,
)
from trading_os_v1.providers.schemas import (
    NormalizedProviderEvidenceRecord,
    PriceBar,
    ProviderMeta,
    ProviderCapability,
    RawProviderEvidenceRecord,
)


@dataclass
class TiingoConfig:
    api_key: str
    base_url: str = "https://api.tiingo.com"
    timeout_seconds: int = 30
    max_retries: int = 2
    retry_delay_seconds: float = 0.1
    max_concurrent_requests: Optional[int] = None

    def __post_init__(self) -> None:
        normalized = normalize_provider_config(
            explicit={
                "api_key": self.api_key,
                "base_url": self.base_url,
                "timeout_seconds": self.timeout_seconds,
                "max_retries": self.max_retries,
                "retry_delay_seconds": self.retry_delay_seconds,
                "max_concurrent_requests": self.max_concurrent_requests,
            },
            env_map={
                "api_key": ("TIINGO_API_KEY", "TIINGO_TOKEN"),
                "base_url": "TIINGO_BASE_URL",
            },
            defaults={
                "base_url": "https://api.tiingo.com",
                "timeout_seconds": 30,
                "max_retries": 2,
                "retry_delay_seconds": 0.1,
            },
            required=("api_key",),
        )
        self.api_key = str(normalized["api_key"])
        self.base_url = str(normalized["base_url"])
        self.timeout_seconds = int(normalized["timeout_seconds"])
        self.max_retries = int(normalized["max_retries"])
        self.retry_delay_seconds = float(normalized["retry_delay_seconds"])
        self.max_concurrent_requests = normalized.get("max_concurrent_requests")


class TiingoHistoricalAdapter:
    """Minimal Tiingo historical adapter implementing daily OHLC fetch.

    Focused, small implementation to satisfy unit tests. This adapter
    tolerantly calls evidence/health hooks whether they are sync or async.
    """

    provider_name = "tiingo"
    provider_capability = ProviderCapability.MARKET_DATA

    def __init__(self, config: TiingoConfig, evidence_store: Any = None, health_manager: Any = None, http_client: Any = None):
        self.config = config
        self.evidence_store = evidence_store
        self.health_manager = health_manager
        self.http_client = http_client

    async def _maybe_await(self, result):
        if asyncio.iscoroutine(result):
            return await result
        return result

    def _parse_date(self, value: str) -> datetime:
        if value is None:
            raise ValueError("missing date")
        s = str(value)
        # handle ISO date or date-only
        if "T" in s:
            if s.endswith("Z"):
                s = s.replace("Z", "+00:00")
            return datetime.fromisoformat(s)
        # date-only YYYY-MM-DD
        dt = datetime.fromisoformat(s)
        return datetime(dt.year, dt.month, dt.day)

    async def fetch_price_bars(self, symbol: str, start: str, end: str, frequency: str = "daily") -> list[PriceBar]:
        # simple retry policy
        max_retries = int(getattr(self.config, "max_retries", 2) or 2)
        retry_delay = float(getattr(self.config, "retry_delay_seconds", 0.1) or 0.1)
        attempt = 0

        url = f"{self.config.base_url.rstrip('/')}/tiingo/daily/{symbol}/prices"
        headers = {"Authorization": f"Token {self.config.api_key}"}
        params = {"startDate": start, "endDate": end}

        for attempt in range(1, max_retries + 1):
            try:
                if self.http_client is not None:
                    resp = await self.http_client.get(url, params=params, headers=headers)
                else:
                    async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
                        resp = await client.get(url, params=params, headers=headers)

                status = getattr(resp, "status_code", None)
                # parse JSON (support sync/async response.json)
                json_coro = resp.json()
                payload = await json_coro if asyncio.iscoroutine(json_coro) else json_coro

                # persist raw evidence if available (once per fetch)
                fetched_at = datetime.now(timezone.utc)
                meta = ProviderMeta(provider_name=self.provider_name, provider_version=None, source_id=symbol, raw_hash=None, received_at=fetched_at, is_delayed=False)
                raw_id = None
                if self.evidence_store is not None:
                    try:
                        raw_result = self.evidence_store.put_raw(capability=self.provider_capability.value, provider_name=self.provider_name, symbol=symbol, fetched_at=fetched_at, payload={"prices": payload}, meta=meta)
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
                        payload={"prices": payload},
                        meta=meta,
                    )

                classification = classify_provider_error(http_status=status, payload=payload)

                # handle HTTP status codes
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
                    # retry
                    await asyncio.sleep(retry_delay)
                    continue

                # success path
                bars: list[PriceBar] = []
                for raw_item in (payload or []):
                    try:
                        dt = self._parse_date(raw_item.get("date"))
                        start_at = dt
                        end_at = dt + timedelta(days=1)
                        pb = PriceBar(
                            symbol=symbol,
                            timeframe="1d",
                            start_at=start_at,
                            end_at=end_at,
                            open=float(raw_item.get("open")),
                            high=float(raw_item.get("high")),
                            low=float(raw_item.get("low")),
                            close=float(raw_item.get("close")),
                            volume=raw_item.get("volume"),
                            adjusted=bool(raw_item.get("adjClose") is not None),
                            meta=meta,
                        )
                        # build a returned object that includes provider and evidence id
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
                            object.__setattr__(returned, "evidence_id", raw_id)

                        bars.append(returned)
                    except Exception as e:
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
                # Authentication errors are terminal and should not trigger extra raw persistence or retries
                if "authentication failed" in str(error).lower():
                    raise
                # final attempt failure handling
                if attempt == max_retries:
                    if self.evidence_store is not None:
                        try:
                            error_fetched_at = datetime.now(timezone.utc)
                            error_meta = ProviderMeta(provider_name=self.provider_name, received_at=error_fetched_at)
                            error_raw_record = RawProviderEvidenceRecord(
                                evidence_id=f"raw-error-{symbol}-{int(error_fetched_at.timestamp())}",
                                provider_name=self.provider_name,
                                capability=self.provider_capability,
                                symbol=symbol,
                                source_id=symbol,
                                fetched_at=error_fetched_at,
                                payload={"error": str(error)},
                                meta=error_meta,
                            )
                            await self._maybe_await(self.evidence_store.put_raw(capability=self.provider_capability.value, provider_name=self.provider_name, symbol=symbol, fetched_at=error_raw_record.fetched_at, payload=error_raw_record.payload, meta=error_raw_record.meta))
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
                # else will retry

        # if retries exhausted without explicit raise, record failure once then raise
        try:
            if self.evidence_store is not None:
                exhausted_fetched_at = datetime.now(timezone.utc)
                exhausted_meta = ProviderMeta(provider_name=self.provider_name, received_at=exhausted_fetched_at)
                exhausted_raw_record = RawProviderEvidenceRecord(
                    evidence_id=f"raw-error-{symbol}-{int(exhausted_fetched_at.timestamp())}",
                    provider_name=self.provider_name,
                    capability=self.provider_capability,
                    symbol=symbol,
                    source_id=symbol,
                    fetched_at=exhausted_fetched_at,
                    payload={"error": "exhausted retries"},
                    meta=exhausted_meta,
                )
                await self._maybe_await(self.evidence_store.put_raw(capability=self.provider_capability.value, provider_name=self.provider_name, symbol=symbol, fetched_at=exhausted_raw_record.fetched_at, payload=exhausted_raw_record.payload, meta=exhausted_raw_record.meta))
        except Exception:
            pass
        if self.health_manager is not None:
            try:
                self.health_manager.record_failure(self.provider_name, self.provider_capability, error_code="RetryExhausted", error_message="exhausted retries")
            except Exception:
                pass
        raise Exception("unhandled tiingo fetch error")

    async def get_provider_meta(self):
        return SimpleNamespace(provider="tiingo", base_url=self.config.base_url)

    async def close(self):
        return None
