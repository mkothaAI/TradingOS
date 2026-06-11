from __future__ import annotations
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from .shared import (
    RequestMeta,
    ResponseStatus,
    ErrorItem,
    UniverseStats,
    FundamentalItem,
)
from .decision_models import (
    TechnicalIndicatorsItem,
    TechnicalSignalsItem,
    EventFlagsItem,
)
from .decision_models import DecisionItem, ExplanationItem
from .shared import RiskMetrics, SizeInfo


class UniverseItem(BaseModel):
    """Single universe member (v1: no per-symbol reason codes)."""

    ticker: str
    metadata: Dict[str, Any]  # Full TickerMetadata


class UniverseResponse(BaseModel):
    meta: RequestMeta
    status: ResponseStatus
    universe_list: List[UniverseItem] = Field(default_factory=list)
    universe_stats: UniverseStats
    errors: List[ErrorItem] = Field(default_factory=list)


class FundamentalResponse(BaseModel):
    """Fundamental engine response."""

    meta: RequestMeta
    status: ResponseStatus
    results: Dict[str, FundamentalItem]  # ticker -> FundamentalItem
    errors: List[ErrorItem] = Field(default_factory=list)


class TechnicalResponse(BaseModel):
    meta: RequestMeta
    status: ResponseStatus
    indicators: Dict[str, TechnicalIndicatorsItem]
    signals: Dict[str, TechnicalSignalsItem]
    errors: List[ErrorItem] = []


class RiskResponse(BaseModel):
    meta: RequestMeta
    status: ResponseStatus
    risk_metrics: RiskMetrics
    size_info: Dict[str, SizeInfo]
    errors: List[ErrorItem] = []


class DecisionResponse(BaseModel):
    meta: RequestMeta
    status: ResponseStatus
    decisions: Dict[str, DecisionItem]
    errors: List[ErrorItem] = []


class ExplanationResponse(BaseModel):
    meta: RequestMeta
    status: ResponseStatus
    explanations: Dict[str, ExplanationItem]
    errors: List[ErrorItem] = []


class EventResponse(BaseModel):
    """Event engine response."""

    meta: RequestMeta
    status: ResponseStatus
    event_flags: Dict[str, EventFlagsItem]
    errors: List[ErrorItem] = Field(default_factory=list)

class PipelineResponse(BaseModel):
    meta: RequestMeta
    run_id: str
    status: ResponseStatus
    decisions: Optional[Dict[str, DecisionItem]] = None
    event_flags: Optional[Dict[str, EventFlagsItem]] = None
    errors: List[ErrorItem] = Field(default_factory=list)
    audit: List["StepAuditItem"] = Field(default_factory=list)
    timing: Optional[Dict[str, int]] = None


