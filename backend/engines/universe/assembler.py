"""Thin deterministic assembler for Universe engine (Phase 6).

No AI inference. No portfolio construction logic.
"""
from typing import Dict, List, Any, Optional
from backend.engines.universe.calc import build_eligible_universe
from backend.schemas.models_responses import UniverseResponse, UniverseItem, UniverseStats
from backend.schemas.shared import RequestMeta, ResponseStatus, ErrorItem


def assemble_universe_request(ticker_metadata: List[Dict], allowed_markets: List[str], max_universe_size: Optional[int] = None) -> Dict[str, Any]:
    """Extract Universe engine inputs."""
    return {
        "ticker_metadata": ticker_metadata,
        "allowed_markets": allowed_markets,
        "max_universe_size": max_universe_size,
    }


def compute_universe(
    ticker_metadata: List[Dict[str, Any]],
    allowed_markets: List[str],
    max_universe_size: Optional[int] = None,
) -> Dict[str, Any]:
    """Orchestrate universe filtering (pure deterministic)."""
    return build_eligible_universe(ticker_metadata, allowed_markets, max_universe_size)


def build_universe_response(
    universe_result: Dict[str, Any],
    meta: RequestMeta,
) -> UniverseResponse:
    """Format universe output into UniverseResponse contract."""
    status = ResponseStatus.OK if not universe_result.get("errors") else ResponseStatus.ERROR
    
    # Convert error dicts to ErrorItem objects
    errors = [
        ErrorItem(code=err.get("code", "UNKNOWN"), message=err.get("message", ""))
        for err in universe_result.get("errors", [])
    ]
    
    # Convert universe list to UniverseItem objects
    universe_items = [
        UniverseItem(ticker=item["ticker"], metadata=item)
        for item in universe_result.get("universe_list", [])
    ]
    
    # Convert stats dict to UniverseStats object
    stats_dict = universe_result.get("universe_stats", {})
    stats = UniverseStats(
        count=stats_dict.get("count", 0),
        total_market_cap=stats_dict.get("total_market_cap", 0),
        sector_exposures=stats_dict.get("sector_exposures", {}),
    )
    
    return UniverseResponse(
        meta=meta,
        status=status,
        universe_list=universe_items,
        universe_stats=stats,
        errors=errors,
    )
