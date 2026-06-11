"""Fixtures for Event engine tests."""

from datetime import date, timedelta
import pytest
from backend.schemas.shared import RequestMeta


@pytest.fixture
def request_meta():
    return RequestMeta(request_id="REQ-EVT-001", as_of_date=date(2024, 1, 15))


@pytest.fixture
def ticker_list():
    return ["AAPL", "TSLA", "MSFT", "NOEVENT"]


@pytest.fixture
def event_config_full():
    return {
        "earnings_blackout_days_before": 5,
        "earnings_blackout_days_after": 3,
        "advisory_only": False,
    }


@pytest.fixture
def event_config_partial_before():
    return {"earnings_blackout_days_before": 5}


@pytest.fixture
def event_config_partial_after():
    return {"earnings_blackout_days_after": 2}


@pytest.fixture
def scheduled_events_mixed(request_meta):
    as_of = request_meta.as_of_date
    return {
        "AAPL": [
            {
                "event_type": "earnings",
                "event_date": as_of - timedelta(days=3),
                "source": "sec",
            },
            {
                "event_type": "dividend",
                "event_date": as_of + timedelta(days=10),
                "source": "issuer",
            },
        ],
        "TSLA": [
            {
                "event_type": "earnings",
                "event_date": as_of + timedelta(days=2),
                "source": "sec",
            },
            {
                "event_type": "split",
                "event_date": as_of + timedelta(days=1),
                "source": "issuer",
            },
        ],
        "MSFT": [
            {"event_type": None, "event_date": as_of, "source": "sec"},
            {
                "event_type": "macro",
                "event_date": as_of - timedelta(days=1),
                "source": "fed",
            },
            {
                "event_type": "earnings",
                "event_date": as_of + timedelta(days=5),
                "source": "sec",
            },
        ],
        # NOEVENT omitted to test no-events behavior
    }


@pytest.fixture
def scheduled_events_with_invalid():
    return {
        "AAPL": [
            {"event_type": "earnings", "event_date": None, "source": "sec"},
            {"event_type": "dividend", "source": "issuer"},
        ]
    }
