from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.engines.decision.producer import build_runtime_decision_inputs, build_runtime_decision_response
from backend.schemas.decision_models import DecisionInputs, EventFlagsItem, TechnicalIndicatorsItem, TechnicalSignalsItem
from backend.schemas.models_responses import EventResponse, FundamentalResponse, RiskResponse, TechnicalResponse
from backend.schemas.shared import FundamentalItem, RequestMeta, RiskMetrics, SizeInfo


def test_runtime_decision_inputs_are_assembled_from_typed_engine_responses() -> None:
    technical_response = TechnicalResponse(
        meta=RequestMeta(request_id="req-1", as_of_date=date(2026, 5, 25)),
        status="OK",
        indicators={"AAPL": TechnicalIndicatorsItem(atr=2.5, ma={10: 100.0})},
        signals={"AAPL": TechnicalSignalsItem(ma_cross=1, candle_classification="bullish")},
        errors=[],
    )
    fundamental_response = FundamentalResponse(
        meta=RequestMeta(request_id="req-1", as_of_date=date(2026, 5, 25)),
        status="OK",
        results={"AAPL": FundamentalItem(fundamental_pass=True, reasons=["ROE_OK"])},
        errors=[],
    )
    risk_response = RiskResponse(
        meta=RequestMeta(request_id="req-1", as_of_date=date(2026, 5, 25)),
        status="OK",
        risk_metrics=RiskMetrics(),
        size_info={"AAPL": SizeInfo(allowed_qty=10)},
        errors=[],
    )
    event_response = EventResponse(
        meta=RequestMeta(request_id="req-1", as_of_date=date(2026, 5, 25)),
        status="OK",
        event_flags={"AAPL": EventFlagsItem(blackout=False, earnings_upcoming=True)},
        errors=[],
    )

    decision_inputs = build_runtime_decision_inputs(
        "AAPL",
        technical_response,
        fundamental_response,
        risk_response,
        event_response,
    )

    assert isinstance(decision_inputs, DecisionInputs)
    assert decision_inputs.technical_signals["AAPL"].ma_cross == 1
    assert decision_inputs.technical_indicators is not None
    assert decision_inputs.technical_indicators["AAPL"].atr == 2.5
    assert decision_inputs.fundamental_results["AAPL"].fundamental_pass is True
    assert decision_inputs.risk_assessment["AAPL"].allowed_qty == 10
    assert decision_inputs.event_flags["AAPL"].earnings_upcoming is True


def test_runtime_decision_response_accepts_typed_decision_inputs() -> None:
    technical_response = TechnicalResponse(
        meta=RequestMeta(request_id="req-2", as_of_date=date(2026, 5, 25)),
        status="OK",
        indicators={"AAPL": TechnicalIndicatorsItem(atr=2.5)},
        signals={"AAPL": TechnicalSignalsItem(ma_cross=1)},
        errors=[],
    )
    fundamental_response = FundamentalResponse(
        meta=RequestMeta(request_id="req-2", as_of_date=date(2026, 5, 25)),
        status="OK",
        results={"AAPL": FundamentalItem(fundamental_pass=True, reasons=[])},
        errors=[],
    )
    risk_response = RiskResponse(
        meta=RequestMeta(request_id="req-2", as_of_date=date(2026, 5, 25)),
        status="OK",
        risk_metrics=RiskMetrics(),
        size_info={"AAPL": SizeInfo(allowed_qty=5)},
        errors=[],
    )
    event_response = EventResponse(
        meta=RequestMeta(request_id="req-2", as_of_date=date(2026, 5, 25)),
        status="OK",
        event_flags={"AAPL": EventFlagsItem(blackout=False)},
        errors=[],
    )

    decision_inputs = build_runtime_decision_inputs(
        "AAPL",
        technical_response,
        fundamental_response,
        risk_response,
        event_response,
    )

    response = build_runtime_decision_response(
        RequestMeta(request_id="req-2", as_of_date=date(2026, 5, 25)),
        "AAPL",
        decision_inputs,
    )

    assert response.decisions["AAPL"].decision == "BUY_CANDIDATE"
