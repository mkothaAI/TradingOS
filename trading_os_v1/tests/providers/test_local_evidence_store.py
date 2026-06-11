from __future__ import annotations

from datetime import datetime

import pytest

from trading_os_v1.providers.local_evidence_store import LocalEvidenceStore
from trading_os_v1.providers.schemas import ProviderMeta


@pytest.mark.asyncio
async def test_put_raw_then_get_raw(tmp_path) -> None:
    store = LocalEvidenceStore(tmp_path)
    meta = ProviderMeta(provider_name="fake_news", received_at=datetime(2024, 1, 15, 15, 30))

    evidence_id = await store.put_raw(
        capability="news",
        provider_name="fake_news",
        symbol="AAPL",
        fetched_at=datetime(2024, 1, 15, 15, 30),
        payload={"headline": "Example", "symbols": ["AAPL"]},
        meta=meta,
    )

    record = await store.get_raw(evidence_id)
    assert record is not None
    assert record["evidence_id"] == evidence_id
    assert record["provider_name"] == "fake_news"
    assert record["payload"]["headline"] == "Example"
    assert record["meta"]["provider_name"] == "fake_news"


@pytest.mark.asyncio
async def test_put_normalized_then_get_normalized(tmp_path) -> None:
    store = LocalEvidenceStore(tmp_path)
    raw_id = await store.put_raw(
        capability="fundamentals",
        provider_name="fake_fmp",
        symbol="MSFT",
        fetched_at=datetime(2024, 1, 15, 15, 30),
        payload={"symbol": "MSFT"},
        meta=ProviderMeta(provider_name="fake_fmp", received_at=datetime(2024, 1, 15, 15, 30)),
    )

    normalized_id = await store.put_normalized(
        capability="fundamentals",
        provider_name="fake_fmp",
        symbol="MSFT",
        fetched_at=datetime(2024, 1, 15, 15, 30),
        normalized_payload={"symbol": "MSFT", "market_cap": 100.0},
        raw_evidence_id=raw_id,
    )

    record = await store.get_normalized(normalized_id)
    assert record is not None
    assert record["evidence_id"] == normalized_id
    assert record["raw_evidence_id"] == raw_id
    assert record["normalized_payload"]["market_cap"] == 100.0


@pytest.mark.asyncio
async def test_normalized_links_back_to_raw(tmp_path) -> None:
    store = LocalEvidenceStore(tmp_path)
    raw_id = await store.put_raw(
        capability="event",
        provider_name="fake_finnhub",
        symbol="AAPL",
        fetched_at=datetime(2024, 1, 15, 15, 30),
        payload={"symbol": "AAPL", "date": "2024-01-31T00:00:00"},
        meta=ProviderMeta(provider_name="fake_finnhub", received_at=datetime(2024, 1, 15, 15, 30)),
    )
    normalized_id = await store.put_normalized(
        capability="event",
        provider_name="fake_finnhub",
        symbol="AAPL",
        fetched_at=datetime(2024, 1, 15, 15, 30),
        normalized_payload={"symbol": "AAPL", "event_type": "earnings"},
        raw_evidence_id=raw_id,
    )

    normalized_record = await store.get_normalized(normalized_id)
    raw_record = await store.get_raw(raw_id)

    assert normalized_record is not None
    assert raw_record is not None
    assert normalized_record["raw_evidence_id"] == raw_record["evidence_id"]
    assert raw_record["provider_name"] == normalized_record["provider_name"]


@pytest.mark.asyncio
async def test_append_only_behavior(tmp_path) -> None:
    store = LocalEvidenceStore(tmp_path)
    meta = ProviderMeta(provider_name="fake_market", received_at=datetime(2024, 1, 15, 15, 30))

    first_id = await store.put_raw(
        capability="market_data",
        provider_name="fake_market",
        symbol="AAPL",
        fetched_at=datetime(2024, 1, 15, 15, 30),
        payload={"last": 100.0},
        meta=meta,
    )
    second_id = await store.put_raw(
        capability="market_data",
        provider_name="fake_market",
        symbol="AAPL",
        fetched_at=datetime(2024, 1, 15, 15, 31),
        payload={"last": 101.0},
        meta=meta,
    )

    raw_path = tmp_path / "raw.jsonl"
    assert raw_path.exists()
    assert len(raw_path.read_text().strip().splitlines()) == 2
    assert first_id != second_id


@pytest.mark.asyncio
async def test_deterministic_offline_only_behavior(tmp_path) -> None:
    store = LocalEvidenceStore(tmp_path)
    meta = ProviderMeta(provider_name="fake_market", received_at=datetime(2024, 1, 15, 15, 30))

    first = await store.put_raw(
        capability="market_data",
        provider_name="fake_market",
        symbol="AAPL",
        fetched_at=datetime(2024, 1, 15, 15, 30),
        payload={"last": 100.0},
        meta=meta,
    )
    second = await store.put_raw(
        capability="market_data",
        provider_name="fake_market",
        symbol="AAPL",
        fetched_at=datetime(2024, 1, 15, 15, 30),
        payload={"last": 100.0},
        meta=meta,
    )

    assert first == second
    assert (tmp_path / "raw.jsonl").exists()


@pytest.mark.asyncio
async def test_multiple_records_for_same_symbol_provider(tmp_path) -> None:
    store = LocalEvidenceStore(tmp_path)
    meta = ProviderMeta(provider_name="fake_news", received_at=datetime(2024, 1, 15, 15, 30))

    first = await store.put_raw(
        capability="news",
        provider_name="fake_news",
        symbol="AAPL",
        fetched_at=datetime(2024, 1, 15, 15, 30),
        payload={"headline": "First"},
        meta=meta,
    )
    second = await store.put_raw(
        capability="news",
        provider_name="fake_news",
        symbol="AAPL",
        fetched_at=datetime(2024, 1, 15, 15, 31),
        payload={"headline": "Second"},
        meta=meta,
    )

    assert first != second
    assert (await store.get_raw(first))["payload"]["headline"] == "First"
    assert (await store.get_raw(second))["payload"]["headline"] == "Second"