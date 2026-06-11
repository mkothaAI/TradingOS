from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Protocol, runtime_checkable

from backend.engines.decision.producer import build_runtime_decision_inputs
from backend.engines.event.assembler import build_event_response, compute_event
from backend.engines.fundamental.assembler import build_fundamental_response, compute_fundamental
from backend.engines.risk.calc import daily_returns, sample_variance
from backend.engines.risk.sizing import position_size_percentage_margin
from backend.engines.technical.assembler import compute_technical_engine
from backend.schemas.decision_models import TechnicalIndicatorsItem, TechnicalSignalsItem
from backend.schemas.models_responses import EventResponse, FundamentalResponse, RiskResponse, TechnicalResponse
from backend.schemas.shared import ErrorItem, RequestMeta, ResponseStatus, RiskMetrics, SizeInfo


@runtime_checkable
class MarketDataProvider(Protocol):
    async def get_bars(self, symbol: str, start: datetime, end: datetime, timeframe: str) -> list[Any]: ...


@runtime_checkable
class EventProvider(Protocol):
    async def fetch_earnings_events(self, symbols: List[str], start: datetime, end: datetime) -> list[Any]: ...


@runtime_checkable
class PortfolioStateProvider(Protocol):
    async def get_portfolio_state(self, as_of_date: date | None = None) -> Dict[str, Any]: ...


@runtime_checkable
class FundamentalDataProvider(Protocol):
    async def get_fundamental_data(self, symbol: str, as_of_date: date | None = None) -> Dict[str, Any]: ...


@dataclass(frozen=True)
class RuntimeEngineResponseBundle:
    technical: TechnicalResponse
    fundamental: FundamentalResponse
    event: EventResponse
    risk: RiskResponse


@dataclass(frozen=True)
class RuntimeEngineInputBundle:
    meta: RequestMeta
    ticker_list: List[str]
    price_series: Dict[str, List[Dict[str, Any]]]
    fundamental_data: Dict[str, Dict[str, Any]]
    scheduled_events: Dict[str, List[Dict[str, Any]]]
    as_of_date: date
    technical_config: Dict[str, Any]
    fundamental_config: Dict[str, Any]
    event_config: Dict[str, Any]
    risk_config: Dict[str, Any]
    portfolio_state: Dict[str, Any]


def _coerce_price_series(price_series: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
    coerced: Dict[str, List[Dict[str, Any]]] = {}
    for ticker, bars in price_series.items():
        coerced[ticker] = []
        for bar in bars or []:
            if hasattr(bar, "model_dump"):
                coerced[ticker].append(bar.model_dump())
            else:
                coerced[ticker].append(dict(bar))
    return coerced


def _build_technical_response(
    meta: RequestMeta,
    price_series: Dict[str, List[Dict[str, Any]]],
    technical_config: Dict[str, Any],
) -> TechnicalResponse:
    raw_result = compute_technical_engine(price_series, technical_config)
    indicators: Dict[str, TechnicalIndicatorsItem] = {}
    signals: Dict[str, TechnicalSignalsItem] = {}
    errors: List[ErrorItem] = []

    for ticker, result in raw_result.items():
        if result.get("error"):
            errors.append(ErrorItem(code=str(result["error"]), message=f"technical engine failed for {ticker}"))

        raw_indicators = result.get("indicators") or {}
        volatility_value = None
        volatility_map = raw_indicators.get("volatility")
        if isinstance(volatility_map, dict) and volatility_map:
            volatility_value = sum(float(value) for value in volatility_map.values()) / len(volatility_map)

        indicators[ticker] = TechnicalIndicatorsItem(
            atr=raw_indicators.get("atr"),
            ma=raw_indicators.get("ma"),
            returns=raw_indicators.get("returns"),
            volatility=volatility_value,
        )

        raw_signals = result.get("signals") or {}
        signals[ticker] = TechnicalSignalsItem(
            ma_cross=raw_signals.get("ma_cross"),
            candle_classification=raw_signals.get("candle"),
            atr_spike=raw_signals.get("atr_spike"),
            momentum_pass=raw_signals.get("momentum"),
        )

    status = ResponseStatus.ERROR if errors else ResponseStatus.OK
    return TechnicalResponse(meta=meta, status=status, indicators=indicators, signals=signals, errors=errors)


def _build_risk_response(
    meta: RequestMeta,
    ticker_list: List[str],
    price_series: Dict[str, List[Dict[str, Any]]],
    risk_config: Dict[str, Any],
    portfolio_state: Dict[str, Any],
) -> RiskResponse:
    total_equity = float((portfolio_state or {}).get("total_equity", 0.0) or 0.0)
    max_position_size_pct = float((risk_config or {}).get("max_position_size_pct", 0.0) or 0.0)
    if max_position_size_pct <= 0:
        max_position_size_pct = 0.1

    size_info: Dict[str, SizeInfo] = {}
    variances: List[float] = []
    errors: List[ErrorItem] = []

    for ticker in ticker_list:
        bars = price_series.get(ticker, [])
        closes = [float(bar["close"]) for bar in bars if "close" in bar]
        if len(closes) >= 2:
            try:
                variances.append(sample_variance(daily_returns(closes)))
            except ValueError as exc:
                errors.append(ErrorItem(code="RISK_HISTORY_ERROR", message=f"{ticker}: {exc}"))

        latest_price = closes[-1] if closes else None
        if latest_price is None or total_equity <= 0:
            allowed_qty = 0
        else:
            try:
                allowed_qty = position_size_percentage_margin(total_equity, max_position_size_pct, latest_price)
            except ValueError as exc:
                errors.append(ErrorItem(code="RISK_SIZING_ERROR", message=f"{ticker}: {exc}"))
                allowed_qty = 0

        notional = float(allowed_qty * latest_price) if latest_price is not None else None
        size_info[ticker] = SizeInfo(
            allowed_qty=allowed_qty,
            notional=notional,
            risk_amount=float(total_equity * float((risk_config or {}).get("per_trade_risk_pct", 0.0) or 0.0)) if total_equity > 0 else None,
            sizing_model_used="max_position_size_pct",
            stop_distance=None,
        )

    portfolio_variance = sum(variances) / len(variances) if variances else None
    volatility = math.sqrt(portfolio_variance) if portfolio_variance is not None else None
    risk_metrics = RiskMetrics(
        portfolio_var=portfolio_variance,
        portfolio_variance=portfolio_variance,
        volatility=volatility,
    )
    status = ResponseStatus.ERROR if errors else ResponseStatus.OK
    return RiskResponse(meta=meta, status=status, risk_metrics=risk_metrics, size_info=size_info, errors=errors)


def build_runtime_engine_response_bundle(
    meta: RequestMeta,
    ticker_list: List[str],
    price_series: Dict[str, List[Dict[str, Any]]],
    fundamental_data: Dict[str, Dict[str, Any]],
    scheduled_events: Dict[str, List[Dict[str, Any]]],
    as_of_date: date,
    technical_config: Dict[str, Any],
    fundamental_config: Dict[str, Any],
    event_config: Dict[str, Any],
    risk_config: Dict[str, Any],
    portfolio_state: Dict[str, Any],
) -> RuntimeEngineResponseBundle:
    """Build the typed upstream engine responses used by decision input assembly.

    This is the runtime source layer for the typed decision-input path. It is
    intentionally independent of dashboard transport and UI concerns.
    """
    coerced_price_series = _coerce_price_series(price_series)

    technical_response = _build_technical_response(meta, coerced_price_series, technical_config)
    fundamental_result = compute_fundamental(fundamental_data, fundamental_config)
    fundamental_response = build_fundamental_response(fundamental_result, meta)
    event_result = compute_event(ticker_list, scheduled_events, as_of_date, event_config)
    event_response = build_event_response(event_result, meta)
    risk_response = _build_risk_response(meta, ticker_list, coerced_price_series, risk_config, portfolio_state)

    return RuntimeEngineResponseBundle(
        technical=technical_response,
        fundamental=fundamental_response,
        event=event_response,
        risk=risk_response,
    )


def build_runtime_engine_input_bundle(
    meta: RequestMeta,
    ticker_list: List[str],
    price_series: Dict[str, List[Dict[str, Any]]],
    fundamental_data: Dict[str, Dict[str, Any]],
    scheduled_events: Dict[str, List[Dict[str, Any]]],
    as_of_date: date,
    technical_config: Dict[str, Any],
    fundamental_config: Dict[str, Any],
    event_config: Dict[str, Any],
    risk_config: Dict[str, Any],
    portfolio_state: Dict[str, Any],
) -> RuntimeEngineInputBundle:
    """Build the first raw runtime input bundle for orchestration.

    This is the upstream source for typed engine-response assembly. It accepts
    only runtime primitives and keeps dashboard/view concerns out of the path.
    """
    return RuntimeEngineInputBundle(
        meta=meta,
        ticker_list=ticker_list,
        price_series=price_series,
        fundamental_data=fundamental_data,
        scheduled_events=scheduled_events,
        as_of_date=as_of_date,
        technical_config=technical_config,
        fundamental_config=fundamental_config,
        event_config=event_config,
        risk_config=risk_config,
        portfolio_state=portfolio_state,
    )


async def build_runtime_market_data_input_bundle(
    market_data_provider: MarketDataProvider,
    meta: RequestMeta,
    ticker_list: List[str],
    bar_start: datetime,
    bar_end: datetime,
    timeframe: str,
    fundamental_data: Dict[str, Dict[str, Any]],
    scheduled_events: Dict[str, List[Dict[str, Any]]],
    as_of_date: date,
    technical_config: Dict[str, Any],
    fundamental_config: Dict[str, Any],
    event_config: Dict[str, Any],
    risk_config: Dict[str, Any],
    portfolio_state: Dict[str, Any],
) -> RuntimeEngineInputBundle:
    """Build the raw orchestration input bundle with market data sourced externally.

    This is the first genuine runtime feed into the raw bundle. Only the market
    data field is sourced from the external provider; the other fields may still
    come from compatibility data until their own runtime feeds exist.
    """
    price_series: Dict[str, List[Dict[str, Any]]] = {}
    for ticker in ticker_list:
        bars = await market_data_provider.get_bars(ticker, start=bar_start, end=bar_end, timeframe=timeframe)
        price_series[ticker] = [bar.model_dump(mode="python") if hasattr(bar, "model_dump") else dict(bar) for bar in bars]

    return build_runtime_engine_input_bundle(
        meta=meta,
        ticker_list=ticker_list,
        price_series=price_series,
        fundamental_data=fundamental_data,
        scheduled_events=scheduled_events,
        as_of_date=as_of_date,
        technical_config=technical_config,
        fundamental_config=fundamental_config,
        event_config=event_config,
        risk_config=risk_config,
        portfolio_state=portfolio_state,
    )


async def build_runtime_event_input_bundle(
    event_provider: EventProvider,
    meta: RequestMeta,
    ticker_list: List[str],
    price_series: Dict[str, List[Dict[str, Any]]],
    fundamental_data: Dict[str, Dict[str, Any]],
    event_start: datetime,
    event_end: datetime,
    as_of_date: date,
    technical_config: Dict[str, Any],
    fundamental_config: Dict[str, Any],
    event_config: Dict[str, Any],
    risk_config: Dict[str, Any],
    portfolio_state: Dict[str, Any],
) -> RuntimeEngineInputBundle:
    """Build the raw orchestration input bundle with externally sourced events.

    Only scheduled_events is sourced from the live event provider here.
    """
    earnings_events = await event_provider.fetch_earnings_events(ticker_list, start=event_start, end=event_end)
    scheduled_events: Dict[str, List[Dict[str, Any]]] = {}
    for event in earnings_events:
        if hasattr(event, "model_dump"):
            event_payload = event.model_dump(mode="python")
            event_symbol = str(getattr(event, "symbol", "") or event_payload.get("symbol") or "")
        else:
            event_payload = dict(event)
            event_symbol = str(event_payload.get("symbol") or "")
        if not event_symbol:
            continue
        event_date = event_payload.get("event_date")
        if isinstance(event_date, datetime):
            event_payload["event_date"] = event_date.date()
        scheduled_events.setdefault(event_symbol, []).append(event_payload)

    return build_runtime_engine_input_bundle(
        meta=meta,
        ticker_list=ticker_list,
        price_series=price_series,
        fundamental_data=fundamental_data,
        scheduled_events=scheduled_events,
        as_of_date=as_of_date,
        technical_config=technical_config,
        fundamental_config=fundamental_config,
        event_config=event_config,
        risk_config=risk_config,
        portfolio_state=portfolio_state,
    )


async def build_runtime_portfolio_state_input_bundle(
    inputs: RuntimeEngineInputBundle,
    portfolio_state_provider: PortfolioStateProvider,
) -> RuntimeEngineInputBundle:
    """Apply externally sourced portfolio_state to an existing raw runtime bundle.

    This keeps the scope intentionally narrow: only portfolio_state is replaced,
    while all other raw input fields remain unchanged.
    """
    portfolio_state = await portfolio_state_provider.get_portfolio_state(as_of_date=inputs.as_of_date)
    return RuntimeEngineInputBundle(
        meta=inputs.meta,
        ticker_list=inputs.ticker_list,
        price_series=inputs.price_series,
        fundamental_data=inputs.fundamental_data,
        scheduled_events=inputs.scheduled_events,
        as_of_date=inputs.as_of_date,
        technical_config=inputs.technical_config,
        fundamental_config=inputs.fundamental_config,
        event_config=inputs.event_config,
        risk_config=inputs.risk_config,
        portfolio_state=portfolio_state,
    )


async def build_runtime_fundamental_input_bundle(
    inputs: RuntimeEngineInputBundle,
    fundamental_data_provider: FundamentalDataProvider,
) -> RuntimeEngineInputBundle:
    """Apply externally sourced fundamental_data to an existing raw runtime bundle.

    This keeps the scope intentionally narrow: only fundamental_data is
    replaced, while all other raw input fields remain unchanged.
    """
    fundamental_data: Dict[str, Dict[str, Any]] = {}
    for ticker in inputs.ticker_list:
        fundamental_data[ticker] = await fundamental_data_provider.get_fundamental_data(
            ticker,
            as_of_date=inputs.as_of_date,
        )

    return RuntimeEngineInputBundle(
        meta=inputs.meta,
        ticker_list=inputs.ticker_list,
        price_series=inputs.price_series,
        fundamental_data=fundamental_data,
        scheduled_events=inputs.scheduled_events,
        as_of_date=inputs.as_of_date,
        technical_config=inputs.technical_config,
        fundamental_config=inputs.fundamental_config,
        event_config=inputs.event_config,
        risk_config=inputs.risk_config,
        portfolio_state=inputs.portfolio_state,
    )


def build_runtime_engine_response_bundle_from_inputs(
    inputs: RuntimeEngineInputBundle,
) -> RuntimeEngineResponseBundle:
    return build_runtime_engine_response_bundle(
        meta=inputs.meta,
        ticker_list=inputs.ticker_list,
        price_series=inputs.price_series,
        fundamental_data=inputs.fundamental_data,
        scheduled_events=inputs.scheduled_events,
        as_of_date=inputs.as_of_date,
        technical_config=inputs.technical_config,
        fundamental_config=inputs.fundamental_config,
        event_config=inputs.event_config,
        risk_config=inputs.risk_config,
        portfolio_state=inputs.portfolio_state,
    )


def build_runtime_decision_inputs_from_bundle(ticker: str, bundle: RuntimeEngineResponseBundle):
    return build_runtime_decision_inputs(ticker, bundle.technical, bundle.fundamental, bundle.risk, bundle.event)
