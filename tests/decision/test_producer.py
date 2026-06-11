from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.engines.decision.producer import build_runtime_decision_response
from backend.schemas.decision_models import DecisionItem
from backend.schemas.models_responses import DecisionResponse
from backend.schemas.shared import RequestMeta


def test_runtime_decision_producer_emits_typed_response() -> None:
    response = build_runtime_decision_response(
        RequestMeta(request_id="req-1", as_of_date=date(2026, 5, 25)),
        "AAPL",
        {
            "technical_signals": {"tech_entry": 1},
            "fundamental_pass": True,
            "risk_assessment": {"size_info": {"allowed_qty": 10}},
            "event_flags": {"blackout": False},
            "portfolio_state": {"existing_position": False},
        },
    )

    assert isinstance(response, DecisionResponse)
    assert isinstance(response.decisions["AAPL"], DecisionItem)
    assert response.decisions["AAPL"].decision == "BUY_CANDIDATE"


def test_runtime_decision_producer_can_emit_hold() -> None:
    response = build_runtime_decision_response(
        RequestMeta(request_id="req-2", as_of_date=date(2026, 5, 25)),
        "AAPL",
        {
            "technical_signals": {"tech_entry": 0},
            "fundamental_pass": True,
            "risk_assessment": {"size_info": {"allowed_qty": 10}},
            "event_flags": {"blackout": False},
            "portfolio_state": {"existing_position": False},
        },
    )

    assert response.decisions["AAPL"].decision == "HOLD"
