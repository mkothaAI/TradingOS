"""FastAPI application for My Trading OS v1."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import re
from datetime import datetime, timedelta, timezone
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel

from trading_os_v1.providers.dashboard_contracts import build_dashboard_projection_bundle, build_dashboard_shell_model, build_quote_watch_item, build_quote_watch_panel
from backend.schemas.decision_models import (
    RecommendationBlock,
    RecommendationBlockType,
    RecommendationStatus,
    EntryPlan,
    EntryBias,
    OptionContractSnapshot,
    OptionContractType,
    OptionsProfile,
    MonitoringCondition,
    MonitoringConditionType,
    MonitoringState,
    MonitoringStateStatus,
)
from trading_os_v1.providers.adapters.recommendation_runtime import get_runtime_recommendation_blocks
from trading_os_v1.providers.adapters.follow_up_runtime import get_runtime_follow_ups
from trading_os_v1.providers.adapters.options_runtime import get_runtime_options_profiles
from trading_os_v1.providers.adapters.monitoring_runtime import get_runtime_monitoring_states
from trading_os_v1.providers.adapters.alert_runtime import get_runtime_alert_events
from backend.engines.orchestration.producer import build_runtime_engine_input_bundle, build_runtime_engine_response_bundle_from_inputs, build_runtime_market_data_input_bundle, build_runtime_event_input_bundle, build_runtime_portfolio_state_input_bundle, build_runtime_fundamental_input_bundle
from backend.engines.decision.producer import build_runtime_decision_response
from backend.engines.decision.producer import build_runtime_decision_inputs
from backend.schemas.shared import FreshnessEnvelope, EvidenceContext, FreshnessLabel
from backend.schemas.shared import RequestMeta
from trading_os_v1.providers.async_composition import ProviderCallSpec, compose_provider_calls
from trading_os_v1.providers.diagnostics import build_provider_diagnostic_bundle
from trading_os_v1.providers.evidence_summaries import summarize_evidence_eligibility_view, summarize_local_evidence
from trading_os_v1.providers.health_summaries import summarize_health
from trading_os_v1.providers.local_evidence_store import LocalEvidenceStore
from trading_os_v1.providers.registry import ProviderBinding, ProviderRegistry
from trading_os_v1.providers.adapters.finnhub import FinnhubConfig, FinnhubEventAdapter
from trading_os_v1.providers.adapters.fmp import FMPFundamentalDataProvider
from trading_os_v1.providers.adapters.portfolio_state import FilePortfolioStateProvider
from trading_os_v1.providers.adapters.twelvedata import QuoteWatchFrame, TwelveDataConfig, TwelveDataMarketDataProvider, TwelveDataRealtimeAdapter, TwelveDataRealtimeConfig
from trading_os_v1.providers.schemas import ProviderCapability, ProviderMeta, QuoteSnapshot
from trading_os_v1.providers.streaming import StreamEventType, build_stream_event, format_sse_message


app = FastAPI(title="My Trading OS v1")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_FRONTEND_INDEX = Path(__file__).resolve().parent.parent / "frontend" / "index.html"

_SYMBOL_PATTERN = re.compile(r"^[A-Z]{3,5}$")
_QUOTE_WATCHLIST_SYMBOLS = ("AAPL", "MSFT", "NVDA")


class AnalyzeSymbolRequest(BaseModel):
    """Loose request model so the endpoint can return project-specific 400s."""

    symbol: str


@app.get("/")
async def dashboard_shell() -> HTMLResponse:
    return HTMLResponse(_FRONTEND_INDEX.read_text(encoding="utf-8"))


async def _build_dashboard_source_model() -> dict[str, object]:
    fixed_now = datetime(2024, 1, 15, 15, 30, tzinfo=timezone.utc)
    with TemporaryDirectory() as temp_dir:
        registry = ProviderRegistry()
        registry.register(
            ProviderBinding(
                capability=ProviderCapability.MARKET_DATA,
                provider_name="primary_market",
                factory=lambda: object(),
                priority=0,
            )
        )
        registry.register(
            ProviderBinding(
                capability=ProviderCapability.NEWS,
                provider_name="primary_news",
                factory=lambda: object(),
                priority=0,
            )
        )
        registry.set_health(
            registry._health.record_success(
                "primary_market",
                ProviderCapability.MARKET_DATA,
                latency_ms=8.0,
                now=fixed_now,
            )
        )
        registry.set_health(
            registry._health.record_failure(
                "primary_news",
                ProviderCapability.NEWS,
                error_code="RATE_LIMIT",
                error_message="slow",
            )
        )

        store = LocalEvidenceStore(temp_dir)
        raw_id = await store.put_raw(
            capability=ProviderCapability.MARKET_DATA.value,
            provider_name="primary_market",
            symbol="AAPL",
            fetched_at=fixed_now,
            payload={"last": 100.0},
            meta=ProviderMeta(provider_name="primary_market", received_at=fixed_now),
        )
        await store.put_normalized(
            capability=ProviderCapability.MARKET_DATA.value,
            provider_name="primary_market",
            symbol="AAPL",
            fetched_at=fixed_now,
            normalized_payload={"last": 100.0},
            raw_evidence_id=raw_id,
        )

        quote_snapshot = QuoteSnapshot(
            symbol="AAPL",
            as_of=fixed_now,
            last=100.25,
            currency="USD",
            exchange="NASDAQ",
            meta=ProviderMeta(provider_name="twelvedata", source_id="AAPL", received_at=fixed_now),
        )
        watchlist_states = {
            item_symbol: {"feed_status": "snapshot_ready", "watch_status": "placeholder", "stale": False}
            for item_symbol in _QUOTE_WATCHLIST_SYMBOLS
        }
        watchlist_states["AAPL"] = {
            "quote": quote_snapshot,
            "feed_status": "snapshot_ready",
            "watch_status": "placeholder",
            "stale": False,
        }
        quote_watchlist_items = _build_quote_watchlist_items(watchlist_states, primary_symbol="AAPL")

        health_summary = summarize_health(registry)
        evidence_summary = summarize_local_evidence(store)
        eligibility_view = summarize_evidence_eligibility_view(health_summary, evidence_summary=evidence_summary)

        async def primary_market_call() -> dict[str, str]:
            return {"provider": "primary_market", "mode": "primary"}

        async def backup_market_call() -> dict[str, str]:
            return {"provider": "backup_market", "mode": "fallback"}

        async def broken_market_call() -> dict[str, str]:
            raise RuntimeError("composition timeout")

        composition_result = await compose_provider_calls(
            [
                ProviderCallSpec(provider_name="primary_market", capability=ProviderCapability.MARKET_DATA.value, call=primary_market_call, fallback_group="market_data_chain", priority=0),
                ProviderCallSpec(provider_name="backup_market", capability=ProviderCapability.MARKET_DATA.value, call=backup_market_call, fallback_group="market_data_chain", priority=10),
                ProviderCallSpec(provider_name="broken_market", capability=ProviderCapability.MARKET_DATA.value, call=broken_market_call, fallback_group="market_data_chain", priority=20),
            ],
            health_summary=health_summary,
            evidence_summary=evidence_summary,
            fallback_policy="best_available",
        )
        diagnostics_bundle = build_provider_diagnostic_bundle(registry, registry._health, store, temp_dir=temp_dir)
        # Build a small freshness/evidence context and obtain runtime domain objects.
        freshness = FreshnessEnvelope(
            freshness_label=FreshnessLabel.SNAPSHOT,
            evidence_timestamp=fixed_now,
            received_at=fixed_now,
        )

        evidence_ctx = EvidenceContext(
            ticker="AAPL",
            analysis_id="analysis-runtime-1",
            verdict_ref="verdict-runtime-1",
            evidence_ids=[raw_id],
            freshness=freshness,
            provenance_summary="local evidence",
        )
        follow_up_qs, follow_up_as = get_runtime_follow_ups(freshness, evidence_ctx)

        runtime_decision_response = None
        try:
            runtime_inputs = None
            fallback_portfolio_state = {"total_equity": 100000.0, "cash": 90000.0, "positions": []}
            fallback_fundamental_data = {evidence_ctx.ticker: {"roe": 0.15, "net_margin": 0.2, "debt_ebitda": 1.0}}
            api_key = (os.getenv("TWELVEDATA_API_KEY") or os.getenv("TWELVE_DATA_API_KEY") or "").strip()
            if api_key:
                market_data_provider = TwelveDataMarketDataProvider(
                    TwelveDataConfig(api_key=api_key),
                    evidence_store=store,
                )
                runtime_inputs = await build_runtime_market_data_input_bundle(
                    market_data_provider=market_data_provider,
                    meta=RequestMeta(request_id="dashboard-runtime-1", as_of_date=fixed_now.date()),
                    ticker_list=[evidence_ctx.ticker],
                    bar_start=fixed_now - timedelta(days=5),
                    bar_end=fixed_now,
                    timeframe="1min",
                    fundamental_data=fallback_fundamental_data,
                    scheduled_events={evidence_ctx.ticker: []},
                    as_of_date=fixed_now.date(),
                    technical_config={"atr_window": 3, "ma_windows": [3, 5], "momentum_windows": [3], "momentum_threshold": 0.0},
                    fundamental_config={"min_roe": 0.12, "min_net_margin": 0.05, "max_debt_ebitda": 2.0},
                    event_config={"earnings_blackout_days_before": 1, "earnings_blackout_days_after": 1},
                    risk_config={"per_trade_risk_pct": 0.01, "max_position_size_pct": 0.1},
                    portfolio_state=fallback_portfolio_state,
                )
            if runtime_inputs is None:
                finnhub_key = (os.getenv("FINNHUB_API_KEY") or os.getenv("FINNHUB_TOKEN") or os.getenv("FINNHUB_API_TOKEN") or "").strip()
                if finnhub_key:
                    event_provider = FinnhubEventAdapter(FinnhubConfig(api_key=finnhub_key, base_url="https://finnhub.io/api/v1"), evidence_store=store)
                    runtime_inputs = await build_runtime_event_input_bundle(
                        event_provider=event_provider,
                        meta=RequestMeta(request_id="dashboard-runtime-1", as_of_date=fixed_now.date()),
                        ticker_list=[evidence_ctx.ticker],
                        price_series={
                            evidence_ctx.ticker: [
                                {"open": 110.0, "high": 111.0, "low": 109.0, "close": 110.0, "volume": 1000},
                                {"open": 109.5, "high": 110.0, "low": 108.5, "close": 109.0, "volume": 1100},
                                {"open": 108.8, "high": 109.2, "low": 107.9, "close": 108.0, "volume": 1200},
                                {"open": 107.9, "high": 108.5, "low": 107.0, "close": 107.0, "volume": 1300},
                                {"open": 106.8, "high": 107.2, "low": 106.0, "close": 106.0, "volume": 1400},
                                {"open": 119.0, "high": 121.0, "low": 118.5, "close": 120.0, "volume": 1500},
                            ]
                        },
                        fundamental_data=fallback_fundamental_data,
                        event_start=fixed_now - timedelta(days=240),
                        event_end=fixed_now + timedelta(days=30),
                        as_of_date=fixed_now.date(),
                        technical_config={"atr_window": 3, "ma_windows": [3, 5], "momentum_windows": [3], "momentum_threshold": 0.0},
                        fundamental_config={"min_roe": 0.12, "min_net_margin": 0.05, "max_debt_ebitda": 2.0},
                        event_config={"earnings_blackout_days_before": 1, "earnings_blackout_days_after": 1},
                        risk_config={"per_trade_risk_pct": 0.01, "max_position_size_pct": 0.1},
                        portfolio_state=fallback_portfolio_state,
                    )
            if runtime_inputs is None:
                runtime_inputs = build_runtime_engine_input_bundle(
                    meta=RequestMeta(request_id="dashboard-runtime-1", as_of_date=fixed_now.date()),
                    ticker_list=[evidence_ctx.ticker],
                    price_series={
                        evidence_ctx.ticker: [
                            {"open": 110.0, "high": 111.0, "low": 109.0, "close": 110.0, "volume": 1000},
                            {"open": 109.5, "high": 110.0, "low": 108.5, "close": 109.0, "volume": 1100},
                            {"open": 108.8, "high": 109.2, "low": 107.9, "close": 108.0, "volume": 1200},
                            {"open": 107.9, "high": 108.5, "low": 107.0, "close": 107.0, "volume": 1300},
                            {"open": 106.8, "high": 107.2, "low": 106.0, "close": 106.0, "volume": 1400},
                            {"open": 119.0, "high": 121.0, "low": 118.5, "close": 120.0, "volume": 1500},
                        ]
                    },
                    fundamental_data=fallback_fundamental_data,
                    scheduled_events={evidence_ctx.ticker: []},
                    as_of_date=fixed_now.date(),
                    technical_config={"atr_window": 3, "ma_windows": [3, 5], "momentum_windows": [3], "momentum_threshold": 0.0},
                    fundamental_config={"min_roe": 0.12, "min_net_margin": 0.05, "max_debt_ebitda": 2.0},
                    event_config={"earnings_blackout_days_before": 1, "earnings_blackout_days_after": 1},
                    risk_config={"per_trade_risk_pct": 0.01, "max_position_size_pct": 0.1},
                    portfolio_state=fallback_portfolio_state,
                )

            portfolio_state_path = (os.getenv("PORTFOLIO_STATE_JSON_PATH") or "").strip()
            if runtime_inputs is not None and portfolio_state_path:
                try:
                    runtime_inputs = await build_runtime_portfolio_state_input_bundle(
                        runtime_inputs,
                        FilePortfolioStateProvider.from_environment(),
                    )
                except Exception:
                    pass

            fmp_key = (os.getenv("FMP_API_KEY") or os.getenv("FINANCIALMODELINGPREP_API_KEY") or os.getenv("FMP_KEY") or "").strip()
            if runtime_inputs is not None and fmp_key:
                try:
                    runtime_inputs = await build_runtime_fundamental_input_bundle(
                        runtime_inputs,
                        FMPFundamentalDataProvider(api_key=fmp_key),
                    )
                except Exception:
                    pass
            runtime_bundle = build_runtime_engine_response_bundle_from_inputs(runtime_inputs)
            runtime_decision_inputs = build_runtime_decision_inputs(
                evidence_ctx.ticker,
                runtime_bundle.technical,
                runtime_bundle.fundamental,
                runtime_bundle.risk,
                runtime_bundle.event,
            )
            runtime_decision_response = build_runtime_decision_response(
                RequestMeta(request_id="dashboard-runtime-1", as_of_date=fixed_now.date()),
                evidence_ctx.ticker,
                runtime_decision_inputs,
            )
        except Exception:
            runtime_decision_response = None

        # Obtain recommendation-family domain objects from the runtime adapter
        recommendation_blocks = get_runtime_recommendation_blocks(freshness, evidence_ctx)
        if runtime_decision_response is not None:
            recommendation_blocks = get_runtime_recommendation_blocks(
                freshness,
                evidence_ctx,
                now=fixed_now,
                decision_response=runtime_decision_response,
            )

        options_profiles = get_runtime_options_profiles(freshness, evidence_ctx)

        projection_bundle = build_dashboard_projection_bundle(
            follow_up_questions=follow_up_qs,
            follow_up_answers=follow_up_as,
            recommendation_blocks=recommendation_blocks,
            options_profiles=options_profiles,
            monitoring_states=get_runtime_monitoring_states(freshness, evidence_ctx),
            alert_events=get_runtime_alert_events(freshness, evidence_ctx, fixed_now),
        )

        shell_model = build_dashboard_shell_model(
            health_summary=health_summary,
            evidence_summary=evidence_summary,
            eligibility_view=eligibility_view,
            diagnostics_bundle=diagnostics_bundle,
            composition_result=composition_result,
            quote_snapshot=quote_snapshot,
            quote_watchlist_items=quote_watchlist_items,
            projection_bundle=projection_bundle,
        )
        return {
            "health_rows": shell_model["provider_status_rows"],
            "evidence_timeline_items": shell_model["evidence_timeline_items"],
            "composition_fallback_panel": shell_model["composition_fallback_panel"],
            "composition_outcome_detail_panel": shell_model["composition_outcome_detail_panel"],
            "quote_watch_panel": shell_model["quote_watch_panel"],
            "diagnostics_drawer": shell_model["diagnostics_drawer"],
            "projection_bundle": shell_model["projection_bundle"],
            "registry_snapshot": diagnostics_bundle["registry"],
            "health_manager_present": diagnostics_bundle["health_manager_present"],
        }


def _build_quote_stream_adapter() -> TwelveDataRealtimeAdapter | None:
    api_key = (os.getenv("TWELVEDATA_API_KEY") or os.getenv("TWELVE_DATA_API_KEY") or "").strip()
    if not api_key:
        return None
    return TwelveDataRealtimeAdapter(TwelveDataRealtimeConfig(api_key=api_key))


def _is_quote_stale(quote: QuoteSnapshot) -> bool:
    quote_time = quote.as_of
    if quote_time.tzinfo is None:
        quote_time = quote_time.replace(tzinfo=timezone.utc)
    age_seconds = max((datetime.now(timezone.utc) - quote_time.astimezone(timezone.utc)).total_seconds(), 0.0)
    return age_seconds > 30.0 or bool(getattr(getattr(quote, "meta", None), "is_delayed", False))


def _build_quote_watch_panel_from_quote(
    quote: QuoteSnapshot,
    *,
    feed_status: str,
    watch_status: str,
    stale: bool,
    last_successful_update_at: datetime | None = None,
    last_error: str | None = None,
    reconnect_attempts: int = 0,
    reconnect_backoff_seconds: float | None = None,
    watchlist_items: tuple[object, ...] | None = None,
) -> dict[str, object]:
    effective_last_successful_update_at = last_successful_update_at
    if effective_last_successful_update_at is None and str(feed_status).lower() == "live":
        effective_last_successful_update_at = getattr(getattr(quote, "meta", None), "received_at", None) or getattr(quote, "as_of", None)

    panel = build_quote_watch_panel(
        quote,
        stream_status=feed_status,
        feed_status=feed_status,
        watch_status=watch_status,
        stale=stale,
        last_successful_update_at=effective_last_successful_update_at,
        last_error=last_error,
        reconnect_attempts=reconnect_attempts,
        reconnect_backoff_seconds=reconnect_backoff_seconds,
        watchlist_items=watchlist_items,
    )
    return panel


def _build_quote_watchlist_items(symbol_states: dict[str, dict[str, object]], primary_symbol: str) -> tuple[object, ...]:
    items = []
    for display_order, item_symbol in enumerate(_QUOTE_WATCHLIST_SYMBOLS):
        state = symbol_states.get(item_symbol) or {}
        items.append(
            build_quote_watch_item(
                state.get("quote"),
                symbol=item_symbol,
                stream_status=str(state.get("feed_status") or "snapshot_ready"),
                feed_status=str(state.get("feed_status") or "snapshot_ready"),
                watch_status=str(state.get("watch_status") or ("watching" if state.get("feed_status") == "live" else "placeholder")),
                stale=bool(state.get("stale") or False),
                last_successful_update_at=state.get("last_successful_update_at"),
                last_error=state.get("last_error"),
                reconnect_attempts=int(state.get("reconnect_attempts") or 0),
                reconnect_backoff_seconds=state.get("reconnect_backoff_seconds"),
                display_order=display_order,
                is_primary=item_symbol == primary_symbol,
            )
        )
    return tuple(items)


def _build_primary_quote_from_state(symbol_states: dict[str, dict[str, object]], primary_symbol: str) -> QuoteSnapshot:
    state = symbol_states.get(primary_symbol) or {}
    quote = state.get("quote")
    if quote is not None:
        return quote  # type: ignore[return-value]
    now = datetime.now(timezone.utc)
    return QuoteSnapshot(
        symbol=primary_symbol,
        as_of=now,
        meta=ProviderMeta(provider_name="twelvedata", source_id=primary_symbol, received_at=now),
    )


async def _iter_quote_watch_stream(symbol: str) -> AsyncIterator[str]:
    adapter = _build_quote_stream_adapter()
    event_index = 6
    watchlist_states: dict[str, dict[str, object]] = {item_symbol: {} for item_symbol in _QUOTE_WATCHLIST_SYMBOLS}

    if adapter is None:
        fallback_quote = QuoteSnapshot(
            symbol=symbol,
            as_of=datetime.now(timezone.utc),
            meta=ProviderMeta(provider_name="twelvedata", source_id=symbol, received_at=datetime.now(timezone.utc)),
        )
        panel = build_quote_watch_panel(
            fallback_quote,
            stream_status="disconnected",
            feed_status="disconnected",
            watch_status="unavailable",
            stale=True,
            last_error="TWELVEDATA_API_KEY not configured",
            watchlist_items=_build_quote_watchlist_items(watchlist_states, primary_symbol="AAPL"),
        )
        yield format_sse_message(
            build_stream_event(StreamEventType.QUOTE_WATCH_SNAPSHOT, {"quote_watch_panel": panel}),
            event_id=f"dashboard-{event_index}",
        )
        return

    try:
        if hasattr(adapter, "stream_quote_watch"):
            async for frame in adapter.stream_quote_watch(_QUOTE_WATCHLIST_SYMBOLS):
                quote = frame.quote or QuoteSnapshot(
                    symbol=frame.symbol or symbol,
                    as_of=frame.last_successful_update_at or datetime.now(timezone.utc),
                    meta=ProviderMeta(provider_name="twelvedata", source_id=frame.symbol or symbol, received_at=frame.last_successful_update_at or datetime.now(timezone.utc)),
                )
                frame_symbol = str(frame.symbol or symbol)
                watchlist_states[frame_symbol] = {
                    "quote": quote if frame.quote is not None else watchlist_states.get(frame_symbol, {}).get("quote"),
                    "feed_status": frame.feed_status,
                    "watch_status": "watching" if frame.feed_status == "live" else frame.feed_status,
                    "stale": frame.feed_status != "live" or _is_quote_stale(quote),
                    "last_successful_update_at": frame.last_successful_update_at,
                    "last_error": frame.last_error,
                    "reconnect_attempts": frame.reconnect_attempts,
                    "reconnect_backoff_seconds": frame.reconnect_backoff_seconds,
                }
                primary_quote = _build_primary_quote_from_state(watchlist_states, "AAPL")
                primary_state = watchlist_states.get("AAPL") or {}
                panel = _build_quote_watch_panel_from_quote(
                    primary_quote,
                    feed_status=str(primary_state.get("feed_status") or "snapshot_ready"),
                    watch_status=str(primary_state.get("watch_status") or "placeholder"),
                    stale=bool(primary_state.get("stale") or False),
                    last_successful_update_at=primary_state.get("last_successful_update_at"),
                    last_error=primary_state.get("last_error"),
                    reconnect_attempts=int(primary_state.get("reconnect_attempts") or 0),
                    reconnect_backoff_seconds=primary_state.get("reconnect_backoff_seconds"),
                    watchlist_items=_build_quote_watchlist_items(watchlist_states, primary_symbol="AAPL"),
                )
                yield format_sse_message(
                    build_stream_event(StreamEventType.QUOTE_WATCH_SNAPSHOT, {"quote_watch_panel": panel}),
                    event_id=f"dashboard-{event_index}",
                )
                event_index += 1
        else:
            async for quote in adapter.stream_quotes(_QUOTE_WATCHLIST_SYMBOLS):
                frame_symbol = str(getattr(quote, "symbol", None) or symbol)
                if frame_symbol in watchlist_states:
                    watchlist_states[frame_symbol] = {
                        "quote": quote,
                        "feed_status": "live",
                        "watch_status": "watching",
                        "stale": _is_quote_stale(quote),
                        "last_successful_update_at": getattr(getattr(quote, "meta", None), "received_at", None) or getattr(quote, "as_of", None),
                        "last_error": None,
                        "reconnect_attempts": 0,
                        "reconnect_backoff_seconds": None,
                    }
                primary_quote = _build_primary_quote_from_state(watchlist_states, "AAPL")
                panel = _build_quote_watch_panel_from_quote(
                    primary_quote,
                    feed_status="live",
                    watch_status="watching",
                    stale=_is_quote_stale(primary_quote),
                    watchlist_items=_build_quote_watchlist_items(watchlist_states, primary_symbol="AAPL"),
                )
                yield format_sse_message(
                    build_stream_event(StreamEventType.QUOTE_WATCH_SNAPSHOT, {"quote_watch_panel": panel}),
                    event_id=f"dashboard-{event_index}",
                )
                event_index += 1
    finally:
        await adapter.close()


@app.get("/dashboard/stream")
async def dashboard_stream() -> StreamingResponse:
    snapshot = await _build_dashboard_source_model()

    async def event_stream() -> AsyncIterator[str]:
        yield format_sse_message(
            build_stream_event(StreamEventType.HEALTH_SNAPSHOT, {"provider_status_rows": snapshot["health_rows"]}),
            event_id="dashboard-1",
        )
        yield format_sse_message(
            build_stream_event(
                StreamEventType.EVIDENCE_TIMELINE_SNAPSHOT,
                {"evidence_timeline_items": snapshot["evidence_timeline_items"]},
            ),
            event_id="dashboard-2",
        )
        yield format_sse_message(
            build_stream_event(
                StreamEventType.COMPOSITION_FALLBACK_SNAPSHOT,
                {"composition_fallback_panel": snapshot["composition_fallback_panel"]},
            ),
            event_id="dashboard-3",
        )
        yield format_sse_message(
            build_stream_event(
                StreamEventType.COMPOSITION_OUTCOME,
                {"composition_outcome_detail_panel": snapshot["composition_outcome_detail_panel"]},
            ),
            event_id="dashboard-4",
        )
        yield format_sse_message(
            build_stream_event(
                StreamEventType.DIAGNOSTICS_SNAPSHOT,
                {
                    "diagnostics_drawer": snapshot["diagnostics_drawer"],
                        "projection_bundle": snapshot["projection_bundle"],
                    "registry_snapshot": snapshot["registry_snapshot"],
                    "health_manager_present": snapshot["health_manager_present"],
                },
            ),
            event_id="dashboard-5",
        )
        async for quote_event in _iter_quote_watch_stream("AAPL"):
            yield quote_event
        await asyncio.sleep(0.25)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/analyze-symbol")
async def analyze_symbol(request: AnalyzeSymbolRequest):
    symbol = request.symbol.strip()

    if symbol == "ERROR":
        raise HTTPException(status_code=500, detail="Internal server error while analyzing symbol")

    if not symbol.isalpha():
        raise HTTPException(status_code=400, detail="Symbol contains invalid characters")

    if not _SYMBOL_PATTERN.fullmatch(symbol):
        raise HTTPException(status_code=400, detail="Invalid symbol format. Must be 3 uppercase letters.")

    price_data = {
        "symbol": symbol,
        "price": 150.25,
        "volume": 500000,
        "timestamp": "2026-05-15T15:30:00Z",
    }

    indicators = {
        "ma50": 148.75,
        "rsi": 65.3,
        "volatility": 2.1,
    }

    decision = {
        "symbol": symbol,
        "price": price_data["price"],
        "indicators": indicators,
        "decision": "BUY_CANDIDATE" if indicators["rsi"] < 70 else "SELL_CANDIDATE",
    }

    return decision