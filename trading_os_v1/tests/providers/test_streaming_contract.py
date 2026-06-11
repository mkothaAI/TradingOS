from __future__ import annotations

from datetime import datetime

import pytest

from trading_os_v1.providers.async_composition import ProviderCallSpec, compose_provider_calls
from trading_os_v1.providers.evidence_summaries import summarize_evidence_eligibility_view, summarize_local_evidence
from trading_os_v1.providers.health import ProviderHealthManager
from trading_os_v1.providers.health_summaries import summarize_health
from trading_os_v1.providers.local_evidence_store import LocalEvidenceStore
from trading_os_v1.providers.registry import ProviderBinding, ProviderRegistry
from trading_os_v1.providers.schemas import ProviderCapability, ProviderMeta
from trading_os_v1.providers.streaming import (
    StreamEventType,
    build_stream_event,
    iter_sse_messages,
    parse_sse_message,
    format_sse_message,
    serialize_stream_event,
)


def _build_registry_and_store(tmp_path):
    registry = ProviderRegistry(ProviderHealthManager())
    registry.register(
        ProviderBinding(
            capability=ProviderCapability.MARKET_DATA,
            provider_name="primary_market",
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
    store = LocalEvidenceStore(tmp_path)
    return registry, store


@pytest.mark.asyncio
async def test_sse_event_serialization(tmp_path) -> None:
    registry, store = _build_registry_and_store(tmp_path)
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
    eligibility = summarize_evidence_eligibility_view(health_summary, evidence_summary=evidence_summary)

    health_event = build_stream_event(StreamEventType.HEALTH_SNAPSHOT, health_summary)
    eligibility_event = build_stream_event(StreamEventType.ELIGIBILITY_SNAPSHOT, eligibility)
    evidence_event = build_stream_event(StreamEventType.EVIDENCE_SUMMARY, evidence_summary)
    diagnostics_event = build_stream_event(
        StreamEventType.DIAGNOSTICS_SNAPSHOT,
        {"diagnostics_drawer": {"health_manager_present": True, "sections": [{"title": "Overview", "items": []}]}},
    )
    quote_event = build_stream_event(
        StreamEventType.QUOTE_WATCH_SNAPSHOT,
        {
            "quote_watch_panel": {
                "watched_symbol": "AAPL",
                "provider_name": "twelvedata",
                "source_name": "AAPL",
                "last_price": 100.25,
                "last_update_at": "2024-01-15T15:30:00",
                "last_successful_update_at": "2024-01-15T15:30:00",
                "stream_status": "live",
                "feed_status": "live",
                "operator_status": "Live",
                "recovery_copy": "Feed is current. Last live update at 2024-01-15T15:30:00.",
                "recovery_detail": "last success 2024-01-15T15:30:00; no recent error",
                "transition_note": "fresh",
                "freshness_label": "fresh",
                "row_severity": "healthy",
                "row_priority": 40,
                "watch_status": "watching",
                "stale": False,
                "bid_available": False,
                "ask_available": False,
                "last_error": None,
                "reconnect_attempts": 0,
                "reconnect_backoff_seconds": None,
                "note": "backend-owned live quote stream",
                "watchlist_items": [
                    {"symbol": "AAPL", "last_price": 100.25, "provider_name": "twelvedata", "source_name": "AAPL", "last_update_at": "2024-01-15T15:30:00", "last_successful_update_at": "2024-01-15T15:30:00", "stream_status": "live", "feed_status": "live", "operator_status": "Live", "recovery_copy": "Feed is current. Last live update at 2024-01-15T15:30:00.", "recovery_detail": "last success 2024-01-15T15:30:00; no recent error", "transition_note": "fresh", "freshness_label": "fresh", "row_severity": "healthy", "row_priority": 40, "watch_status": "watching", "stale": False, "last_error": None, "reconnect_attempts": 0, "reconnect_backoff_seconds": None, "display_order": 0, "is_primary": True},
                    {"symbol": "MSFT", "last_price": None, "provider_name": "twelvedata", "source_name": "MSFT", "last_update_at": "n/a", "last_successful_update_at": None, "stream_status": "snapshot_ready", "feed_status": "snapshot_ready", "operator_status": "Snapshot Ready", "recovery_copy": "Feed status: snapshot_ready.", "recovery_detail": "last success n/a; no recent error", "transition_note": "snapshot", "freshness_label": "snapshot", "row_severity": "neutral", "row_priority": 150, "watch_status": "placeholder", "stale": False, "last_error": None, "reconnect_attempts": 0, "reconnect_backoff_seconds": None, "display_order": 1, "is_primary": False},
                    {"symbol": "NVDA", "last_price": None, "provider_name": "twelvedata", "source_name": "NVDA", "last_update_at": "n/a", "last_successful_update_at": None, "stream_status": "snapshot_ready", "feed_status": "snapshot_ready", "operator_status": "Snapshot Ready", "recovery_copy": "Feed status: snapshot_ready.", "recovery_detail": "last success n/a; no recent error", "transition_note": "snapshot", "freshness_label": "snapshot", "row_severity": "neutral", "row_priority": 150, "watch_status": "placeholder", "stale": False, "last_error": None, "reconnect_attempts": 0, "reconnect_backoff_seconds": None, "display_order": 2, "is_primary": False},
                ],
                "signals": [{"label": "symbol", "value": "AAPL"}],
            }
        },
    )
    composition_detail_event = build_stream_event(
        StreamEventType.COMPOSITION_OUTCOME,
        {
            "composition_outcome_detail_panel": {
                "overall_status": "fallback_degraded",
                "fallback_policy": "best_available",
                "selection_reason": "highest_priority_successful_provider_was_selected",
                "selected_provider_names": ["primary_market"],
                "attempted_provider_names": ["primary_market", "backup_market"],
                "failed_provider_names": [],
                "skipped_provider_names": ["backup_market"],
                "sections": [{"title": "Summary", "items": []}],
            }
        },
    )
    composition_event = build_stream_event(
        StreamEventType.COMPOSITION_FALLBACK_SNAPSHOT,
        {
            "composition_fallback_panel": {
                "overall_status": "fallback_applied",
                "fallback_policy": "best_available",
                "attempted_provider_names": ["primary_market", "backup_market"],
                "selected_provider_names": ["primary_market"],
                "failed_provider_names": [],
                "skipped_provider_names": ["backup_market"],
                "items": [],
            }
        },
    )
    timeline_event = build_stream_event(
        StreamEventType.EVIDENCE_TIMELINE_SNAPSHOT,
        {"evidence_timeline_items": [{"provider_name": "primary_market", "capability": ProviderCapability.MARKET_DATA.value}]},
    )

    assert serialize_stream_event(health_event) == serialize_stream_event(health_event)
    assert serialize_stream_event(eligibility_event) == serialize_stream_event(eligibility_event)
    assert serialize_stream_event(evidence_event) == serialize_stream_event(evidence_event)
    assert serialize_stream_event(diagnostics_event) == serialize_stream_event(diagnostics_event)
    assert serialize_stream_event(quote_event) == serialize_stream_event(quote_event)
    assert serialize_stream_event(composition_detail_event) == serialize_stream_event(composition_detail_event)
    assert serialize_stream_event(composition_event) == serialize_stream_event(composition_event)
    assert serialize_stream_event(timeline_event) == serialize_stream_event(timeline_event)

    assert '"event_type":"HealthSnapshot"' in serialize_stream_event(health_event)
    assert '"event_type":"EligibilitySnapshot"' in serialize_stream_event(eligibility_event)
    assert '"event_type":"EvidenceSummary"' in serialize_stream_event(evidence_event)
    assert '"event_type":"DiagnosticsSnapshot"' in serialize_stream_event(diagnostics_event)
    assert '"event_type":"QuoteWatchSnapshot"' in serialize_stream_event(quote_event)
    assert '"event_type":"CompositionOutcome"' in serialize_stream_event(composition_detail_event)
    assert '"event_type":"EvidenceTimelineSnapshot"' in serialize_stream_event(timeline_event)
    assert '"event_type":"CompositionFallbackSnapshot"' in serialize_stream_event(composition_event)
    assert format_sse_message(health_event, event_id="evt-1").endswith("\n\n")


@pytest.mark.asyncio
async def test_event_schema_compatibility(tmp_path) -> None:
    registry, store = _build_registry_and_store(tmp_path)
    raw_id = await store.put_raw(
        capability=ProviderCapability.MARKET_DATA.value,
        provider_name="primary_market",
        symbol="AAPL",
        fetched_at=datetime(2024, 1, 15, 15, 30),
        payload={"last": 101.0},
        meta=ProviderMeta(provider_name="primary_market", received_at=datetime(2024, 1, 15, 15, 30)),
    )
    await store.put_normalized(
        capability=ProviderCapability.MARKET_DATA.value,
        provider_name="primary_market",
        symbol="AAPL",
        fetched_at=datetime(2024, 1, 15, 15, 30),
        normalized_payload={"last": 101.0},
        raw_evidence_id=raw_id,
    )

    health_summary = summarize_health(registry)
    evidence_summary = summarize_local_evidence(store)
    eligibility = summarize_evidence_eligibility_view(health_summary, evidence_summary=evidence_summary)

    async def call_ok() -> dict[str, str]:
        return {"provider": "primary_market"}

    composition = await compose_provider_calls(
        [ProviderCallSpec(provider_name="primary_market", capability=ProviderCapability.MARKET_DATA.value, call=call_ok)],
        health_summary=health_summary,
        evidence_summary=evidence_summary,
    )

    quote_event = build_stream_event(
        StreamEventType.QUOTE_WATCH_SNAPSHOT,
        {
            "quote_watch_panel": {
                "watched_symbol": "AAPL",
                "provider_name": "twelvedata",
                "source_name": "AAPL",
                "last_price": 100.25,
                "last_update_at": "2024-01-15T15:30:00",
                "last_successful_update_at": "2024-01-15T15:30:00",
                "stream_status": "live",
                "feed_status": "live",
                "operator_status": "Live",
                "recovery_copy": "Feed is current. Last live update at 2024-01-15T15:30:00.",
                "recovery_detail": "last success 2024-01-15T15:30:00; no recent error",
                "transition_note": "fresh",
                "freshness_label": "fresh",
                "row_severity": "healthy",
                "row_priority": 40,
                "watch_status": "watching",
                "stale": False,
                "bid_available": False,
                "ask_available": False,
                "last_error": None,
                "reconnect_attempts": 0,
                "reconnect_backoff_seconds": None,
                "note": "backend-owned live quote stream",
                "watchlist_items": [
                    {"symbol": "AAPL", "last_price": 100.25, "provider_name": "twelvedata", "source_name": "AAPL", "last_update_at": "2024-01-15T15:30:00", "last_successful_update_at": "2024-01-15T15:30:00", "stream_status": "live", "feed_status": "live", "operator_status": "Live", "recovery_copy": "Feed is current. Last live update at 2024-01-15T15:30:00.", "recovery_detail": "last success 2024-01-15T15:30:00; no recent error", "transition_note": "fresh", "freshness_label": "fresh", "row_severity": "healthy", "row_priority": 40, "watch_status": "watching", "stale": False, "last_error": None, "reconnect_attempts": 0, "reconnect_backoff_seconds": None, "display_order": 0, "is_primary": True},
                    {"symbol": "MSFT", "last_price": None, "provider_name": "twelvedata", "source_name": "MSFT", "last_update_at": "n/a", "last_successful_update_at": None, "stream_status": "snapshot_ready", "feed_status": "snapshot_ready", "operator_status": "Snapshot Ready", "recovery_copy": "Feed status: snapshot_ready.", "recovery_detail": "last success n/a; no recent error", "transition_note": "snapshot", "freshness_label": "snapshot", "row_severity": "neutral", "row_priority": 150, "watch_status": "placeholder", "stale": False, "last_error": None, "reconnect_attempts": 0, "reconnect_backoff_seconds": None, "display_order": 1, "is_primary": False},
                    {"symbol": "NVDA", "last_price": None, "provider_name": "twelvedata", "source_name": "NVDA", "last_update_at": "n/a", "last_successful_update_at": None, "stream_status": "snapshot_ready", "feed_status": "snapshot_ready", "operator_status": "Snapshot Ready", "recovery_copy": "Feed status: snapshot_ready.", "recovery_detail": "last success n/a; no recent error", "transition_note": "snapshot", "freshness_label": "snapshot", "row_severity": "neutral", "row_priority": 150, "watch_status": "placeholder", "stale": False, "last_error": None, "reconnect_attempts": 0, "reconnect_backoff_seconds": None, "display_order": 2, "is_primary": False},
                ],
                "signals": [{"label": "symbol", "value": "AAPL"}],
            }
        },
    )

    events = [
        build_stream_event(StreamEventType.HEALTH_SNAPSHOT, health_summary),
        build_stream_event(StreamEventType.EVIDENCE_TIMELINE_SNAPSHOT, {"evidence_timeline_items": [{"provider_name": "primary_market", "capability": ProviderCapability.MARKET_DATA.value}]}),
        build_stream_event(StreamEventType.COMPOSITION_FALLBACK_SNAPSHOT, {"composition_fallback_panel": {"overall_status": "fallback_applied", "fallback_policy": "best_available", "attempted_provider_names": ["primary_market", "backup_market"], "selected_provider_names": ["primary_market"], "failed_provider_names": [], "skipped_provider_names": ["backup_market"], "items": []}}),
        build_stream_event(StreamEventType.COMPOSITION_OUTCOME, {"composition_outcome_detail_panel": {"overall_status": "fallback_degraded", "fallback_policy": "best_available", "selection_reason": "highest_priority_successful_provider_was_selected", "selected_provider_names": ["primary_market"], "attempted_provider_names": ["primary_market", "backup_market"], "failed_provider_names": [], "skipped_provider_names": ["backup_market"], "sections": [{"title": "Summary", "items": []}]}}),
        quote_event,
        build_stream_event(StreamEventType.ELIGIBILITY_SNAPSHOT, eligibility),
        build_stream_event(StreamEventType.EVIDENCE_SUMMARY, evidence_summary),
        build_stream_event(StreamEventType.DIAGNOSTICS_SNAPSHOT, {"diagnostics_drawer": {"health_manager_present": True, "sections": [{"title": "Overview", "items": []}]}}),
        build_stream_event(StreamEventType.COMPOSITION_OUTCOME, composition),
    ]

    for event in events:
        parsed = parse_sse_message(
            f"id: evt-1\nevent: {event['event_type']}\ndata: {serialize_stream_event(event['payload'])}\n"
        )
        assert parsed["event_type"] == event["event_type"]
        assert isinstance(parsed["payload"], dict)


@pytest.mark.asyncio
async def test_streaming_contract_round_trip(tmp_path) -> None:
    registry, store = _build_registry_and_store(tmp_path)
    raw_id = await store.put_raw(
        capability=ProviderCapability.MARKET_DATA.value,
        provider_name="primary_market",
        symbol="AAPL",
        fetched_at=datetime(2024, 1, 15, 15, 30),
        payload={"last": 102.0},
        meta=ProviderMeta(provider_name="primary_market", received_at=datetime(2024, 1, 15, 15, 30)),
    )
    await store.put_normalized(
        capability=ProviderCapability.MARKET_DATA.value,
        provider_name="primary_market",
        symbol="AAPL",
        fetched_at=datetime(2024, 1, 15, 15, 30),
        normalized_payload={"last": 102.0},
        raw_evidence_id=raw_id,
    )

    health_summary = summarize_health(registry)
    evidence_summary = summarize_local_evidence(store)
    eligibility = summarize_evidence_eligibility_view(health_summary, evidence_summary=evidence_summary)

    async def call_ok() -> dict[str, str]:
        return {"provider": "primary_market"}

    composition = await compose_provider_calls(
        [ProviderCallSpec(provider_name="primary_market", capability=ProviderCapability.MARKET_DATA.value, call=call_ok)],
        health_summary=health_summary,
        evidence_summary=evidence_summary,
    )

    quote_event = build_stream_event(
        StreamEventType.QUOTE_WATCH_SNAPSHOT,
        {
            "quote_watch_panel": {
                "watched_symbol": "AAPL",
                "provider_name": "twelvedata",
                "source_name": "AAPL",
                "last_price": 100.25,
                "last_update_at": "2024-01-15T15:30:00",
                "last_successful_update_at": "2024-01-15T15:30:00",
                "stream_status": "live",
                "feed_status": "live",
                "operator_status": "Live",
                "recovery_copy": "Feed is current. Last live update at 2024-01-15T15:30:00.",
                "freshness_label": "fresh",
                "row_severity": "healthy",
                "row_priority": 40,
                "watch_status": "watching",
                "stale": False,
                "bid_available": False,
                "ask_available": False,
                "last_error": None,
                "reconnect_attempts": 0,
                "reconnect_backoff_seconds": None,
                "note": "backend-owned live quote stream",
                "watchlist_items": [
                    {"symbol": "AAPL", "last_price": 100.25, "provider_name": "twelvedata", "source_name": "AAPL", "last_update_at": "2024-01-15T15:30:00", "last_successful_update_at": "2024-01-15T15:30:00", "stream_status": "live", "feed_status": "live", "operator_status": "Live", "recovery_copy": "Feed is current. Last live update at 2024-01-15T15:30:00.", "freshness_label": "fresh", "row_severity": "healthy", "row_priority": 40, "watch_status": "watching", "stale": False, "last_error": None, "reconnect_attempts": 0, "reconnect_backoff_seconds": None, "display_order": 0, "is_primary": True},
                    {"symbol": "MSFT", "last_price": None, "provider_name": "twelvedata", "source_name": "MSFT", "last_update_at": "n/a", "last_successful_update_at": None, "stream_status": "snapshot_ready", "feed_status": "snapshot_ready", "operator_status": "Snapshot Ready", "recovery_copy": "Feed status: snapshot_ready.", "freshness_label": "snapshot", "row_severity": "neutral", "row_priority": 150, "watch_status": "placeholder", "stale": False, "last_error": None, "reconnect_attempts": 0, "reconnect_backoff_seconds": None, "display_order": 1, "is_primary": False},
                    {"symbol": "NVDA", "last_price": None, "provider_name": "twelvedata", "source_name": "NVDA", "last_update_at": "n/a", "last_successful_update_at": None, "stream_status": "snapshot_ready", "feed_status": "snapshot_ready", "operator_status": "Snapshot Ready", "recovery_copy": "Feed status: snapshot_ready.", "freshness_label": "snapshot", "row_severity": "neutral", "row_priority": 150, "watch_status": "placeholder", "stale": False, "last_error": None, "reconnect_attempts": 0, "reconnect_backoff_seconds": None, "display_order": 2, "is_primary": False},
                ],
                "signals": [{"label": "symbol", "value": "AAPL"}],
            }
        },
    )

    composition_detail = build_stream_event(
        StreamEventType.COMPOSITION_OUTCOME,
        {
            "composition_outcome_detail_panel": {
                "overall_status": "ok",
                "fallback_policy": "none",
                "selection_reason": "successful_provider_returned_a_result",
                "selected_provider_names": ["primary_market"],
                "attempted_provider_names": ["primary_market"],
                "failed_provider_names": [],
                "skipped_provider_names": [],
                "sections": [{"title": "Summary", "items": []}],
            }
        },
    )

    events = [
        build_stream_event(StreamEventType.HEALTH_SNAPSHOT, health_summary),
        build_stream_event(
            StreamEventType.EVIDENCE_TIMELINE_SNAPSHOT,
            {"evidence_timeline_items": [{"provider_name": "primary_market", "capability": ProviderCapability.MARKET_DATA.value}]},
        ),
        build_stream_event(StreamEventType.COMPOSITION_FALLBACK_SNAPSHOT, {"composition_fallback_panel": {"overall_status": "fallback_applied", "fallback_policy": "best_available", "attempted_provider_names": ["primary_market", "backup_market"], "selected_provider_names": ["primary_market"], "failed_provider_names": [], "skipped_provider_names": ["backup_market"], "items": []}}),
        composition_detail,
        quote_event,
        build_stream_event(StreamEventType.ELIGIBILITY_SNAPSHOT, eligibility),
        build_stream_event(StreamEventType.EVIDENCE_SUMMARY, evidence_summary),
        build_stream_event(StreamEventType.COMPOSITION_OUTCOME, composition),
    ]

    received: list[dict[str, object]] = []
    async for message in iter_sse_messages(events, event_id_prefix="stream", delay_seconds=0.0):
        received.append(parse_sse_message(message))

    assert [item["event_type"] for item in received] == [event["event_type"] for event in events]
    assert received[0]["id"] == "stream-1"
    assert received[1]["id"] == "stream-2"
    assert received[2]["id"] == "stream-3"
    assert received[3]["id"] == "stream-4"
    assert received[4]["id"] == "stream-5"
    assert received[5]["id"] == "stream-6"
    assert received[6]["id"] == "stream-7"
    assert received[7]["id"] == "stream-8"
    assert received[3]["payload"]["composition_outcome_detail_panel"]["selection_reason"] == "successful_provider_returned_a_result"
    assert received[4]["payload"]["quote_watch_panel"]["watched_symbol"] == "AAPL"
    assert received[1]["payload"]["evidence_timeline_items"][0]["provider_name"] == "primary_market"