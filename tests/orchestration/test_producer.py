from __future__ import annotations

import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.engines.decision.producer import build_runtime_decision_inputs, build_runtime_decision_response
from backend.engines.orchestration.producer import build_runtime_engine_input_bundle, build_runtime_engine_response_bundle_from_inputs, build_runtime_market_data_input_bundle, build_runtime_event_input_bundle, build_runtime_portfolio_state_input_bundle, build_runtime_fundamental_input_bundle
from backend.schemas.models_responses import EventResponse, FundamentalResponse, RiskResponse, TechnicalResponse
from backend.schemas.shared import RequestMeta
from tests.fixtures.technical.ohlcv_sma_cross import OHLCV_SMA_CROSS


class FakeMarketDataProvider:
    async def get_bars(self, symbol, start, end, timeframe):
        return [
            {
                "symbol": symbol,
                "timeframe": timeframe,
                "start_at": start,
                "end_at": end,
                "open": 100.0,
                "high": 105.0,
                "low": 99.0,
                "close": 104.0,
                "volume": 1000,
            }
        ]


class FakeEventProvider:
    async def fetch_earnings_events(self, symbols, start, end):
        return [
            {
                "symbol": symbols[0],
                "event_type": "earnings",
                "event_date": end,
                "timezone": "UTC",
                "fiscal_year": 2026,
                "fiscal_quarter": 2,
                "meta": {
                    "provider_name": "fake_events",
                    "received_at": end,
                    "source_id": symbols[0],
                },
            }
        ]


class FakePortfolioStateProvider:
    async def get_portfolio_state(self, as_of_date=None):
        del as_of_date
        return {
            "total_equity": 250000.0,
            "cash": 120000.0,
            "positions": [{"symbol": "AAPL", "qty": 10}],
        }


class FakeFundamentalDataProvider:
    async def get_fundamental_data(self, symbol, as_of_date=None):
        del as_of_date
        return {
            "roe": 0.33 if symbol == "AAPL" else 0.2,
            "net_margin": 0.18,
            "debt_ebitda": 0.75,
        }


def test_runtime_engine_input_bundle_feeds_decision_inputs() -> None:
    meta = RequestMeta(request_id="req-runtime-1", as_of_date=date(2026, 5, 25))
    ticker = "AAPL"

    price_series = {ticker: OHLCV_SMA_CROSS}
    fundamental_data = {ticker: {"roe": 0.2, "net_margin": 0.1, "debt_ebitda": 1.0}}
    scheduled_events = {ticker: [{"event_type": "earnings", "event_date": meta.as_of_date + timedelta(days=10), "source": "sec"}]}

    runtime_inputs = build_runtime_engine_input_bundle(
        meta=meta,
        ticker_list=[ticker],
        price_series=price_series,
        fundamental_data=fundamental_data,
        scheduled_events=scheduled_events,
        as_of_date=meta.as_of_date,
        technical_config={"atr_window": 3, "ma_windows": [5, 20], "momentum_windows": [3], "momentum_threshold": 0.0},
        fundamental_config={"min_roe": 0.12, "min_net_margin": 0.05, "max_debt_ebitda": 2.0},
        event_config={"earnings_blackout_days_before": 1, "earnings_blackout_days_after": 1},
        risk_config={"per_trade_risk_pct": 0.01, "max_position_size_pct": 0.1},
        portfolio_state={"total_equity": 100000.0, "cash": 90000.0, "positions": []},
    )

    bundle = build_runtime_engine_response_bundle_from_inputs(runtime_inputs)

    assert isinstance(bundle.technical, TechnicalResponse)
    assert isinstance(bundle.fundamental, FundamentalResponse)
    assert isinstance(bundle.event, EventResponse)
    assert isinstance(bundle.risk, RiskResponse)
    assert bundle.technical.signals[ticker].ma_cross == 1
    assert bundle.risk.size_info[ticker].allowed_qty > 0

    decision_inputs = build_runtime_decision_inputs(ticker, bundle.technical, bundle.fundamental, bundle.risk, bundle.event)
    assert decision_inputs.technical_signals[ticker].ma_cross == 1
    assert decision_inputs.fundamental_results[ticker].fundamental_pass is True
    assert decision_inputs.risk_assessment[ticker].allowed_qty > 0

    response = build_runtime_decision_response(meta, ticker, decision_inputs)
    assert response.decisions[ticker].decision == "BUY_CANDIDATE"


@pytest.mark.asyncio
async def test_runtime_market_data_feed_populates_raw_bundle() -> None:
    meta = RequestMeta(request_id="req-runtime-2", as_of_date=date(2026, 5, 25))
    ticker = "AAPL"
    bar_start = datetime(2026, 5, 24, 15, 30, tzinfo=timezone.utc)
    bar_end = datetime(2026, 5, 25, 15, 30, tzinfo=timezone.utc)

    runtime_inputs = await build_runtime_market_data_input_bundle(
        market_data_provider=FakeMarketDataProvider(),
        meta=meta,
        ticker_list=[ticker],
        bar_start=bar_start,
        bar_end=bar_end,
        timeframe="1min",
        fundamental_data={ticker: {"roe": 0.2, "net_margin": 0.1, "debt_ebitda": 1.0}},
        scheduled_events={ticker: [{"event_type": "earnings", "event_date": meta.as_of_date + timedelta(days=10), "source": "sec"}]},
        as_of_date=meta.as_of_date,
        technical_config={"atr_window": 3, "ma_windows": [5, 20], "momentum_windows": [3], "momentum_threshold": 0.0},
        fundamental_config={"min_roe": 0.12, "min_net_margin": 0.05, "max_debt_ebitda": 2.0},
        event_config={"earnings_blackout_days_before": 1, "earnings_blackout_days_after": 1},
        risk_config={"per_trade_risk_pct": 0.01, "max_position_size_pct": 0.1},
        portfolio_state={"total_equity": 100000.0, "cash": 90000.0, "positions": []},
    )

    assert runtime_inputs.price_series[ticker][0]["close"] == 104.0
    bundle = build_runtime_engine_response_bundle_from_inputs(runtime_inputs)
    assert isinstance(bundle.technical, TechnicalResponse)


@pytest.mark.asyncio
async def test_runtime_event_feed_populates_scheduled_events() -> None:
    meta = RequestMeta(request_id="req-runtime-3", as_of_date=date(2026, 5, 25))
    ticker = "AAPL"
    bar_start = datetime(2026, 5, 24, 15, 30, tzinfo=timezone.utc)
    bar_end = datetime(2026, 5, 25, 15, 30, tzinfo=timezone.utc)

    runtime_inputs = await build_runtime_event_input_bundle(
        event_provider=FakeEventProvider(),
        meta=meta,
        ticker_list=[ticker],
        price_series={ticker: OHLCV_SMA_CROSS},
        fundamental_data={ticker: {"roe": 0.2, "net_margin": 0.1, "debt_ebitda": 1.0}},
        event_start=bar_start,
        event_end=bar_end,
        as_of_date=meta.as_of_date,
        technical_config={"atr_window": 3, "ma_windows": [5, 20], "momentum_windows": [3], "momentum_threshold": 0.0},
        fundamental_config={"min_roe": 0.12, "min_net_margin": 0.05, "max_debt_ebitda": 2.0},
        event_config={"earnings_blackout_days_before": 1, "earnings_blackout_days_after": 1},
        risk_config={"per_trade_risk_pct": 0.01, "max_position_size_pct": 0.1},
        portfolio_state={"total_equity": 100000.0, "cash": 90000.0, "positions": []},
    )

    assert ticker in runtime_inputs.scheduled_events
    assert runtime_inputs.scheduled_events[ticker][0]["event_type"] == "earnings"
    bundle = build_runtime_engine_response_bundle_from_inputs(runtime_inputs)
    decision_inputs = build_runtime_decision_inputs(ticker, bundle.technical, bundle.fundamental, bundle.risk, bundle.event)
    assert decision_inputs.event_flags[ticker].earnings_upcoming is True


@pytest.mark.asyncio
async def test_runtime_portfolio_state_feed_populates_raw_bundle() -> None:
    meta = RequestMeta(request_id="req-runtime-4", as_of_date=date(2026, 5, 25))
    ticker = "AAPL"

    runtime_inputs = build_runtime_engine_input_bundle(
        meta=meta,
        ticker_list=[ticker],
        price_series={ticker: OHLCV_SMA_CROSS},
        fundamental_data={ticker: {"roe": 0.2, "net_margin": 0.1, "debt_ebitda": 1.0}},
        scheduled_events={ticker: []},
        as_of_date=meta.as_of_date,
        technical_config={"atr_window": 3, "ma_windows": [5, 20], "momentum_windows": [3], "momentum_threshold": 0.0},
        fundamental_config={"min_roe": 0.12, "min_net_margin": 0.05, "max_debt_ebitda": 2.0},
        event_config={"earnings_blackout_days_before": 1, "earnings_blackout_days_after": 1},
        risk_config={"per_trade_risk_pct": 0.01, "max_position_size_pct": 0.1},
        portfolio_state={"total_equity": 100000.0, "cash": 90000.0, "positions": []},
    )

    updated_inputs = await build_runtime_portfolio_state_input_bundle(runtime_inputs, FakePortfolioStateProvider())

    assert updated_inputs.portfolio_state["total_equity"] == 250000.0
    assert updated_inputs.portfolio_state["cash"] == 120000.0
    assert updated_inputs.portfolio_state["positions"][0]["symbol"] == "AAPL"


@pytest.mark.asyncio
async def test_runtime_fundamental_feed_populates_raw_bundle() -> None:
    meta = RequestMeta(request_id="req-runtime-5", as_of_date=date(2026, 5, 25))
    ticker = "AAPL"

    runtime_inputs = build_runtime_engine_input_bundle(
        meta=meta,
        ticker_list=[ticker],
        price_series={ticker: OHLCV_SMA_CROSS},
        fundamental_data={ticker: {"roe": 0.2, "net_margin": 0.1, "debt_ebitda": 1.0}},
        scheduled_events={ticker: []},
        as_of_date=meta.as_of_date,
        technical_config={"atr_window": 3, "ma_windows": [5, 20], "momentum_windows": [3], "momentum_threshold": 0.0},
        fundamental_config={"min_roe": 0.12, "min_net_margin": 0.05, "max_debt_ebitda": 2.0},
        event_config={"earnings_blackout_days_before": 1, "earnings_blackout_days_after": 1},
        risk_config={"per_trade_risk_pct": 0.01, "max_position_size_pct": 0.1},
        portfolio_state={"total_equity": 100000.0, "cash": 90000.0, "positions": []},
    )

    updated_inputs = await build_runtime_fundamental_input_bundle(runtime_inputs, FakeFundamentalDataProvider())

    assert updated_inputs.fundamental_data[ticker]["roe"] == 0.33
    assert updated_inputs.fundamental_data[ticker]["net_margin"] == 0.18
    assert updated_inputs.fundamental_data[ticker]["debt_ebitda"] == 0.75
