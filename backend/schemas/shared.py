from __future__ import annotations
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum
from datetime import date, datetime, timedelta


def _ensure_utc_datetime(value: datetime, field_name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError(f"{field_name} must be UTC-aware (offset +00:00 or Z)")
    return value


class ResponseStatus(str, Enum):
    OK = "OK"
    ERROR = "ERROR"


class FreshnessLabel(str, Enum):
    REAL_TIME = "real_time"
    DELAYED = "delayed"
    STALE = "stale"
    SNAPSHOT = "snapshot"


class RequestMeta(BaseModel):
    request_id: str
    as_of_date: date


class FreshnessEnvelope(BaseModel):
    freshness_label: FreshnessLabel
    evidence_timestamp: datetime
    received_at: datetime
    last_updated_at: Optional[datetime] = None
    delay_seconds: Optional[float] = Field(default=None, ge=0)
    staleness_seconds: Optional[float] = Field(default=None, ge=0)
    delay_reason: Optional[str] = None

    @field_validator("evidence_timestamp")
    @classmethod
    def _validate_evidence_timestamp(cls, value: datetime) -> datetime:
        return _ensure_utc_datetime(value, "evidence_timestamp")

    @field_validator("received_at")
    @classmethod
    def _validate_received_at(cls, value: datetime) -> datetime:
        return _ensure_utc_datetime(value, "received_at")

    @field_validator("last_updated_at")
    @classmethod
    def _validate_last_updated_at(cls, value: Optional[datetime]) -> Optional[datetime]:
        if value is None:
            return None
        return _ensure_utc_datetime(value, "last_updated_at")


class TickerMetadata(BaseModel):
    ticker: str
    exchange: str
    sector: Optional[str] = None
    market_cap: Optional[float] = None
    lot_size: Optional[int] = None
    tradable: bool = True


class PriceBar(BaseModel):
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: Optional[int] = None


class UniverseConfig(BaseModel):
    allowed_markets: List[str] = Field(default_factory=lambda: ["US"])
    sector_caps: Optional[Dict[str, float]] = None
    max_universe_size: Optional[int] = None


class UniverseStats(BaseModel):
    """Universe statistics: count, total market cap, sector distribution."""
    count: int
    total_market_cap: float
    sector_exposures: Dict[str, float] = Field(default_factory=dict)


class TechnicalConfig(BaseModel):
    atr_window: int = Field(14, ge=1)
    ma_windows: Optional[List[int]] = None
    momentum_windows: Optional[List[int]] = None


class EventConfig(BaseModel):
    earnings_blackout_days_before: Optional[int] = None
    earnings_blackout_days_after: Optional[int] = None
    advisory_only: Optional[bool] = True


class PositionItem(BaseModel):
    ticker: str
    qty: int
    entry_price: float
    side: str


class PortfolioState(BaseModel):
    total_equity: float
    cash: float
    positions: List[PositionItem]


class RiskConfig(BaseModel):
    per_trade_risk_pct: Optional[float] = None
    max_position_size_pct: Optional[float] = None
    max_leverage: Optional[float] = None
    var_confidence: Optional[float] = None
    sizing_model: Optional[str] = None


class SizeInfo(BaseModel):
    allowed_qty: int
    notional: Optional[float] = None
    risk_amount: Optional[float] = None
    sizing_model_used: Optional[str] = None
    stop_distance: Optional[float] = None


class RiskMetrics(BaseModel):
    portfolio_var: Optional[float] = None
    portfolio_variance: Optional[float] = None
    volatility: Optional[float] = None


class SourceLink(BaseModel):
    rule_id: str
    file: str
    line_range: Optional[str] = None
    note: Optional[str] = None


class EvidenceContext(BaseModel):
    ticker: str = Field(min_length=1)
    analysis_id: str = Field(min_length=1)
    verdict_ref: str = Field(min_length=1)
    evidence_ids: List[str] = Field(default_factory=list)
    source_links: List[SourceLink] = Field(default_factory=list)
    primary_topics: List[str] = Field(default_factory=list)
    freshness: FreshnessEnvelope
    evidence_window_start: Optional[datetime] = None
    evidence_window_end: Optional[datetime] = None
    provenance_summary: Optional[str] = None
    stale_reason: Optional[str] = None

    @field_validator("evidence_window_start")
    @classmethod
    def _validate_evidence_window_start(cls, value: Optional[datetime]) -> Optional[datetime]:
        if value is None:
            return None
        return _ensure_utc_datetime(value, "evidence_window_start")

    @field_validator("evidence_window_end")
    @classmethod
    def _validate_evidence_window_end(cls, value: Optional[datetime]) -> Optional[datetime]:
        if value is None:
            return None
        return _ensure_utc_datetime(value, "evidence_window_end")

    @model_validator(mode="after")
    def _validate_evidence_presence(self) -> "EvidenceContext":
        if not self.evidence_ids and not self.source_links:
            raise ValueError("evidence_ids or source_links must be provided")
        return self


class ErrorItem(BaseModel):
    code: str
    message: str
    details: Optional[Dict] = None


class DecisionToken(str, Enum):
    BUY_CANDIDATE = "BUY_CANDIDATE"
    SELL_EXIT_CANDIDATE = "SELL_EXIT_CANDIDATE"
    HOLD = "HOLD"
    NO_TRADE = "NO_TRADE"


class FundamentalItem(BaseModel):
    """Fundamental check results for one ticker."""
    fundamental_pass: bool
    reasons: List[str] = Field(default_factory=list)


class StepAuditItem(BaseModel):
    step_name: str
    status: str  # OK | ERROR | SKIPPED
    duration_ms: int
    error_codes: List[str] = Field(default_factory=list)
    summary: Dict[str, Any] = Field(default_factory=dict)
