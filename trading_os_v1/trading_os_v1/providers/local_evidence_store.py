from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from trading_os_v1.providers.evidence_store import EvidenceStore
from trading_os_v1.providers.schemas import ProviderMeta


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _stable_digest(value: Any) -> str:
    return hashlib.sha256(_stable_json(value).encode("utf-8")).hexdigest()


def _as_json_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, ProviderMeta):
        return value.model_dump(mode="json")
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {key: _as_json_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_as_json_value(item) for item in value]
    return value


@dataclass(frozen=True)
class _StoredEvidence:
    evidence_id: str
    kind: str
    capability: str
    provider_name: str
    symbol: str | None
    fetched_at: str
    meta: dict[str, Any]
    payload_key: str
    payload: dict[str, Any]
    raw_evidence_id: str | None = None


class LocalEvidenceStore(EvidenceStore):
    def __init__(self, base_dir: str | Path) -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._raw_path = self.base_dir / "raw.jsonl"
        self._normalized_path = self.base_dir / "normalized.jsonl"

    def _build_evidence_id(
        self,
        *,
        kind: str,
        capability: str,
        provider_name: str,
        symbol: str | None,
        fetched_at: datetime,
        payload: dict[str, Any],
        raw_evidence_id: str | None = None,
    ) -> str:
        fingerprint = {
            "kind": kind,
            "capability": capability,
            "provider_name": provider_name,
            "symbol": symbol,
            "fetched_at": fetched_at.isoformat(),
            "payload": _as_json_value(payload),
            "raw_evidence_id": raw_evidence_id,
        }
        return f"{kind}-{_stable_digest(fingerprint)[:24]}"

    def _append_record(self, path: Path, record: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(_stable_json(record))
            handle.write("\n")

    def _scan_records(self, path: Path, evidence_id: str) -> dict[str, Any] | None:
        if not path.exists():
            return None
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                record = json.loads(line)
                if record.get("evidence_id") == evidence_id:
                    return record
        return None

    async def put_raw(
        self,
        *,
        capability: str,
        provider_name: str,
        symbol: str | None,
        fetched_at: datetime,
        payload: dict[str, Any],
        meta: ProviderMeta,
    ) -> str:
        evidence_id = self._build_evidence_id(
            kind="raw",
            capability=capability,
            provider_name=provider_name,
            symbol=symbol,
            fetched_at=fetched_at,
            payload=payload,
        )
        record = {
            "evidence_id": evidence_id,
            "kind": "raw",
            "capability": capability,
            "provider_name": provider_name,
            "symbol": symbol,
            "fetched_at": fetched_at.isoformat(),
            "meta": meta.model_dump(mode="json"),
            "payload": _as_json_value(payload),
        }
        self._append_record(self._raw_path, record)
        return evidence_id

    async def put_normalized(
        self,
        *,
        capability: str,
        provider_name: str,
        symbol: str | None,
        fetched_at: datetime,
        normalized_payload: dict[str, Any],
        raw_evidence_id: str,
    ) -> str:
        evidence_id = self._build_evidence_id(
            kind="normalized",
            capability=capability,
            provider_name=provider_name,
            symbol=symbol,
            fetched_at=fetched_at,
            payload=normalized_payload,
            raw_evidence_id=raw_evidence_id,
        )
        record = {
            "evidence_id": evidence_id,
            "kind": "normalized",
            "capability": capability,
            "provider_name": provider_name,
            "symbol": symbol,
            "fetched_at": fetched_at.isoformat(),
            "raw_evidence_id": raw_evidence_id,
            "normalized_payload": _as_json_value(normalized_payload),
        }
        self._append_record(self._normalized_path, record)
        return evidence_id

    async def get_raw(self, evidence_id: str) -> dict[str, Any] | None:
        return self._scan_records(self._raw_path, evidence_id)

    async def get_normalized(self, evidence_id: str) -> dict[str, Any] | None:
        return self._scan_records(self._normalized_path, evidence_id)