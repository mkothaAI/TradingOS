from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Union

from .schemas import (
    NormalizedProviderEvidenceRecord,
    RawProviderEvidenceRecord,
)


ProviderEvidenceRecord = Union[RawProviderEvidenceRecord, NormalizedProviderEvidenceRecord]


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _evidence_dump(record: ProviderEvidenceRecord) -> dict[str, Any]:
    return record.model_dump(mode="json")


def serialize_provider_evidence(record: ProviderEvidenceRecord) -> str:
    return _canonical_json(_evidence_dump(record))


def hash_provider_evidence(record: ProviderEvidenceRecord) -> str:
    return hashlib.sha256(serialize_provider_evidence(record).encode("utf-8")).hexdigest()


def _artifact_directory(record: ProviderEvidenceRecord, base_dir: str | Path | None) -> Path:
    root = Path(base_dir) if base_dir is not None else Path()
    return root / record.provider_name / record.capability.value / record.kind


def build_provider_evidence_artifact_path(
    record: ProviderEvidenceRecord,
    base_dir: str | Path | None = None,
) -> Path:
    digest = hash_provider_evidence(record)
    return _artifact_directory(record, base_dir) / f"{record.evidence_id}-{digest}.json"


@dataclass(frozen=True)
class ProviderEvidenceArtifactDescriptor:
    evidence_id: str
    provider_name: str
    capability: str
    kind: str
    artifact_path: Path
    sha256: str
    created_at: datetime


@dataclass(frozen=True)
class ProviderEvidenceArtifact:
    descriptor: ProviderEvidenceArtifactDescriptor
    serialized_evidence: str


def create_provider_evidence_artifact(
    record: ProviderEvidenceRecord,
    base_dir: str | Path | None = None,
    created_at: datetime | None = None,
) -> ProviderEvidenceArtifact:
    digest = hash_provider_evidence(record)
    descriptor = ProviderEvidenceArtifactDescriptor(
        evidence_id=record.evidence_id,
        provider_name=record.provider_name,
        capability=record.capability.value,
        kind=record.kind,
        artifact_path=build_provider_evidence_artifact_path(record, base_dir),
        sha256=digest,
        created_at=created_at or datetime.now(timezone.utc),
    )
    return ProviderEvidenceArtifact(descriptor=descriptor, serialized_evidence=serialize_provider_evidence(record))


def verify_provider_evidence_artifact(
    artifact: ProviderEvidenceArtifact,
    record: ProviderEvidenceRecord,
) -> bool:
    expected_serialized = serialize_provider_evidence(record)
    expected_digest = hashlib.sha256(expected_serialized.encode("utf-8")).hexdigest()
    expected_path_name = f"{record.evidence_id}-{expected_digest}.json"
    expected_suffix = Path(record.provider_name) / record.capability.value / record.kind / expected_path_name

    return (
        artifact.serialized_evidence == expected_serialized
        and artifact.descriptor.sha256 == expected_digest
        and artifact.descriptor.artifact_path.as_posix().endswith(expected_suffix.as_posix())
        and artifact.descriptor.evidence_id == record.evidence_id
        and artifact.descriptor.provider_name == record.provider_name
        and artifact.descriptor.capability == record.capability.value
        and artifact.descriptor.kind == record.kind
    )