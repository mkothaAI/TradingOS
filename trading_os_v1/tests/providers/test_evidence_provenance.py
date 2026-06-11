from __future__ import annotations

from datetime import datetime, timezone

import pytest

from trading_os_v1.providers.evidence_artifacts import create_provider_evidence_artifact, verify_provider_evidence_artifact
from trading_os_v1.providers.evidence_provenance import (
    attach_provider_evidence_provenance,
    build_provider_evidence_provenance,
)
from trading_os_v1.providers.schemas import (
    NormalizedProviderEvidenceRecord,
    ProviderCapability,
    ProviderMeta,
    RawProviderEvidenceRecord,
)


UTC_NOW = datetime(2024, 1, 15, 15, 30, tzinfo=timezone.utc)


def _raw_record() -> RawProviderEvidenceRecord:
    return RawProviderEvidenceRecord(
        evidence_id="raw-1",
        provider_name="fake_news",
        capability=ProviderCapability.NEWS,
        symbol="AAPL",
        source_id="news-1",
        fetched_at=UTC_NOW,
        payload={"headline": "Example", "symbols": ["AAPL"]},
        meta=ProviderMeta(provider_name="fake_news", source_id="news-1", received_at=UTC_NOW),
    )


def _normalized_record() -> NormalizedProviderEvidenceRecord:
    return NormalizedProviderEvidenceRecord(
        evidence_id="normalized-1",
        provider_name="fake_news",
        capability=ProviderCapability.NEWS,
        symbol="AAPL",
        source_id="news-1",
        fetched_at=UTC_NOW,
        normalized_payload={"headline": "Example", "score": 0.5},
        raw_evidence_id="raw-1",
    )


def test_raw_to_normalized_linkage_preservation() -> None:
    provenance = build_provider_evidence_provenance(_raw_record(), _normalized_record())

    assert provenance.raw_record.evidence_id == "raw-1"
    assert provenance.normalized_record is not None
    assert provenance.normalized_record.raw_evidence_id == provenance.raw_record.evidence_id
    assert verify_provider_evidence_artifact(provenance.raw_artifact, provenance.raw_record)
    assert provenance.normalized_artifact is not None
    assert verify_provider_evidence_artifact(provenance.normalized_artifact, provenance.normalized_record)


def test_provenance_chain_is_deterministic() -> None:
    provenance_one = build_provider_evidence_provenance(_raw_record(), _normalized_record())
    provenance_two = build_provider_evidence_provenance(_raw_record(), _normalized_record())

    assert provenance_one.chain_id == provenance_two.chain_id
    assert provenance_one.raw_artifact.descriptor.sha256 == provenance_two.raw_artifact.descriptor.sha256
    assert provenance_one.normalized_artifact is not None
    assert provenance_two.normalized_artifact is not None
    assert provenance_one.normalized_artifact.descriptor.sha256 == provenance_two.normalized_artifact.descriptor.sha256


def test_provenance_rejects_missing_or_malformed_linkage() -> None:
    malformed_normalized = NormalizedProviderEvidenceRecord(
        evidence_id="normalized-1",
        provider_name="fake_news",
        capability=ProviderCapability.NEWS,
        symbol="AAPL",
        source_id="news-1",
        fetched_at=UTC_NOW,
        normalized_payload={"headline": "Example"},
        raw_evidence_id="raw-999",
    )

    with pytest.raises(ValueError):
        build_provider_evidence_provenance(_raw_record(), malformed_normalized)


def test_provenance_attaches_trace_fields_to_adapter_outputs() -> None:
    provenance = build_provider_evidence_provenance(_raw_record(), _normalized_record())
    target = type("Target", (), {})()

    attach_provider_evidence_provenance(target, provenance)

    assert target.raw_evidence_id == "raw-1"
    assert target.normalized_evidence_id == "normalized-1"
    assert target.provenance_chain_id == provenance.chain_id
    assert target.raw_artifact_sha256 == provenance.raw_artifact.descriptor.sha256
    assert target.normalized_artifact_sha256 == provenance.normalized_artifact.descriptor.sha256


def test_artifact_generation_from_adapter_evidence_records() -> None:
    raw_record = _raw_record()
    artifact = create_provider_evidence_artifact(raw_record)

    assert artifact.descriptor.evidence_id == raw_record.evidence_id
    assert artifact.descriptor.sha256
    assert verify_provider_evidence_artifact(artifact, raw_record)