from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import socket

import pytest

from trading_os_v1.providers.composition import build_test_provider_registry
from trading_os_v1.providers.local_evidence_store import LocalEvidenceStore
from trading_os_v1.providers.schemas import ProviderCapability, QuoteSnapshot


def test_composed_registry_resolves_expected_providers_by_capability() -> None:
    registry = build_test_provider_registry()

    market = registry.resolve(ProviderCapability.MARKET_DATA)
    news = registry.resolve(ProviderCapability.NEWS)
    event = registry.resolve(ProviderCapability.EVENT)
    fundamentals = registry.resolve(ProviderCapability.FUNDAMENTALS)
    realtime = registry.resolve(ProviderCapability.REALTIME_STREAM)

    assert market.provider_name == "fake_market_primary"
    assert news.provider_name == "fake_news_primary"
    assert event.provider_name == "fake_event_primary"
    assert fundamentals.provider_name == "fake_fundamentals_primary"
    assert realtime.provider_name == "polling_realtime"


def test_composed_registry_fallback_order_is_deterministic() -> None:
    registry = build_test_provider_registry()
    resolved = registry.resolve_all(ProviderCapability.NEWS)
    assert [provider.provider_name for provider in resolved] == ["fake_news_primary", "fake_news_fallback"]


@pytest.mark.asyncio
async def test_polling_realtime_is_composed_from_wired_fake_market_provider() -> None:
    registry = build_test_provider_registry(symbols=["AAPL"], polling_interval_seconds=0)
    realtime = registry.resolve(ProviderCapability.REALTIME_STREAM)

    stream = realtime.stream_quotes(["AAPL"])
    quote = await stream.__anext__()

    assert isinstance(quote, QuoteSnapshot)
    assert quote.symbol == "AAPL"
    assert quote.meta.provider_name == "fake_market_primary"

    await realtime.close()


def test_composed_registry_health_aware_skipping_works() -> None:
    registry = build_test_provider_registry()
    registry.set_health(
        registry._health.record_failure(
            "fake_news_primary",
            ProviderCapability.NEWS,
            error_code="AUTH",
            error_message="unauthorized",
            now=datetime(2024, 1, 15, 15, 30),
        )
    )

    selected = registry.resolve(ProviderCapability.NEWS)
    assert selected.provider_name == "fake_news_fallback"


@pytest.mark.asyncio
async def test_composed_provider_writes_raw_and_normalized_evidence(tmp_path) -> None:
    store = LocalEvidenceStore(tmp_path)
    registry = build_test_provider_registry(evidence_store=store)
    quote_provider = registry.resolve(ProviderCapability.MARKET_DATA)

    quote = await quote_provider.get_quote("AAPL")

    raw_path = Path(tmp_path) / "raw.jsonl"
    normalized_path = Path(tmp_path) / "normalized.jsonl"
    assert raw_path.exists()
    assert normalized_path.exists()

    raw_records = [json.loads(line) for line in raw_path.read_text().splitlines() if line.strip()]
    normalized_records = [json.loads(line) for line in normalized_path.read_text().splitlines() if line.strip()]

    assert len(raw_records) == 1
    assert len(normalized_records) == 1
    assert raw_records[0]["provider_name"] == "fake_market_primary"
    assert normalized_records[0]["provider_name"] == "fake_market_primary"
    assert normalized_records[0]["raw_evidence_id"] == raw_records[0]["evidence_id"]
    assert quote.symbol == "AAPL"


@pytest.mark.asyncio
async def test_composed_provider_can_write_normalized_evidence_linked_to_raw(tmp_path) -> None:
    store = LocalEvidenceStore(tmp_path)
    registry = build_test_provider_registry(evidence_store=store)
    news_provider = registry.resolve(ProviderCapability.NEWS)

    news_items = await news_provider.fetch_news(["AAPL"], start=datetime(2024, 1, 15, 15, 30), end=datetime(2024, 1, 15, 15, 31))

    raw_records = [json.loads(line) for line in (Path(tmp_path) / "raw.jsonl").read_text().splitlines() if line.strip()]
    normalized_records = [json.loads(line) for line in (Path(tmp_path) / "normalized.jsonl").read_text().splitlines() if line.strip()]

    assert news_items[0].title == "AAPL headline"
    assert raw_records[0]["evidence_id"] == normalized_records[0]["raw_evidence_id"]
    assert raw_records[0]["symbol"] == "AAPL"
    assert normalized_records[0]["capability"] == ProviderCapability.NEWS.value


@pytest.mark.asyncio
async def test_evidence_is_persisted_locally_through_composed_setup(tmp_path) -> None:
    store = LocalEvidenceStore(tmp_path)
    registry = build_test_provider_registry(evidence_store=store)
    event_provider = registry.resolve(ProviderCapability.EVENT)
    fundamentals_provider = registry.resolve(ProviderCapability.FUNDAMENTALS)

    await event_provider.fetch_earnings_events(["AAPL"], start=datetime(2024, 1, 15, 15, 30), end=datetime(2024, 1, 15, 15, 31))
    await fundamentals_provider.get_company_fundamentals("AAPL")

    raw_lines = (Path(tmp_path) / "raw.jsonl").read_text().splitlines()
    normalized_lines = (Path(tmp_path) / "normalized.jsonl").read_text().splitlines()

    assert len(raw_lines) == 2
    assert len(normalized_lines) == 2
    assert any('"provider_name":"fake_event_primary"' in line for line in raw_lines)
    assert any('"provider_name":"fake_fundamentals_primary"' in line for line in raw_lines)


@pytest.mark.asyncio
async def test_polling_realtime_composition_still_works(tmp_path) -> None:
    registry = build_test_provider_registry(evidence_store=LocalEvidenceStore(tmp_path), symbols=["AAPL"], polling_interval_seconds=0)
    realtime = registry.resolve(ProviderCapability.REALTIME_STREAM)

    stream = realtime.stream_quotes(["AAPL"])
    quote = await stream.__anext__()

    assert isinstance(quote, QuoteSnapshot)
    assert quote.symbol == "AAPL"
    assert quote.meta.provider_name == "fake_market_primary"

    await realtime.close()


@pytest.mark.asyncio
async def test_offline_only_behavior_remains_true(tmp_path, monkeypatch) -> None:
    def fail_if_network(*args, **kwargs):
        raise AssertionError("network access is not allowed")

    monkeypatch.setattr(socket, "create_connection", fail_if_network)

    registry = build_test_provider_registry(evidence_store=LocalEvidenceStore(tmp_path))
    quote_provider = registry.resolve(ProviderCapability.MARKET_DATA)
    quote = await quote_provider.get_quote("AAPL")

    assert quote_provider.provider_name == "fake_market_primary"
    assert quote.symbol == "AAPL"


@pytest.mark.asyncio
async def test_composed_registry_requires_no_live_adapter_or_network_behavior() -> None:
    registry = build_test_provider_registry()
    quote_provider = registry.resolve(ProviderCapability.MARKET_DATA)

    quote = await quote_provider.get_quote("AAPL")

    assert quote_provider.provider_name == "fake_market_primary"
    assert isinstance(quote, QuoteSnapshot)
    assert quote.symbol == "AAPL"
    assert quote.meta.provider_name == "fake_market_primary"