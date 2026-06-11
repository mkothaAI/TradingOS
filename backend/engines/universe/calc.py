"""Pure universe filtering logic (Phase 6).

All functions are deterministic, accept primitives/dicts only, and produce
deterministic outputs. No AI inference, no portfolio construction, no defaults assumed.
"""
from typing import List, Dict, Any, Optional


# Central, auditable exchange mapping (single source of truth)
EXCHANGE_MAP = {
    "US": {"NASDAQ", "NYSE", "AMEX", "OTC"},
}


def validate_required_fields(ticker_metadata: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter symbols missing critical fields: ticker, exchange, sector, market_cap, lot_size, tradable.
    Fail-closed: any missing/null field → exclude symbol (no defaults assumed).
    """
    required_fields = ["ticker", "exchange", "sector", "market_cap", "lot_size", "tradable"]
    valid = []
    for item in ticker_metadata:
        if all(item.get(field) is not None for field in required_fields):
            valid.append(item)
    return valid


def filter_tradable_symbols(ticker_metadata: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter: keep only symbols with tradable==True."""
    return [item for item in ticker_metadata if item.get("tradable") is True]


def filter_by_market(
    ticker_metadata: List[Dict[str, Any]],
    allowed_markets: List[str],
) -> List[Dict[str, Any]]:
    """
    Filter: keep symbols whose exchange is in allowed_markets.
    allowed_markets: e.g., ["US"]
    Uses central EXCHANGE_MAP for deterministic, auditable mappings.
    """
    allowed_exchanges = set()
    for market in allowed_markets:
        allowed_exchanges.update(EXCHANGE_MAP.get(market, set()))
    
    return [item for item in ticker_metadata if item.get("exchange") in allowed_exchanges]


def filter_by_lot_size(ticker_metadata: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter: keep lot_size > 0.
    NOTE: lot_size is a proxy for liquidity in v1 (no explicit volume/spread data in contracts).
    Phase 7+: consider volume-based filters if price/volume data added to contracts.
    """
    return [item for item in ticker_metadata if item.get("lot_size", 0) > 0]


def sort_by_market_cap_descending(ticker_metadata: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Sort by market_cap descending.
    Ties broken by ticker alphabetically (deterministic).
    """
    return sorted(
        ticker_metadata,
        key=lambda x: (-x.get("market_cap", 0), x.get("ticker", ""))
    )


def dedup_by_ticker(ticker_metadata: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicate tickers; keep first occurrence."""
    seen = set()
    result = []
    for item in ticker_metadata:
        ticker = item.get("ticker")
        if ticker not in seen:
            result.append(item)
            seen.add(ticker)
    return result


def apply_max_universe_size(
    ticker_metadata: List[Dict[str, Any]],
    max_universe_size: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Truncate universe to max_universe_size symbols.
    (Must be called after sorting by market_cap descending; keeps top N.)
    If max_universe_size is None, return all symbols.
    """
    if max_universe_size is None:
        return ticker_metadata
    return ticker_metadata[:max_universe_size]


def compute_universe_stats(universe: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute universe statistics: count, total market cap, sector distribution.
    Sector exposures sorted alphabetically for determinism.
    """
    total_market_cap = sum(item.get("market_cap", 0) for item in universe)
    sector_exposures = {}
    
    if total_market_cap > 0:
        # Collect sectors and compute exposures
        for sector in set(item.get("sector") for item in universe if item.get("sector")):
            sector_market_cap = sum(
                item.get("market_cap", 0) for item in universe if item.get("sector") == sector
            )
            sector_exposures[sector] = sector_market_cap / total_market_cap
    
    # Sort sector_exposures alphabetically for deterministic output
    sector_exposures = dict(sorted(sector_exposures.items()))
    
    return {
        "count": len(universe),
        "total_market_cap": total_market_cap,
        "sector_exposures": sector_exposures,
    }


def build_eligible_universe(
    ticker_metadata: List[Dict[str, Any]],
    allowed_markets: List[str],
    max_universe_size: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Build eligible universe by applying deterministic filters in sequence.
    
    Filter order (deterministic):
    1. Validate required fields (fail-closed for missing data).
    2. Filter tradable==True.
    3. Filter by market (allowed_markets → EXCHANGE_MAP).
    4. Filter by lot_size > 0 (v1 liquidity proxy).
    5. Dedup by ticker.
    6. Sort by market_cap descending (ties by ticker alphabetically).
    7. Truncate to max_universe_size if set.
    8. Compute stats.
    
    Returns {
        "universe_list": [...filtered tickers...],
        "universe_stats": {count, total_market_cap, sector_exposures},
        "errors": []
    }
    
    FUTURE WORK (Phase 7+):
    - Sector cap enforcement (portfolio construction logic).
    - Volume-based liquidity filters (requires volume data in contracts).
    - Price floor / price-range filters (requires price data in contracts).
    """
    errors = []
    
    # Apply filters in sequence
    universe = ticker_metadata
    universe = validate_required_fields(universe)
    universe = filter_tradable_symbols(universe)
    universe = filter_by_market(universe, allowed_markets)
    universe = filter_by_lot_size(universe)
    universe = dedup_by_ticker(universe)
    universe = sort_by_market_cap_descending(universe)
    universe = apply_max_universe_size(universe, max_universe_size)
    
    # Compute stats
    stats = compute_universe_stats(universe)
    
    # Error handling
    if not universe:
        errors.append({"code": "UNIVERSE_EMPTY", "message": "No eligible symbols after filters"})
    
    return {
        "universe_list": universe,
        "universe_stats": stats,
        "errors": errors,
    }
