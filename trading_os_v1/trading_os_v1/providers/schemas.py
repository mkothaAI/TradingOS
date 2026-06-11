from __future__ import annotations

from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, ConfigDict, model_validator, field_validator


def _ensure_utc_datetime(value: datetime, field_name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError(f"{field_name} must be UTC-aware (offset +00:00 or Z)")
    return value


class ProviderCapability(str, Enum):
    MARKET_DATA = "market_data"
    REALTIME_STREAM = "realtime_stream"
    NEWS = "news"
    EVENT = "event"
    FUNDAMENTALS = "fundamentals"


class ProviderMeta(BaseModel):
    provider_name: str
    provider_version: Optional[str] = None
    source_id: Optional[str] = None
    raw_hash: Optional[str] = None
    received_at: datetime
    is_delayed: bool = False


class _BaseProviderEvidenceRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    evidence_id: str = Field(min_length=1)
    provider_name: str = Field(min_length=1)
    capability: ProviderCapability
    symbol: Optional[str] = None
    source_id: Optional[str] = None
    fetched_at: datetime

    @field_validator("fetched_at")
    @classmethod
    def _validate_fetched_at(cls, value: datetime) -> datetime:
        return _ensure_utc_datetime(value, "fetched_at")


class RawProviderEvidenceRecord(_BaseProviderEvidenceRecord):
    kind: Literal["raw"] = "raw"
    payload: dict[str, Any]
    meta: ProviderMeta

    @model_validator(mode="after")
    def _validate_meta(self) -> "RawProviderEvidenceRecord":
        _ensure_utc_datetime(self.meta.received_at, "meta.received_at")
        return self


class NormalizedProviderEvidenceRecord(_BaseProviderEvidenceRecord):
    kind: Literal["normalized"] = "normalized"
    normalized_payload: dict[str, Any]
    raw_evidence_id: str = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_raw_link(self) -> "NormalizedProviderEvidenceRecord":
        if not self.raw_evidence_id.strip():
            raise ValueError("raw_evidence_id must be a non-empty string")
        return self


class QuoteSnapshot(BaseModel):
    symbol: str
    as_of: datetime
    bid: Optional[float] = None
    ask: Optional[float] = None
    last: Optional[float] = None
    bid_size: Optional[float] = None
    ask_size: Optional[float] = None
    last_size: Optional[float] = None
    mid: Optional[float] = None
    spread: Optional[float] = None
    currency: Optional[str] = None
    exchange: Optional[str] = None
    meta: ProviderMeta


class PriceBar(BaseModel):
    symbol: str
    timeframe: str
    start_at: datetime
    end_at: datetime
    open: float
    high: float
    low: float
    close: float
    volume: Optional[float] = None
    vwap: Optional[float] = None
    adjusted: bool = False
    split_factor: Optional[float] = None
    dividend_factor: Optional[float] = None
    meta: ProviderMeta


class NewsItem(BaseModel):
    news_id: str
    published_at: datetime
    source_name: str
    title: str
    summary: Optional[str] = None
    url: Optional[str] = None
    symbols: list[str] = Field(default_factory=list)
    language: Optional[str] = None
    author: Optional[str] = None
    sentiment_score: Optional[float] = None
    meta: ProviderMeta


class EarningsEvent(BaseModel):
    symbol: str
    event_type: Literal["earnings"]
    event_date: datetime
    timezone: Optional[str] = None
    fiscal_year: Optional[int] = None
    fiscal_quarter: Optional[int] = None
    event_time: Optional[str] = None
    eps_estimate: Optional[float] = None
    eps_actual: Optional[float] = None
    revenue_estimate: Optional[float] = None
    revenue_actual: Optional[float] = None
    guidance_text: Optional[str] = None
    status: Optional[str] = None
    meta: ProviderMeta


class CompanyFundamentals(BaseModel):
    symbol: str
    as_of: datetime
    company_name: Optional[str] = None
    exchange: Optional[str] = None
    currency: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap: Optional[float] = None
    shares_outstanding: Optional[float] = None
    float_shares: Optional[float] = None
    beta: Optional[float] = None
    pe_ttm: Optional[float] = None
    pb: Optional[float] = None
    ps: Optional[float] = None
    ev_ebitda: Optional[float] = None
    revenue_ttm: Optional[float] = None
    net_income_ttm: Optional[float] = None
    gross_margin_ttm: Optional[float] = None
    operating_margin_ttm: Optional[float] = None
    debt_to_equity: Optional[float] = None
    current_ratio: Optional[float] = None
    dividend_yield: Optional[float] = None
    fiscal_year_end: Optional[str] = None
    meta: ProviderMeta


class ProviderHealthStatus(BaseModel):
    provider_name: str
    capability: ProviderCapability
    status: Literal["healthy", "degraded", "down", "disabled"]
    last_success_at: Optional[datetime] = None
    last_failure_at: Optional[datetime] = None
    latency_ms_p50: Optional[float] = None
    latency_ms_p95: Optional[float] = None
    quota_remaining: Optional[int] = None
    quota_reset_at: Optional[datetime] = None
    staleness_seconds: Optional[float] = None
    last_error_code: Optional[str] = None
    last_error_message: Optional[str] = None
    degraded_reason: Optional[str] = None
    updated_at: datetime