"""Event engine tests (Phase 8)"""

from datetime import date, timedelta
import pytest
from backend.engines.event.calc import (
    evaluate_event_universe,
)
from backend.engines.event.assembler import compute_event, build_event_response


# Happy-path (4)


def test_no_events_scheduled(ticker_list):
    res = evaluate_event_universe(ticker_list, {}, date(2024, 1, 15), {})
    for t in ticker_list:
        assert res[t]["earnings_upcoming"] is False
        assert res[t]["blackout"] is False
        assert res[t]["events"] == []


def test_event_outside_blackout(ticker_list, scheduled_events_mixed):
    # AAPL dividend at +10 days should not cause blackout
    res = evaluate_event_universe(
        ticker_list,
        scheduled_events_mixed,
        date(2024, 1, 15),
        {"earnings_blackout_days_before": 2, "earnings_blackout_days_after": 2},
    )
    assert res["AAPL"]["blackout"] is False
    assert any(e["event_type"] == "dividend" for e in res["AAPL"]["events"])


def test_empty_config(ticker_list, scheduled_events_mixed):
    # missing sides treated as 0
    res = evaluate_event_universe(
        ticker_list, scheduled_events_mixed, date(2024, 1, 15), {}
    )
    # only events on as_of_date cause blackout
    # MSFT has an event on as_of_date (event_type None) -> not earnings => no blackout
    for t in ticker_list:
        assert res[t]["blackout"] is False


def test_earnings_upcoming_flag(scheduled_events_mixed):
    res = evaluate_event_universe(
        ["AAPL", "TSLA", "MSFT"], scheduled_events_mixed, date(2024, 1, 15), {}
    )
    assert res["AAPL"]["earnings_upcoming"] is True
    assert res["TSLA"]["earnings_upcoming"] is True
    assert res["MSFT"]["earnings_upcoming"] is True


# Blackout logic (6)


def test_earnings_within_blackout_before(
    request_meta, ticker_list, scheduled_events_mixed, event_config_full
):
    as_of = request_meta.as_of_date
    # AAPL earnings at as_of -3, before=5 -> blackout
    res = evaluate_event_universe(
        ticker_list, scheduled_events_mixed, as_of, event_config_full
    )
    assert res["AAPL"]["blackout"] is True


def test_earnings_within_blackout_after(
    request_meta, ticker_list, scheduled_events_mixed, event_config_full
):
    as_of = request_meta.as_of_date
    # TSLA earnings at as_of +2, after=3 -> blackout
    res = evaluate_event_universe(
        ticker_list, scheduled_events_mixed, as_of, event_config_full
    )
    assert res["TSLA"]["blackout"] is True


def test_earnings_boundary_before(request_meta, scheduled_events_mixed):
    as_of = request_meta.as_of_date
    events = {
        "X": [
            {
                "event_type": "earnings",
                "event_date": as_of - timedelta(days=5),
                "source": "sec",
            }
        ]
    }
    res = evaluate_event_universe(
        ["X"], events, as_of, {"earnings_blackout_days_before": 5}
    )
    assert res["X"]["blackout"] is True


def test_earnings_boundary_after(request_meta):
    as_of = request_meta.as_of_date
    events = {
        "X": [
            {
                "event_type": "earnings",
                "event_date": as_of + timedelta(days=2),
                "source": "sec",
            }
        ]
    }
    res = evaluate_event_universe(
        ["X"], events, as_of, {"earnings_blackout_days_after": 2}
    )
    assert res["X"]["blackout"] is True


def test_partial_config_before_only(request_meta):
    as_of = request_meta.as_of_date
    events = {
        "X": [
            {
                "event_type": "earnings",
                "event_date": as_of - timedelta(days=3),
                "source": "sec",
            }
        ]
    }
    # after missing -> treated as 0 -> window = [as_of -5, as_of]
    res = evaluate_event_universe(
        ["X"], events, as_of, {"earnings_blackout_days_before": 5}
    )
    assert res["X"]["blackout"] is True


def test_partial_config_after_only(request_meta):
    as_of = request_meta.as_of_date
    events = {
        "X": [
            {
                "event_type": "earnings",
                "event_date": as_of + timedelta(days=1),
                "source": "sec",
            }
        ]
    }
    # before missing -> treated as 0 -> window = [as_of, as_of + 2]
    res = evaluate_event_universe(
        ["X"], events, as_of, {"earnings_blackout_days_after": 2}
    )
    assert res["X"]["blackout"] is True


# Event-type isolation (3)


def test_dividend_does_not_trigger_blackout(request_meta):
    as_of = request_meta.as_of_date
    events = {
        "A": [{"event_type": "dividend", "event_date": as_of, "source": "issuer"}]
    }
    res = evaluate_event_universe(
        ["A"],
        events,
        as_of,
        {"earnings_blackout_days_before": 1, "earnings_blackout_days_after": 1},
    )
    assert res["A"]["blackout"] is False


def test_split_does_not_trigger_blackout(request_meta):
    as_of = request_meta.as_of_date
    events = {"A": [{"event_type": "split", "event_date": as_of, "source": "issuer"}]}
    res = evaluate_event_universe(
        ["A"],
        events,
        as_of,
        {"earnings_blackout_days_before": 1, "earnings_blackout_days_after": 1},
    )
    assert res["A"]["blackout"] is False


def test_macro_event_does_not_trigger_blackout(request_meta):
    as_of = request_meta.as_of_date
    events = {"A": [{"event_type": "macro", "event_date": as_of, "source": "fed"}]}
    res = evaluate_event_universe(
        ["A"],
        events,
        as_of,
        {"earnings_blackout_days_before": 1, "earnings_blackout_days_after": 1},
    )
    assert res["A"]["blackout"] is False


# Event presence & ordering (2)


def test_event_present_flag(scheduled_events_mixed):
    res = evaluate_event_universe(
        ["AAPL"], scheduled_events_mixed, date(2024, 1, 15), {}
    )
    assert res["AAPL"]["event_present"] is True


def test_event_list_deterministic_order(request_meta):
    as_of = request_meta.as_of_date
    events = {
        "A": [
            {"event_type": "b", "event_date": as_of, "source": "b"},
            {"event_type": "a", "event_date": as_of, "source": "a"},
            {"event_type": "a", "event_date": as_of, "source": "b"},
        ]
    }
    res = evaluate_event_universe(["A"], events, as_of, {})
    evs = res["A"]["events"]
    # expected order: (date,a,a),(date,a,b),(date,b,a) based on source then event_type
    assert evs[0]["source"] == "a"
    assert evs[1]["source"] == "b"


# Missing data & fail-closed (2)


def test_missing_event_date_skips():
    res = evaluate_event_universe(
        ["A"],
        {"A": [{"event_type": "earnings", "event_date": None}]},
        date(2024, 1, 15),
        {},
    )
    assert res["A"]["events"] == []


def test_invalid_event_type_treated_generic():
    as_of = date(2024, 1, 15)
    res = evaluate_event_universe(["A"], {"A": [{"event_date": as_of}]}, as_of, {})
    assert res["A"]["event_present"] is True
    assert res["A"]["earnings_upcoming"] is False


# Config validation (1)


def test_invalid_config_keys_raise_value_error():
    with pytest.raises(ValueError):
        evaluate_event_universe(["A"], {}, date(2024, 1, 15), {"unknown": 1})


# Complete ticker coverage (1)


def test_return_flags_for_all_requested_tickers(ticker_list, scheduled_events_mixed):
    res = evaluate_event_universe(
        ticker_list, scheduled_events_mixed, date(2024, 1, 15), {}
    )
    for t in ticker_list:
        assert t in res
        assert isinstance(res[t]["events"], list)


# Assembler contract test


def test_compute_and_build_response(ticker_list, scheduled_events_mixed, request_meta):
    result = compute_event(
        ticker_list, scheduled_events_mixed, request_meta.as_of_date, {}
    )
    response = build_event_response(result, request_meta)
    assert response.status.value == "OK"
    assert set(response.event_flags.keys()) == set(ticker_list)
