from __future__ import annotations

from datetime import datetime

import pytest

from trading_os_v1.providers.async_composition import ProviderCallSpec, compose_provider_calls
from trading_os_v1.providers.dashboard_contracts import (
    build_dashboard_shell_model,
    build_composition_fallback_panel,
    build_composition_outcome_detail_panel,
    build_composition_result_panel,
    build_evidence_timeline_items,
    build_quote_watch_item,
    build_quote_watch_panel,
    build_provider_status_rows,
)
from trading_os_v1.providers.evidence_summaries import summarize_evidence_eligibility_view, summarize_local_evidence
from trading_os_v1.providers.health import ProviderHealthManager
from trading_os_v1.providers.health_summaries import summarize_health
from trading_os_v1.providers.local_evidence_store import LocalEvidenceStore
from trading_os_v1.providers.registry import ProviderBinding, ProviderRegistry
from trading_os_v1.providers.schemas import ProviderCapability, ProviderMeta, QuoteSnapshot


def _build_registry(tmp_path):
    manager = ProviderHealthManager()
    registry = ProviderRegistry(manager)
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
            now=datetime(2024, 1, 15, 15, 30),
        )
    )
    registry.set_health(
        registry._health.record_failure(
            "primary_news",
            ProviderCapability.NEWS,
            error_code="RATE_LIMIT",
            error_message="slow",
            now=datetime(2024, 1, 15, 15, 31),
        )
    )
    return registry


@pytest.mark.asyncio
async def test_dashboard_provider_status_rows_are_deterministic(tmp_path) -> None:
    registry = _build_registry(tmp_path)
    store = LocalEvidenceStore(tmp_path)

    raw_id = await store.put_raw(
        capability=ProviderCapability.MARKET_DATA.value,
        provider_name="primary_market",
        symbol="AAPL",
        fetched_at=datetime(2024, 1, 15, 15, 30),
        payload={"last": 100.0},
        meta=ProviderMeta(provider_name="primary_market", received_at=datetime(2024, 1, 15, 15, 30)),
    )
    await store.put_normalized(
        capability=ProviderCapability.MARKET_DATA.value,
        provider_name="primary_market",
        symbol="AAPL",
        fetched_at=datetime(2024, 1, 15, 15, 30),
        normalized_payload={"last": 100.0},
        raw_evidence_id=raw_id,
    )

    health_summary = summarize_health(registry)
    evidence_summary = summarize_local_evidence(store)
    eligibility_view = summarize_evidence_eligibility_view(health_summary, evidence_summary=evidence_summary)

    rows = build_provider_status_rows(health_summary, evidence_summary, eligibility_view)

    assert [(row.provider_name, row.capability) for row in rows] == [
        ("primary_market", ProviderCapability.MARKET_DATA.value),
        ("primary_news", ProviderCapability.NEWS.value),
    ]
    assert rows[0].health_status == "healthy"
    assert rows[0].eligibility_code == "HEALTHY_ELIGIBLE"
    assert rows[0].raw_count == 1
    assert rows[0].row_severity == "healthy"
    assert rows[0].operator_summary == "healthy · eligible · evidence current"
    assert rows[0].evidence_recency == "latest evidence 2024-01-15T15:30:00"
    assert rows[1].health_status == "degraded"
    assert rows[1].eligibility_state == "not_eligible"
    assert rows[1].last_error_code == "RATE_LIMIT"
    assert rows[1].row_severity == "warning"
    assert rows[1].operator_summary == "degraded · not_eligible · check evidence"
    assert rows[1].evidence_recency == "no evidence yet"


@pytest.mark.asyncio
async def test_dashboard_evidence_timeline_items_are_stable_and_sorted(tmp_path) -> None:
    store = LocalEvidenceStore(tmp_path)

    raw_market = await store.put_raw(
        capability=ProviderCapability.MARKET_DATA.value,
        provider_name="primary_market",
        symbol="AAPL",
        fetched_at=datetime(2024, 1, 15, 15, 30),
        payload={"last": 100.0},
        meta=ProviderMeta(provider_name="primary_market", received_at=datetime(2024, 1, 15, 15, 30)),
    )
    await store.put_normalized(
        capability=ProviderCapability.MARKET_DATA.value,
        provider_name="primary_market",
        symbol="AAPL",
        fetched_at=datetime(2024, 1, 15, 15, 30),
        normalized_payload={"last": 100.0},
        raw_evidence_id=raw_market,
    )
    raw_news = await store.put_raw(
        capability=ProviderCapability.NEWS.value,
        provider_name="primary_news",
        symbol="AAPL",
        fetched_at=datetime(2024, 1, 15, 15, 31),
        payload={"headline": "One"},
        meta=ProviderMeta(provider_name="primary_news", received_at=datetime(2024, 1, 15, 15, 31)),
    )
    await store.put_normalized(
        capability=ProviderCapability.NEWS.value,
        provider_name="primary_news",
        symbol="AAPL",
        fetched_at=datetime(2024, 1, 15, 15, 31),
        normalized_payload={"headline": "One"},
        raw_evidence_id=raw_news,
    )

    items = build_evidence_timeline_items(summarize_local_evidence(store))

    assert [(item.provider_name, item.capability) for item in items] == [
        ("primary_market", ProviderCapability.MARKET_DATA.value),
        ("primary_news", ProviderCapability.NEWS.value),
    ]
    assert items[0].raw_count == 1
    assert items[0].normalized_count == 1
    assert items[0].symbols == ("AAPL",)
    assert items[1].newest_fetched_at == "2024-01-15T15:31:00"
    assert items[0].stages[0] == ("raw_evidence_written", "complete", "1 raw record(s)")
    assert items[0].stages[1] == ("normalized_evidence_linked", "complete", "1 normalized record(s)")
    assert items[0].stages[2][0] == "artifact_created_and_verified"
    assert items[0].stages[3][0] == "provenance_chain_available"


@pytest.mark.asyncio
async def test_dashboard_composition_result_panel_mapping(tmp_path) -> None:
    registry = _build_registry(tmp_path)
    store = LocalEvidenceStore(tmp_path)

    raw_id = await store.put_raw(
        capability=ProviderCapability.MARKET_DATA.value,
        provider_name="primary_market",
        symbol="AAPL",
        fetched_at=datetime(2024, 1, 15, 15, 30),
        payload={"last": 100.0},
        meta=ProviderMeta(provider_name="primary_market", received_at=datetime(2024, 1, 15, 15, 30)),
    )
    await store.put_normalized(
        capability=ProviderCapability.MARKET_DATA.value,
        provider_name="primary_market",
        symbol="AAPL",
        fetched_at=datetime(2024, 1, 15, 15, 30),
        normalized_payload={"last": 100.0},
        raw_evidence_id=raw_id,
    )

    health_summary = summarize_health(registry)
    evidence_summary = summarize_local_evidence(store)

    async def call_ok() -> dict[str, str]:
        return {"provider": "primary_market"}

    composition = await compose_provider_calls(
        [ProviderCallSpec(provider_name="primary_market", capability=ProviderCapability.MARKET_DATA.value, call=call_ok)],
        health_summary=health_summary,
        evidence_summary=evidence_summary,
    )

    panel = build_composition_result_panel(composition["outcomes"][0])

    assert panel.provider_name == "primary_market"
    assert panel.capability == ProviderCapability.MARKET_DATA.value
    assert panel.status == "ok"
    assert panel.selected_provider == "primary_market"
    assert panel.error_type is None


@pytest.mark.asyncio
async def test_dashboard_quote_watch_panel_mapping(tmp_path) -> None:
    quote = QuoteSnapshot(
        symbol="AAPL",
        as_of=datetime(2024, 1, 15, 15, 30),
        last=100.25,
        currency="USD",
        exchange="NASDAQ",
        meta=ProviderMeta(provider_name="twelvedata", source_id="AAPL", received_at=datetime(2024, 1, 15, 15, 30)),
    )

    panel = build_quote_watch_panel(quote)

    assert panel.watched_symbol == "AAPL"
    assert panel.last_price == 100.25
    assert panel.provider_name == "twelvedata"
    assert panel.source_name == "AAPL"
    assert panel.last_update_at == "2024-01-15T15:30:00"
    assert panel.stream_status == "snapshot_ready"
    assert panel.feed_status == "snapshot_ready"
    assert panel.operator_status == "Snapshot Ready"
    assert panel.recovery_copy.startswith("Feed status: snapshot_ready.")
    assert panel.watch_status == "placeholder"
    assert panel.stale is False
    assert panel.bid_available is False
    assert panel.ask_available is False
    assert panel.signals[0].label == "symbol"


@pytest.mark.asyncio
async def test_dashboard_quote_watch_panel_feed_health_mapping(tmp_path) -> None:
    quote = QuoteSnapshot(
        symbol="AAPL",
        as_of=datetime(2024, 1, 15, 15, 31),
        last=100.75,
        currency="USD",
        exchange="NASDAQ",
        meta=ProviderMeta(provider_name="twelvedata", source_id="AAPL", received_at=datetime(2024, 1, 15, 15, 31)),
    )

    panel = build_quote_watch_panel(
        quote,
        stream_status="live",
        feed_status="reconnecting",
        watch_status="watching",
        stale=True,
        last_successful_update_at=datetime(2024, 1, 15, 15, 31),
        last_error="socket dropped",
        reconnect_attempts=2,
        reconnect_backoff_seconds=0.5,
    )

    assert panel.feed_status == "reconnecting"
    assert panel.last_update_at == "2024-01-15T15:31:00"
    assert panel.last_successful_update_at == "2024-01-15T15:31:00"
    assert panel.last_error == "socket dropped"
    assert panel.reconnect_attempts == 2
    assert panel.reconnect_backoff_seconds == 0.5
    assert panel.operator_status == "Recovering"
    assert panel.recovery_copy.startswith("Last live update at 2024-01-15T15:31:00")
    assert panel.stream_status == "live"
    assert panel.stale is True
    assert panel.watch_status == "watching"


@pytest.mark.asyncio
async def test_dashboard_quote_watch_panel_warming_up_mapping(tmp_path) -> None:
    quote = QuoteSnapshot(
        symbol="AAPL",
        as_of=datetime(2024, 1, 15, 15, 31),
        last=None,
        currency="USD",
        exchange="NASDAQ",
        meta=ProviderMeta(provider_name="twelvedata", source_id="AAPL", received_at=datetime(2024, 1, 15, 15, 31)),
    )

    panel = build_quote_watch_panel(
        quote,
        stream_status="live",
        feed_status="reconnecting",
        watch_status="watching",
        stale=False,
        last_successful_update_at=None,
        last_error="socket dropped",
        reconnect_attempts=1,
        reconnect_backoff_seconds=0.5,
    )

    assert panel.last_update_at == "n/a"
    assert panel.last_successful_update_at is None
    assert panel.operator_status == "Waiting for first live tick"
    assert panel.recovery_copy.startswith("Stream is warming up.")


@pytest.mark.asyncio
async def test_dashboard_quote_watch_panel_live_state(tmp_path) -> None:
    quote = QuoteSnapshot(
        symbol="AAPL",
        as_of=datetime(2024, 1, 15, 15, 31),
        last=100.75,
        currency="USD",
        exchange="NASDAQ",
        meta=ProviderMeta(provider_name="twelvedata", source_id="AAPL", received_at=datetime(2024, 1, 15, 15, 31)),
    )

    panel = build_quote_watch_panel(quote, stream_status="live", watch_status="watching", stale=False)

    assert panel.stream_status == "live"
    assert panel.watch_status == "watching"


@pytest.mark.asyncio
async def test_dashboard_quote_watch_panel_watchlist_mapping(tmp_path) -> None:
    quote = QuoteSnapshot(
        symbol="AAPL",
        as_of=datetime(2024, 1, 15, 15, 31),
        last=100.75,
        currency="USD",
        exchange="NASDAQ",
        meta=ProviderMeta(provider_name="twelvedata", source_id="AAPL", received_at=datetime(2024, 1, 15, 15, 31)),
    )

    watchlist_items = (
        build_quote_watch_item(
            quote,
            symbol="AAPL",
            feed_status="live",
            watch_status="watching",
            stale=False,
            last_successful_update_at=datetime(2024, 1, 15, 15, 31),
            display_order=0,
            is_primary=True,
        ),
        build_quote_watch_item(None, symbol="MSFT", feed_status="snapshot_ready", watch_status="placeholder", stale=False, display_order=1),
        build_quote_watch_item(None, symbol="NVDA", feed_status="snapshot_ready", watch_status="placeholder", stale=False, display_order=2),
    )

    panel = build_quote_watch_panel(quote, stream_status="live", watch_status="watching", stale=False, watchlist_items=watchlist_items)

    assert [item.symbol for item in panel.watchlist_items] == ["AAPL", "MSFT", "NVDA"]
    assert panel.watchlist_items[0].is_primary is True
    assert panel.watchlist_items[0].display_order == 0
    assert panel.watchlist_items[0].freshness_label == "fresh"
    assert panel.watchlist_items[0].row_severity == "healthy"
    assert panel.watchlist_items[0].transition_note == "fresh"
    assert panel.watchlist_items[0].recovery_detail.startswith("last success 2024-01-15T15:31:00")
    assert panel.watchlist_items[1].operator_status == "Snapshot Ready"
    assert panel.watchlist_items[1].freshness_label == "snapshot"
    assert panel.watchlist_items[1].row_severity == "neutral"
    assert panel.watchlist_items[1].transition_note == "snapshot ready"
    assert panel.watchlist_items[2].last_price is None
    assert panel.watchlist_items[2].display_order == 2
    assert "live quote stream" in panel.note
    assert panel.stale is False


@pytest.mark.asyncio
async def test_dashboard_quote_watch_panel_orders_by_row_priority(tmp_path) -> None:
    quote = QuoteSnapshot(
        symbol="AAPL",
        as_of=datetime(2024, 1, 15, 15, 31),
        last=100.75,
        currency="USD",
        exchange="NASDAQ",
        meta=ProviderMeta(provider_name="twelvedata", source_id="AAPL", received_at=datetime(2024, 1, 15, 15, 31)),
    )

    watchlist_items = (
        build_quote_watch_item(None, symbol="NVDA", feed_status="disconnected", watch_status="unavailable", stale=True, last_error="socket dropped", display_order=2),
        build_quote_watch_item(None, symbol="MSFT", feed_status="reconnecting", watch_status="watching", stale=False, last_successful_update_at=datetime(2024, 1, 15, 15, 31), display_order=1),
        build_quote_watch_item(quote, symbol="AAPL", feed_status="live", watch_status="watching", stale=False, last_successful_update_at=datetime(2024, 1, 15, 15, 31), display_order=0, is_primary=True),
    )

    panel = build_quote_watch_panel(quote, stream_status="live", watch_status="watching", stale=False, watchlist_items=watchlist_items)

    assert [item.symbol for item in panel.watchlist_items] == ["AAPL", "NVDA", "MSFT"]
    assert panel.watchlist_items[0].row_priority < panel.watchlist_items[1].row_priority
    assert panel.watchlist_items[1].row_severity == "critical"
    assert panel.watchlist_items[2].row_severity == "warning"
    assert panel.watchlist_items[1].transition_note == "disconnected"
    assert panel.watchlist_items[2].transition_note == "recovering"


@pytest.mark.asyncio
async def test_dashboard_composition_outcome_detail_panel_mapping(tmp_path) -> None:
    registry = _build_registry(tmp_path)
    store = LocalEvidenceStore(tmp_path)

    raw_id = await store.put_raw(
        capability=ProviderCapability.MARKET_DATA.value,
        provider_name="primary_market",
        symbol="AAPL",
        fetched_at=datetime(2024, 1, 15, 15, 30),
        payload={"last": 100.0},
        meta=ProviderMeta(provider_name="primary_market", received_at=datetime(2024, 1, 15, 15, 30)),
    )
    await store.put_normalized(
        capability=ProviderCapability.MARKET_DATA.value,
        provider_name="primary_market",
        symbol="AAPL",
        fetched_at=datetime(2024, 1, 15, 15, 30),
        normalized_payload={"last": 100.0},
        raw_evidence_id=raw_id,
    )

    health_summary = summarize_health(registry)
    evidence_summary = summarize_local_evidence(store)

    async def primary_market() -> dict[str, str]:
        return {"provider": "primary_market"}

    async def backup_market() -> dict[str, str]:
        return {"provider": "backup_market"}

    async def broken_market() -> dict[str, str]:
        raise TimeoutError("composition timeout")

    composition_result = await compose_provider_calls(
        [
            ProviderCallSpec(provider_name="primary_market", capability=ProviderCapability.MARKET_DATA.value, call=primary_market, fallback_group="market_data_chain", priority=0),
            ProviderCallSpec(provider_name="backup_market", capability=ProviderCapability.MARKET_DATA.value, call=backup_market, fallback_group="market_data_chain", priority=10),
            ProviderCallSpec(provider_name="broken_market", capability=ProviderCapability.MARKET_DATA.value, call=broken_market, fallback_group="market_data_chain", priority=20),
        ],
        health_summary=health_summary,
        evidence_summary=evidence_summary,
        fallback_policy="best_available",
    )

    diagnostics_bundle = {
        "health_summary": health_summary,
        "evidence_summary": evidence_summary,
        "correlation": {
            "primary_market": {
                ProviderCapability.MARKET_DATA.value: {
                    "health_status": "healthy",
                    "total_evidence_count": 2,
                    "degraded_or_down_evidence_count": 0,
                }
            },
            "backup_market": {
                ProviderCapability.MARKET_DATA.value: {
                    "health_status": "healthy",
                    "total_evidence_count": 0,
                    "degraded_or_down_evidence_count": 0,
                }
            },
            "broken_market": {
                ProviderCapability.MARKET_DATA.value: {
                    "health_status": "healthy",
                    "total_evidence_count": 0,
                    "degraded_or_down_evidence_count": 0,
                }
            },
        },
        "eligibility": composition_result["eligibility"],
        "health_manager_present": True,
    }

    quote = QuoteSnapshot(
        symbol="AAPL",
        as_of=datetime(2024, 1, 15, 15, 30),
        last=100.25,
        currency="USD",
        exchange="NASDAQ",
        meta=ProviderMeta(provider_name="twelvedata", source_id="AAPL", received_at=datetime(2024, 1, 15, 15, 30)),
    )

    panel = build_composition_outcome_detail_panel(composition_result, diagnostics_bundle)

    assert panel.overall_status == "fallback_degraded"
    assert panel.selection_reason == "highest_priority_successful_provider_was_selected"
    assert panel.selected_provider_names == ("primary_market",)
    assert [section.title for section in panel.sections] == [
        "Summary",
        "Outcome Path",
        "Eligibility",
        "Evidence / Provenance",
        "Failures / Skips",
    ]
    assert [item.label for item in panel.sections[1].items] == [
        "backup_market / market_data",
        "broken_market / market_data",
        "primary_market / market_data",
    ]
    assert panel.sections[1].items[2].value == "ok"
    assert panel.sections[2].items[0].value == "HEALTHY_ELIGIBLE"
    assert [item.value for item in panel.sections[3].items] == [
        "0 raw / 0 normalized",
        "0 raw / 0 normalized",
        "1 raw / 1 normalized",
    ]
    assert any(item.value == "TimeoutError" for item in panel.sections[4].items)


@pytest.mark.asyncio
async def test_dashboard_composition_fallback_panel_is_deterministic(tmp_path) -> None:
    async def primary_market() -> dict[str, str]:
        return {"provider": "primary_market"}

    async def backup_market() -> dict[str, str]:
        return {"provider": "backup_market"}

    async def broken_market() -> dict[str, str]:
        raise TimeoutError("composition timeout")

    composition_result = await compose_provider_calls(
        [
            ProviderCallSpec(provider_name="primary_market", capability=ProviderCapability.MARKET_DATA.value, call=primary_market, fallback_group="market_data_chain", priority=0),
            ProviderCallSpec(provider_name="backup_market", capability=ProviderCapability.MARKET_DATA.value, call=backup_market, fallback_group="market_data_chain", priority=10),
            ProviderCallSpec(provider_name="broken_market", capability=ProviderCapability.MARKET_DATA.value, call=broken_market, fallback_group="market_data_chain", priority=20),
        ],
        fallback_policy="best_available",
    )

    panel = build_composition_fallback_panel(composition_result)

    assert panel.overall_status == "fallback_degraded"
    assert panel.fallback_policy == "best_available"
    assert panel.attempted_provider_names == ("primary_market", "backup_market", "broken_market")
    assert panel.selected_provider_names == ("primary_market",)
    assert panel.failed_provider_names == ("broken_market",)
    assert panel.skipped_provider_names == ("backup_market",)
    assert [item.status for item in panel.items] == ["ok", "skipped_fallback", "error"]
    assert panel.items[1].selected_provider == "primary_market"
    assert panel.items[2].selected_provider is None


@pytest.mark.asyncio
async def test_dashboard_shell_model_uses_backend_contracts_only(tmp_path) -> None:
    registry = _build_registry(tmp_path)
    store = LocalEvidenceStore(tmp_path)

    raw_id = await store.put_raw(
        capability=ProviderCapability.MARKET_DATA.value,
        provider_name="primary_market",
        symbol="AAPL",
        fetched_at=datetime(2024, 1, 15, 15, 30),
        payload={"last": 100.0},
        meta=ProviderMeta(provider_name="primary_market", received_at=datetime(2024, 1, 15, 15, 30)),
    )
    await store.put_normalized(
        capability=ProviderCapability.MARKET_DATA.value,
        provider_name="primary_market",
        symbol="AAPL",
        fetched_at=datetime(2024, 1, 15, 15, 30),
        normalized_payload={"last": 100.0},
        raw_evidence_id=raw_id,
    )

    health_summary = summarize_health(registry)
    evidence_summary = summarize_local_evidence(store)
    eligibility_view = summarize_evidence_eligibility_view(health_summary, evidence_summary=evidence_summary)
    diagnostics_bundle = {
        "registry": {"market_data": [{"provider_name": "primary_market", "priority": 0, "enabled": True}]},
        "health_manager_present": True,
        "health_summary": health_summary,
        "evidence_summary": evidence_summary,
        "correlation": {
            "primary_market": {
                ProviderCapability.MARKET_DATA.value: {
                    "health_status": "healthy",
                    "total_evidence_count": 2,
                    "degraded_or_down_evidence_count": 0,
                }
            }
        },
        "eligibility": eligibility_view,
    }

    composition_result = {"fallback_policy": "best_available", "outcomes": []}
    quote = QuoteSnapshot(
        symbol="AAPL",
        as_of=datetime(2024, 1, 15, 15, 30),
        last=100.25,
        currency="USD",
        exchange="NASDAQ",
        meta=ProviderMeta(provider_name="twelvedata", source_id="AAPL", received_at=datetime(2024, 1, 15, 15, 30)),
    )

    shell_model = build_dashboard_shell_model(
        health_summary=health_summary,
        evidence_summary=evidence_summary,
        eligibility_view=eligibility_view,
        diagnostics_bundle=diagnostics_bundle,
        composition_result=composition_result,
    )

    assert shell_model["provider_status_rows"][0]["provider_name"] == "primary_market"
    assert shell_model["provider_status_rows"][0]["eligibility_code"] == "HEALTHY_ELIGIBLE"
    assert shell_model["provider_status_rows"][0]["row_severity"] == "healthy"
    assert shell_model["provider_status_rows"][0]["operator_summary"] == "healthy · eligible · evidence current"
    assert shell_model["evidence_timeline_items"][0]["provider_name"] == "primary_market"
    assert shell_model["diagnostics_drawer"]["health_manager_present"] is True
    assert shell_model["diagnostics_drawer"]["status_row_count"] == 2
    assert [section["title"] for section in shell_model["diagnostics_drawer"]["sections"]] == [
        "Overview",
        "Health Signals",
        "Evidence Linkage",
        "Eligibility Reasons",
        "Correlation",
        "Composition Context",
    ]
    assert shell_model["diagnostics_drawer"]["sections"][1]["items"][0]["label"] == "primary_market / market_data"
    assert shell_model["diagnostics_drawer"]["sections"][5]["items"][0]["value"] == "best_available"
    assert shell_model["composition_outcome_detail_panel"]["selection_reason"] == "no_provider_selected"
    assert build_dashboard_shell_model(
        health_summary=health_summary,
        evidence_summary=evidence_summary,
        eligibility_view=eligibility_view,
        diagnostics_bundle=diagnostics_bundle,
        composition_result=composition_result,
        quote_snapshot=quote,
        quote_watchlist_items=(
            build_quote_watch_item(quote, symbol="AAPL", feed_status="live", watch_status="watching", stale=False, display_order=0, is_primary=True),
            build_quote_watch_item(None, symbol="MSFT", feed_status="snapshot_ready", watch_status="placeholder", stale=False, display_order=1),
            build_quote_watch_item(None, symbol="NVDA", feed_status="snapshot_ready", watch_status="placeholder", stale=False, display_order=2),
        ),
    )["quote_watch_panel"]["watchlist_items"][0]["symbol"] == "AAPL"