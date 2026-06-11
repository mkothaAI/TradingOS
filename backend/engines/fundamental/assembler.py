"""Thin deterministic assembler for Fundamental engine (Phase 7).

No AI inference. No portfolio construction logic.
"""
from typing import Dict, List, Any
from backend.engines.fundamental.calc import evaluate_fundamental_universe
from backend.schemas.models_responses import FundamentalResponse, FundamentalItem
from backend.schemas.shared import RequestMeta, ResponseStatus, ErrorItem


def compute_fundamental(
    fundamental_data: Dict[str, Dict[str, Any]],
    fundamental_config: Dict[str, float],
) -> Dict[str, Dict[str, Any]]:
    """Orchestrate fundamental checks (pure deterministic)."""
    return evaluate_fundamental_universe(fundamental_data, fundamental_config)


def build_fundamental_response(
    fundamental_result: Dict[str, Dict[str, Any]],
    meta: RequestMeta,
) -> FundamentalResponse:
    """Format fundamental output into FundamentalResponse contract."""
    status = ResponseStatus.OK
    
    # Convert fundamental result to FundamentalItem objects
    results = {}
    for ticker, result in fundamental_result.items():
        results[ticker] = FundamentalItem(
            fundamental_pass=result["fundamental_pass"],
            reasons=result["reasons"],
        )
    
    return FundamentalResponse(
        meta=meta,
        status=status,
        results=results,
        errors=[],
    )
