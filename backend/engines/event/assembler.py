"""Thin assembler for Phase 8 Event engine.

Orchestrates pure functions and formats response using contracts.
"""

from typing import Dict, List, Any
from datetime import date
from backend.engines.event.calc import evaluate_event_universe
from backend.schemas.models_responses import EventResponse
from backend.schemas.shared import RequestMeta, ResponseStatus, ErrorItem
from backend.schemas.decision_models import ScheduledEventItem, EventFlagsItem


def compute_event(
    ticker_list: List[str],
    scheduled_events: Dict[str, List[Dict[str, Any]]],
    as_of_date: date,
    event_config: Dict[str, Any],
) -> Dict[str, Dict[str, Any]]:
    return evaluate_event_universe(
        ticker_list, scheduled_events, as_of_date, event_config
    )


def build_event_response(
    event_result: Dict[str, Dict[str, Any]],
    meta: RequestMeta,
) -> EventResponse:
    status = ResponseStatus.OK
    errors: List[ErrorItem] = []

    # Convert to EventFlagsItem
    event_flags: Dict[str, EventFlagsItem] = {}
    for ticker, data in event_result.items():
        # convert dict events to ScheduledEventItem where possible
        ev_list = []
        for ev in data.get("events", []) or []:
            ev_list.append(
                ScheduledEventItem(
                    ticker=ticker,
                    event_type=ev.get("event_type") or "",
                    event_date=ev.get("event_date"),
                    source=ev.get("source"),
                )
            )

        event_flags[ticker] = EventFlagsItem(
            earnings_upcoming=data.get("earnings_upcoming", False),
            blackout=data.get("blackout", False),
            events=ev_list if ev_list else None,
        )

    return EventResponse(
        meta=meta, status=status, event_flags=event_flags, errors=errors
    )
