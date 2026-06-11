"""Pure functions for Phase 8 Event engine.

Deterministic, earnings-only blackout logic. See Phase 8 design.
"""

from datetime import date, timedelta
from typing import Dict, List, Any, Tuple


# Canonical config keys for v1
KNOWN_CONFIG_KEYS = {
    "earnings_blackout_days_before",
    "earnings_blackout_days_after",
    "advisory_only",
}

# Event type constant (v1: exact match)
EARNINGS_TYPE = "earnings"


def validate_event_config_keys(event_config: Dict[str, Any]) -> None:
    """Raise ValueError if unknown keys present."""
    if not event_config:
        return
    unknown = set(event_config.keys()) - KNOWN_CONFIG_KEYS
    if unknown:
        raise ValueError(f"Unknown event_config keys: {unknown}")


def _blackout_window_bounds(
    as_of_date: date, event_config: Dict[str, Any]
) -> Tuple[date, date]:
    """Compute inclusive blackout start and end dates.

    Missing sides are treated as 0 days.
    Returns (start_date, end_date).
    """
    before = event_config.get("earnings_blackout_days_before")
    after = event_config.get("earnings_blackout_days_after")

    before_days = int(before) if before is not None else 0
    after_days = int(after) if after is not None else 0

    start = as_of_date - timedelta(days=before_days)
    end = as_of_date + timedelta(days=after_days)
    return start, end


def _event_triggers_blackout(
    event: Dict[str, Any], as_of_date: date, event_config: Dict[str, Any]
) -> bool:
    """Return True if this event (dict) triggers earnings-only blackout.

    Rules:
    - Only events whose `event_type` == EARNINGS_TYPE trigger blackout.
    - Missing `event_date` => event cannot trigger blackout (skipped upstream by caller).
    - Partial config sides treated as 0.
    - Inclusive boundaries.
    """
    if not event:
        return False
    event_type = event.get("event_type")
    if event_type != EARNINGS_TYPE:
        return False
    event_date = event.get("event_date")
    if event_date is None:
        return False

    start, end = _blackout_window_bounds(as_of_date, event_config or {})
    return start <= event_date <= end


def evaluate_event_flags_for_ticker(
    ticker: str,
    events_for_ticker: List[Dict[str, Any]],
    as_of_date: date,
    event_config: Dict[str, Any],
) -> Dict[str, Any]:
    """Evaluate flags for a single ticker.

    Returns dict with keys: earnings_upcoming, blackout, events, event_present
    - events: list of valid events (skipping those without event_date)
    - sorting: event_date asc, source asc, event_type asc
    """
    validate_event_config_keys(event_config)

    earnings_upcoming = False
    blackout = False
    valid_events: List[Dict[str, Any]] = []

    if not events_for_ticker:
        return {
            "earnings_upcoming": False,
            "blackout": False,
            "events": [],
            "event_present": False,
        }

    for ev in events_for_ticker:
        # Must have event_date to be considered valid; skip otherwise
        ev_date = ev.get("event_date")
        if ev_date is None:
            # skip invalid event
            continue

        # treat missing type as generic (never earnings)
        if ev.get("event_type") == EARNINGS_TYPE:
            earnings_upcoming = True

        # Check blackout only for earnings events
        if _event_triggers_blackout(ev, as_of_date, event_config or {}):
            blackout = True

        # include valid event
        valid_events.append(ev)

    # deterministic sorting: date asc, source asc, event_type asc
    valid_events.sort(
        key=lambda e: (
            e.get("event_date"),
            e.get("source") or "",
            e.get("event_type") or "",
        )
    )

    return {
        "earnings_upcoming": earnings_upcoming,
        "blackout": blackout,
        "events": valid_events,
        "event_present": len(valid_events) > 0,
    }


def evaluate_event_universe(
    ticker_list: List[str],
    scheduled_events: Dict[str, List[Dict[str, Any]]],
    as_of_date: date,
    event_config: Dict[str, Any],
) -> Dict[str, Dict[str, Any]]:
    """Evaluate event flags for all tickers in `ticker_list`.

    - `ticker_list` is authoritative; every ticker in it will have a result.
    - scheduled_events may omit tickers; those will receive default flags.
    """
    validate_event_config_keys(event_config)

    results: Dict[str, Dict[str, Any]] = {}
    for ticker in ticker_list:
        events = scheduled_events.get(ticker) if scheduled_events else None
        res = evaluate_event_flags_for_ticker(
            ticker, events or [], as_of_date, event_config or {}
        )
        results[ticker] = res

    return results
