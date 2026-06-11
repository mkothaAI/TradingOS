from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

from trading_os_v1.providers.evidence_artifacts import (
    build_provider_evidence_artifact_path,
    create_provider_evidence_artifact,
    hash_provider_evidence,
    serialize_provider_evidence,
    verify_provider_evidence_artifact,
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
        payload={"headline": "Example", "symbols": ["AAPL"], "priority": 1},
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
        normalized_payload={"headline": "Example", "score": 0.75},
        raw_evidence_id="raw-1",
    )


def test_same_input_produces_same_hash() -> None:
    record_one = _raw_record()
    record_two = _raw_record()

    assert hash_provider_evidence(record_one) == hash_provider_evidence(record_two)
    assert serialize_provider_evidence(record_one) == serialize_provider_evidence(record_two)


def test_different_input_produces_different_hash() -> None:
    record_one = _raw_record()
    record_two = RawProviderEvidenceRecord(
        evidence_id="raw-2",
        provider_name="fake_news",
        capability=ProviderCapability.NEWS,
        symbol="AAPL",
        source_id="news-2",
        fetched_at=UTC_NOW,
        payload={"headline": "Different", "symbols": ["AAPL"]},
        meta=ProviderMeta(provider_name="fake_news", source_id="news-2", received_at=UTC_NOW),
    )

    assert hash_provider_evidence(record_one) != hash_provider_evidence(record_two)


def test_hash_is_stable_across_repeated_serialization() -> None:
    record_one = _raw_record()
    record_two = RawProviderEvidenceRecord(
        evidence_id="raw-1",
        provider_name="fake_news",
        capability=ProviderCapability.NEWS,
        symbol="AAPL",
        source_id="news-1",
        fetched_at=UTC_NOW,
        payload={"priority": 1, "symbols": ["AAPL"], "headline": "Example"},
        meta=ProviderMeta(provider_name="fake_news", source_id="news-1", received_at=UTC_NOW),
    )

    assert serialize_provider_evidence(record_one) == serialize_provider_evidence(record_two)
    assert hash_provider_evidence(record_one) == hash_provider_evidence(record_two)


def test_artifact_descriptor_path_is_stable_and_deterministic(tmp_path) -> None:
    record = _raw_record()

    artifact_one = create_provider_evidence_artifact(record, base_dir=tmp_path)
    artifact_two = create_provider_evidence_artifact(record, base_dir=tmp_path)

    expected_path = build_provider_evidence_artifact_path(record, base_dir=tmp_path)

    assert artifact_one.descriptor.artifact_path == expected_path
    assert artifact_two.descriptor.artifact_path == expected_path
    assert artifact_one.descriptor.artifact_path == artifact_two.descriptor.artifact_path
    assert artifact_one.descriptor.sha256 == artifact_two.descriptor.sha256


def test_verification_fails_on_tampered_payload_or_hash(tmp_path) -> None:
    record = _raw_record()
    artifact = create_provider_evidence_artifact(record, base_dir=tmp_path)

    tampered_payload = replace(artifact, serialized_evidence=artifact.serialized_evidence.replace("Example", "Tampered"))
    tampered_hash = replace(artifact, descriptor=replace(artifact.descriptor, sha256="0" * 64))

    assert verify_provider_evidence_artifact(artifact, record) is True
    assert verify_provider_evidence_artifact(tampered_payload, record) is False
    assert verify_provider_evidence_artifact(tampered_hash, record) is False


def test_artifact_creation_works_with_evidence_contract_models(tmp_path) -> None:
    raw_record = _raw_record()
    normalized_record = _normalized_record()

    raw_artifact = create_provider_evidence_artifact(raw_record, base_dir=tmp_path)
    normalized_artifact = create_provider_evidence_artifact(normalized_record, base_dir=tmp_path)

    assert raw_artifact.descriptor.evidence_id == raw_record.evidence_id
    assert normalized_artifact.descriptor.evidence_id == normalized_record.evidence_id
    assert raw_artifact.descriptor.kind == "raw"
    assert normalized_artifact.descriptor.kind == "normalized"
    assert verify_provider_evidence_artifact(raw_artifact, raw_record) is True
    assert verify_provider_evidence_artifact(normalized_artifact, normalized_record) is True