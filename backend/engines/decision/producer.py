from __future__ import annotations

from typing import Any, Dict

from backend.engines.decision.assembler import compute_decision
from backend.schemas.decision_models import (
    DecisionInputs,
    DecisionItem,
    FundamentalResultItem,
)
from backend.schemas.models_responses import (
    DecisionResponse,
    EventResponse,
    FundamentalResponse,
    RiskResponse,
    TechnicalResponse,
)
from backend.schemas.shared import RequestMeta, SizeInfo


def build_runtime_decision_inputs(
    ticker: str,
    technical_response: TechnicalResponse,
    fundamental_response: FundamentalResponse,
    risk_response: RiskResponse,
    event_response: EventResponse,
) -> DecisionInputs:
    """Build a typed DecisionInputs bundle from upstream engine responses.

    This is the domain/runtime boundary for the decision input layer. It keeps
    dashboard and UI concerns out of the decision path and only selects the
    ticker-specific typed inputs needed by the decision engine.
    """
    if ticker not in technical_response.signals:
        raise KeyError(f"Missing technical signals for ticker {ticker}")
    if ticker not in fundamental_response.results:
        raise KeyError(f"Missing fundamental results for ticker {ticker}")
    if ticker not in risk_response.size_info:
        raise KeyError(f"Missing risk sizing for ticker {ticker}")
    if ticker not in event_response.event_flags:
        raise KeyError(f"Missing event flags for ticker {ticker}")

    technical_signals = {ticker: technical_response.signals[ticker]}
    technical_indicators = None
    if ticker in technical_response.indicators:
        technical_indicators = {ticker: technical_response.indicators[ticker]}

    fundamental_item = fundamental_response.results[ticker]
    fundamental_results = {
        ticker: FundamentalResultItem(
            fundamental_pass=fundamental_item.fundamental_pass,
            reasons=list(fundamental_item.reasons),
        )
    }

    return DecisionInputs(
        technical_signals=technical_signals,
        technical_indicators=technical_indicators,
        fundamental_results=fundamental_results,
        risk_assessment={ticker: risk_response.size_info[ticker]},
        event_flags={ticker: event_response.event_flags[ticker]},
    )


def _decision_inputs_to_payload(ticker: str, decision_inputs: DecisionInputs) -> Dict[str, Any]:
    technical_signals = decision_inputs.technical_signals.get(ticker)
    fundamental_results = decision_inputs.fundamental_results.get(ticker)
    risk_assessment = decision_inputs.risk_assessment.get(ticker)
    event_flags = decision_inputs.event_flags.get(ticker)

    if technical_signals is None:
        raise KeyError(f"Missing technical signals in DecisionInputs for ticker {ticker}")
    if fundamental_results is None:
        raise KeyError(f"Missing fundamental results in DecisionInputs for ticker {ticker}")
    if risk_assessment is None:
        raise KeyError(f"Missing risk assessment in DecisionInputs for ticker {ticker}")
    if event_flags is None:
        raise KeyError(f"Missing event flags in DecisionInputs for ticker {ticker}")

    payload: Dict[str, Any] = {
        "technical_signals": technical_signals.model_dump(exclude_none=True),
        "fundamental_pass": fundamental_results.fundamental_pass,
        "risk_assessment": {"size_info": risk_assessment.model_dump(exclude_none=True)},
        "event_flags": event_flags.model_dump(exclude_none=True),
    }

    if decision_inputs.technical_indicators and ticker in decision_inputs.technical_indicators:
        payload["technical_indicators"] = decision_inputs.technical_indicators[ticker].model_dump(exclude_none=True)

    return payload


def build_runtime_decision_response(
    meta: RequestMeta,
    ticker: str,
    payload: Dict[str, Any] | DecisionInputs,
    pipeline_config: Dict[str, Any] | None = None,
) -> DecisionResponse:
    """Build a typed DecisionResponse from the deterministic decision engine.

    This is the upstream business-logic producer boundary for decision output.
    It returns authoritative schema models only.
    """
    if isinstance(payload, DecisionInputs):
        payload = _decision_inputs_to_payload(ticker, payload)

    decision_dict = compute_decision(payload, pipeline_config)
    size_info_payload = decision_dict.get("size_info")
    size_info = SizeInfo(**size_info_payload) if isinstance(size_info_payload, dict) else None
    decision_item = DecisionItem(
        ticker=ticker,
        decision=str(decision_dict.get("decision_token", "NO_TRADE")),
        size_info=size_info,
        reason_codes=list(decision_dict.get("reason_codes", [])),
        applied_rules=list(decision_dict.get("applied_rules", [])),
    )
    return DecisionResponse(meta=meta, status="OK", decisions={ticker: decision_item}, errors=[])
