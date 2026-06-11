from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .evidence_artifacts import ProviderEvidenceArtifact, create_provider_evidence_artifact
from .schemas import NormalizedProviderEvidenceRecord, RawProviderEvidenceRecord


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _stable_digest(value: Any) -> str:
    return hashlib.sha256(_stable_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ProviderEvidenceProvenance:
    raw_record: RawProviderEvidenceRecord
    raw_artifact: ProviderEvidenceArtifact
    normalized_record: NormalizedProviderEvidenceRecord | None = None
    normalized_artifact: ProviderEvidenceArtifact | None = None
    chain_id: str = ""


def _validate_linkage(
    raw_record: RawProviderEvidenceRecord,
    normalized_record: NormalizedProviderEvidenceRecord | None,
) -> None:
    if normalized_record is None:
        return
    if normalized_record.raw_evidence_id != raw_record.evidence_id:
        raise ValueError("normalized evidence must reference the raw evidence_id")
    if normalized_record.provider_name != raw_record.provider_name:
        raise ValueError("normalized evidence must preserve provider_name")
    if normalized_record.capability != raw_record.capability:
        raise ValueError("normalized evidence must preserve capability")
    if normalized_record.symbol != raw_record.symbol:
        raise ValueError("normalized evidence must preserve symbol")
    if normalized_record.source_id != raw_record.source_id:
        raise ValueError("normalized evidence must preserve source_id")


def build_provider_evidence_provenance(
    raw_record: RawProviderEvidenceRecord,
    normalized_record: NormalizedProviderEvidenceRecord | None = None,
    base_dir: str | Path | None = None,
) -> ProviderEvidenceProvenance:
    _validate_linkage(raw_record, normalized_record)
    raw_artifact = create_provider_evidence_artifact(raw_record, base_dir=base_dir)
    normalized_artifact = (
        create_provider_evidence_artifact(normalized_record, base_dir=base_dir)
        if normalized_record is not None
        else None
    )
    chain_fingerprint = {
        "raw_evidence_id": raw_record.evidence_id,
        "raw_sha256": raw_artifact.descriptor.sha256,
        "normalized_evidence_id": normalized_record.evidence_id if normalized_record is not None else None,
        "normalized_sha256": normalized_artifact.descriptor.sha256 if normalized_artifact is not None else None,
    }
    chain_id = f"prov-{_stable_digest(chain_fingerprint)[:24]}"
    return ProviderEvidenceProvenance(
        raw_record=raw_record,
        raw_artifact=raw_artifact,
        normalized_record=normalized_record,
        normalized_artifact=normalized_artifact,
        chain_id=chain_id,
    )


def attach_provider_evidence_provenance(target: Any, provenance: ProviderEvidenceProvenance) -> Any:
    object.__setattr__(target, "provenance_chain_id", provenance.chain_id)
    object.__setattr__(target, "raw_evidence_id", provenance.raw_record.evidence_id)
    object.__setattr__(target, "raw_artifact_sha256", provenance.raw_artifact.descriptor.sha256)
    object.__setattr__(target, "raw_artifact_path", provenance.raw_artifact.descriptor.artifact_path.as_posix())
    if provenance.normalized_record is not None:
        object.__setattr__(target, "normalized_evidence_id", provenance.normalized_record.evidence_id)
    if provenance.normalized_artifact is not None:
        object.__setattr__(target, "normalized_artifact_sha256", provenance.normalized_artifact.descriptor.sha256)
        object.__setattr__(target, "normalized_artifact_path", provenance.normalized_artifact.descriptor.artifact_path.as_posix())
    object.__setattr__(target, "evidence_provenance", provenance)
    return target