from __future__ import annotations
from typing import Dict, List, Any
from pydantic import BaseModel, Field
from .shared import RequestMeta, UniverseConfig, TickerMetadata, TechnicalConfig, PriceBar, EventConfig, RiskConfig, PortfolioState
from .decision_models import DecisionInputs


class UniverseRequest(BaseModel):
    meta: RequestMeta
    universe_config: UniverseConfig
    ticker_metadata: List[TickerMetadata]


class FundamentalRequest(BaseModel):
    meta: RequestMeta
    fundamental_config: Dict = {}  # e.g., {"min_roe": 0.12, "min_net_margin": 0.05}
    fundamental_data: Dict[str, Dict] = {}  # ticker -> {field: value, ...}


class TechnicalRequest(BaseModel):
    meta: RequestMeta
    technical_config: TechnicalConfig
    price_series: Dict[str, List[PriceBar]]


class EventRequest(BaseModel):
    meta: RequestMeta
    event_config: EventConfig
    scheduled_events: List[Dict]


class PipelineRequest(BaseModel):
    meta: RequestMeta
    ticker_list: List[str]
    payloads: Dict[str, Any] = Field(default_factory=dict)
    configs: Dict[str, Any] = Field(default_factory=dict)


class RiskRequest(BaseModel):
    meta: RequestMeta
    risk_config: RiskConfig
    portfolio_state: PortfolioState
    price_series: Dict[str, List[PriceBar]]


class DecisionRequest(BaseModel):
    meta: RequestMeta
    inputs: DecisionInputs
    policy_config: Dict = {}


class ExplanationRequest(BaseModel):
    meta: RequestMeta
    decision_payload: Dict[str, Dict]
    include_line_links: bool = False
