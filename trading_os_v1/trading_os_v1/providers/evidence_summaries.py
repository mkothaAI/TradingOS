from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from trading_os_v1.providers.eligibility import summarize_provider_eligibility
from trading_os_v1.providers.local_evidence_store import LocalEvidenceStore
from trading_os_v1.providers.schemas import ProviderCapability


def _parse_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    return None


def _load_jsonl_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            records.append(json.loads(line))
    return records


def _init_bucket(provider_name: str, capability: str) -> dict[str, Any]:
    return {
        "provider_name": provider_name,
        "capability": capability,
        "raw_count": 0,
        "normalized_count": 0,
        "total_count": 0,
        "raw_evidence_ids": [],
        "normalized_evidence_ids": [],
        "raw_record_count": 0,
        "normalized_record_count": 0,
        "oldest_fetched_at": None,
        "newest_fetched_at": None,
        "symbols": set(),
    }


def _update_time_bounds(bucket: dict[str, Any], fetched_at: datetime | None) -> None:
    if fetched_at is None:
        return
    oldest = bucket["oldest_fetched_at"]
    newest = bucket["newest_fetched_at"]
    if oldest is None or fetched_at < oldest:
        bucket["oldest_fetched_at"] = fetched_at
    if newest is None or fetched_at > newest:
        bucket["newest_fetched_at"] = fetched_at


def _finalize_bucket(bucket: dict[str, Any]) -> dict[str, Any]:
    finalized = dict(bucket)
    finalized["symbols"] = sorted(bucket["symbols"])
    if finalized["oldest_fetched_at"] is not None:
        finalized["oldest_fetched_at"] = finalized["oldest_fetched_at"].isoformat()
    if finalized["newest_fetched_at"] is not None:
        finalized["newest_fetched_at"] = finalized["newest_fetched_at"].isoformat()
    finalized.pop("raw_record_count", None)
    finalized.pop("normalized_record_count", None)
    return finalized


def summarize_local_evidence(source: LocalEvidenceStore | str | Path) -> dict[str, dict[str, Any]]:
    base_dir = Path(source.base_dir if isinstance(source, LocalEvidenceStore) else source)
    raw_records = _load_jsonl_records(base_dir / "raw.jsonl")
    normalized_records = _load_jsonl_records(base_dir / "normalized.jsonl")

    summary: dict[str, dict[str, Any]] = defaultdict(dict)

    for record in raw_records:
        provider_name = str(record.get("provider_name") or "")
        capability = str(record.get("capability") or "")
        bucket = summary[provider_name].get(capability) or _init_bucket(provider_name, capability)
        bucket["raw_count"] += 1
        bucket["total_count"] += 1
        bucket["raw_evidence_ids"].append(record.get("evidence_id"))
        bucket["raw_record_count"] += 1
        bucket["symbols"].add(record.get("symbol"))
        _update_time_bounds(bucket, _parse_datetime(record.get("fetched_at")))
        summary[provider_name][capability] = bucket

    for record in normalized_records:
        provider_name = str(record.get("provider_name") or "")
        capability = str(record.get("capability") or "")
        bucket = summary[provider_name].get(capability) or _init_bucket(provider_name, capability)
        bucket["normalized_count"] += 1
        bucket["total_count"] += 1
        bucket["normalized_evidence_ids"].append(record.get("evidence_id"))
        bucket["normalized_record_count"] += 1
        bucket["symbols"].add(record.get("symbol"))
        _update_time_bounds(bucket, _parse_datetime(record.get("fetched_at")))
        summary[provider_name][capability] = bucket

    return {
        provider_name: {
            capability: _finalize_bucket(bucket)
            for capability, bucket in capability_map.items()
        }
        for provider_name, capability_map in summary.items()
    }


def correlate_health_and_evidence(
    health_summary: dict[str, dict[str, Any]],
    evidence_summary: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    correlated: dict[str, dict[str, Any]] = {}

    for provider_name, capability_map in evidence_summary.items():
        provider_result: dict[str, Any] = {}
        for capability, evidence_bucket in capability_map.items():
            health_bucket = health_summary.get(capability, {}).get("providers", {}).get(provider_name)
            health_status = health_bucket.get("status") if health_bucket else None
            degraded_or_down_count = evidence_bucket["total_count"] if health_status in {"degraded", "down"} else 0
            provider_result[capability] = {
                "provider_name": provider_name,
                "capability": capability,
                "total_evidence_count": evidence_bucket["total_count"],
                "oldest_fetched_at": evidence_bucket["oldest_fetched_at"],
                "newest_fetched_at": evidence_bucket["newest_fetched_at"],
                "health_status": health_status,
                "degraded_or_down_evidence_count": degraded_or_down_count,
            }
        correlated[provider_name] = provider_result

    return correlated


def summarize_evidence_by_capability(source: LocalEvidenceStore | str | Path) -> dict[str, dict[str, Any]]:
    evidence_summary = summarize_local_evidence(source)
    capability_summary: dict[str, dict[str, Any]] = defaultdict(dict)

    for provider_name, capability_map in evidence_summary.items():
        for capability, bucket in capability_map.items():
            aggregate = capability_summary.get(capability) or {
                "capability": capability,
                "providers": {},
                "total_count": 0,
                "oldest_fetched_at": None,
                "newest_fetched_at": None,
            }
            aggregate["providers"][provider_name] = bucket
            aggregate["total_count"] += bucket["total_count"]

            oldest = _parse_datetime(bucket["oldest_fetched_at"])
            newest = _parse_datetime(bucket["newest_fetched_at"])
            current_oldest = _parse_datetime(aggregate["oldest_fetched_at"])
            current_newest = _parse_datetime(aggregate["newest_fetched_at"])
            if oldest is not None and (current_oldest is None or oldest < current_oldest):
                aggregate["oldest_fetched_at"] = oldest.isoformat()
            if newest is not None and (current_newest is None or newest > current_newest):
                aggregate["newest_fetched_at"] = newest.isoformat()

            capability_summary[capability] = aggregate

    return dict(capability_summary)


def summarize_evidence_eligibility_view(
    health_summary: dict[str, dict[str, Any]],
    *,
    evidence_source: LocalEvidenceStore | str | Path | None = None,
    evidence_summary: dict[str, dict[str, Any]] | None = None,
) -> dict[str, dict[str, Any]]:
    if not isinstance(health_summary, dict):
        raise TypeError("health_summary must be a dict")
    if evidence_source is None and evidence_summary is None:
        raise ValueError("either evidence_source or evidence_summary must be provided")
    if evidence_summary is not None and not isinstance(evidence_summary, dict):
        raise TypeError("evidence_summary must be a dict when provided")

    resolved_evidence_summary = evidence_summary
    if resolved_evidence_summary is None:
        resolved_evidence_summary = summarize_local_evidence(evidence_source)

    return summarize_provider_eligibility(health_summary, resolved_evidence_summary)