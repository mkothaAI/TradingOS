"""Fixtures for orchestration tests."""
from datetime import date
import pytest
from backend.schemas.shared import RequestMeta, UniverseStats, ErrorItem
from backend.schemas.models_responses import (
    UniverseResponse,
    FundamentalResponse,
    EventResponse,
    RiskResponse,
    DecisionResponse,
)
from backend.schemas.decision_models import DecisionItem
from backend.schemas.shared import RiskMetrics, SizeInfo


@pytest.fixture
def request_meta():
    return RequestMeta(request_id="REQ-PIPE-001", as_of_date=date(2024,1,15))


@pytest.fixture
def ticker_list():
    return ["AAPL","TSLA","MSFT"]


@pytest.fixture
def universe_response(ticker_list, request_meta):
    stats = UniverseStats(count=len(ticker_list), total_market_cap=1000.0, sector_exposures={})
    items = []
    return UniverseResponse(meta=request_meta, status="OK", universe_list=items, universe_stats=stats, errors=[])


@pytest.fixture
def fundamental_response(ticker_list, request_meta):
    results = {t: {"fundamental_pass": True, "reasons": []} for t in ticker_list}
    return FundamentalResponse(meta=request_meta, status="OK", results=results, errors=[])


@pytest.fixture
def event_response(request_meta):
    return EventResponse(meta=request_meta, status="OK", event_flags={}, errors=[])


@pytest.fixture
def risk_response(request_meta, ticker_list):
    metrics = RiskMetrics()
    size_info = {t: SizeInfo(allowed_qty=0) for t in ticker_list}
    return RiskResponse(meta=request_meta, status="OK", risk_metrics=metrics, size_info=size_info, errors=[])


@pytest.fixture
def decision_response(request_meta, ticker_list):
    decisions = {}
    for t in ticker_list:
        decisions[t] = DecisionItem(ticker=t, decision="BUY_CANDIDATE", size_info=None, reason_codes=["OK"], applied_rules=["R1"])
    return DecisionResponse(meta=request_meta, status="OK", decisions=decisions, errors=[])
