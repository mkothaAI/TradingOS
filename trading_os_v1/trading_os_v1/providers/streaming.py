from __future__ import annotations

import asyncio
import json
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from enum import Enum
from typing import Any, AsyncIterator, Iterable


class StreamEventType(str, Enum):
    HEALTH_SNAPSHOT = "HealthSnapshot"
    ELIGIBILITY_SNAPSHOT = "EligibilitySnapshot"
    EVIDENCE_SUMMARY = "EvidenceSummary"
    EVIDENCE_TIMELINE_SNAPSHOT = "EvidenceTimelineSnapshot"
    COMPOSITION_FALLBACK_SNAPSHOT = "CompositionFallbackSnapshot"
    COMPOSITION_OUTCOME = "CompositionOutcome"
    QUOTE_WATCH_SNAPSHOT = "QuoteWatchSnapshot"
    DIAGNOSTICS_SNAPSHOT = "DiagnosticsSnapshot"


def _to_jsonable(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if is_dataclass(value):
        return _to_jsonable(asdict(value))
    if hasattr(value, "model_dump"):
        return _to_jsonable(value.model_dump(mode="json"))
    if isinstance(value, dict):
        return {str(key): _to_jsonable(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, list):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, set):
        return sorted(_to_jsonable(item) for item in value)
    return value


def build_stream_event(event_type: StreamEventType, payload: Any) -> dict[str, Any]:
    return {
        "event_type": event_type.value,
        "payload": _to_jsonable(payload),
    }


def serialize_stream_event(event: dict[str, Any]) -> str:
    return json.dumps(_to_jsonable(event), sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def format_sse_message(event: dict[str, Any], *, event_id: str | None = None) -> str:
    lines: list[str] = []
    if event_id is not None:
        lines.append(f"id: {event_id}")
    lines.append(f"event: {event['event_type']}")
    lines.append(f"data: {serialize_stream_event(event['payload'])}")
    lines.append("")
    return "\n".join(lines) + "\n"


def parse_sse_message(message: str) -> dict[str, Any]:
    event_type = ""
    event_id: str | None = None
    data = "{}"
    for line in message.splitlines():
        if line.startswith("id: "):
            event_id = line[4:]
        elif line.startswith("event: "):
            event_type = line[7:]
        elif line.startswith("data: "):
            data = line[6:]
    return {
        "id": event_id,
        "event_type": event_type,
        "payload": json.loads(data),
    }


async def iter_sse_messages(
    events: Iterable[dict[str, Any]],
    *,
    event_id_prefix: str = "evt",
    delay_seconds: float = 0.0,
) -> AsyncIterator[str]:
    for index, event in enumerate(events, start=1):
        if delay_seconds > 0:
            await asyncio.sleep(delay_seconds)
        yield format_sse_message(event, event_id=f"{event_id_prefix}-{index}")