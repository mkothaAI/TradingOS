from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from trading_os_v1.providers.schemas import (
    NormalizedProviderEvidenceRecord,
    ProviderCapability,
    ProviderMeta,
    RawProviderEvidenceRecord,
)


UTC_NOW = datetime(2024, 1, 15, 15, 30, tzinfo=timezone.utc)


def test_raw_provider_evidence_round_trip() -> None:
    meta = ProviderMeta(provider_name="fake_news", source_id="news-1", received_at=UTC_NOW)
    record = RawProviderEvidenceRecord(
        evidence_id="raw-1",
        provider_name="fake_news",
        capability=ProviderCapability.NEWS,
        symbol="AAPL",
        source_id="news-1",
        fetched_at=UTC_NOW,
        payload={"headline": "Example", "symbols": ["AAPL"]},
        meta=meta,
    )

    restored = RawProviderEvidenceRecord.model_validate(record.model_dump())

    assert restored == record
    assert restored.meta.provider_name == "fake_news"
    assert restored.payload["headline"] == "Example"


def test_normalized_provider_evidence_round_trip_and_linkage() -> None:
    record = NormalizedProviderEvidenceRecord(
        evidence_id="normalized-1",
        provider_name="fake_news",
        capability=ProviderCapability.NEWS,
        symbol="AAPL",
        source_id="news-1",
        fetched_at=UTC_NOW,
        normalized_payload={"news_id": "news-1", "title": "Example"},
        raw_evidence_id="raw-1",
    )

    restored = NormalizedProviderEvidenceRecord.model_validate(record.model_dump())

    assert restored == record
    assert restored.raw_evidence_id == "raw-1"
    assert restored.normalized_payload["news_id"] == "news-1"


@pytest.mark.parametrize(
    "record_cls,payload",
    [
        (RawProviderEvidenceRecord, {"evidence_id": "raw-1", "capability": ProviderCapability.NEWS, "fetched_at": UTC_NOW, "payload": {}, "meta": ProviderMeta(provider_name="fake_news", received_at=UTC_NOW)}),
        (NormalizedProviderEvidenceRecord, {"evidence_id": "normalized-1", "capability": ProviderCapability.NEWS, "fetched_at": UTC_NOW, "normalized_payload": {}, "raw_evidence_id": "raw-1"}),
    ],
)
def test_evidence_records_require_provider_name(record_cls, payload) -> None:
    with pytest.raises(ValidationError):
        record_cls.model_validate(payload)


def test_rejects_naive_timestamps() -> None:
    naive = datetime(2024, 1, 15, 15, 30)
    meta = ProviderMeta(provider_name="fake_news", source_id="news-1", received_at=UTC_NOW)

    with pytest.raises(ValidationError):
        RawProviderEvidenceRecord(
            evidence_id="raw-1",
            provider_name="fake_news",
            capability=ProviderCapability.NEWS,
            symbol="AAPL",
            source_id="news-1",
            fetched_at=naive,
            payload={"headline": "Example"},
            meta=meta,
        )


def test_rejects_malformed_payload_shapes() -> None:
    meta = ProviderMeta(provider_name="fake_news", source_id="news-1", received_at=UTC_NOW)

    with pytest.raises(ValidationError):
        RawProviderEvidenceRecord(
            evidence_id="raw-1",
            provider_name="fake_news",
            capability=ProviderCapability.NEWS,
            symbol="AAPL",
            source_id="news-1",
            fetched_at=UTC_NOW,
            payload=["not", "a", "dict"],
            meta=meta,
        )

    with pytest.raises(ValidationError):
        NormalizedProviderEvidenceRecord(
            evidence_id="normalized-1",
            provider_name="fake_news",
            capability=ProviderCapability.NEWS,
            symbol="AAPL",
            source_id="news-1",
            fetched_at=UTC_NOW,
            normalized_payload=["not", "a", "dict"],
            raw_evidence_id="raw-1",
        )
