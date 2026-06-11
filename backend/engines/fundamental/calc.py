"""Pure fundamental check logic (Phase 7).

All functions deterministic, accept primitives/dicts only, produce deterministic outputs.
No AI inference, no defaults assumed, no valuation modeling.
"""
from typing import Dict, List, Any, Tuple, Optional


# Canonical config keys (v1 scope: ROE, Net Margin, Debt/EBITDA only)
KNOWN_CONFIG_KEYS = {"min_roe", "min_net_margin", "max_debt_ebitda"}

# Canonical reason code order (from module-03 v1-safe rules)
CANONICAL_REASON_ORDER = {
    "ROE_FAIL": 0,
    "ROE_MISSING": 0,
    "MARGIN_FAIL": 1,
    "MARGIN_MISSING": 1,
    "DEBT_FAIL": 2,
    "DEBT_MISSING": 2,
}


def validate_config_keys(fundamental_config: Dict[str, float]) -> None:
    """
    Validate that config only contains known keys.
    Raises ValueError if unknown keys found (fail-safe).
    """
    unknown_keys = set(fundamental_config.keys()) - KNOWN_CONFIG_KEYS
    if unknown_keys:
        raise ValueError(
            f"Unknown config keys: {unknown_keys}. "
            f"Valid keys: {KNOWN_CONFIG_KEYS}"
        )


def check_roe_threshold(
    roe: Optional[float],
    min_roe: float,
) -> Tuple[bool, Optional[str]]:
    """
    Check if ROE >= min_roe.
    Returns (passed, reason_code).
    reason_code: None if passed, "ROE_FAIL" if failed check, "ROE_MISSING" if missing.
    """
    if roe is None:
        return False, "ROE_MISSING"
    if roe < min_roe:
        return False, "ROE_FAIL"
    return True, None


def check_net_margin_threshold(
    net_margin: Optional[float],
    min_net_margin: float,
) -> Tuple[bool, Optional[str]]:
    """
    Check if net_margin >= min_net_margin.
    Returns (passed, reason_code).
    reason_code: None if passed, "MARGIN_FAIL" if failed, "MARGIN_MISSING" if missing.
    """
    if net_margin is None:
        return False, "MARGIN_MISSING"
    if net_margin < min_net_margin:
        return False, "MARGIN_FAIL"
    return True, None


def check_debt_ebitda_ceiling(
    debt_ebitda: Optional[float],
    max_debt_ebitda: float,
) -> Tuple[bool, Optional[str]]:
    """
    Check if debt_ebitda <= max_debt_ebitda.
    Returns (passed, reason_code).
    reason_code: None if passed, "DEBT_FAIL" if failed, "DEBT_MISSING" if missing.
    """
    if debt_ebitda is None:
        return False, "DEBT_MISSING"
    if debt_ebitda > max_debt_ebitda:
        return False, "DEBT_FAIL"
    return True, None


def evaluate_fundamental_checks(
    ticker: str,
    fundamental_data_item: Dict[str, Any],
    fundamental_config: Dict[str, float],
) -> Dict[str, Any]:
    """
    Evaluate all configured fundamental checks for a single ticker.
    
    Args:
        ticker: stock symbol (for logging/tracing)
        fundamental_data_item: {field: value, ...} (e.g., {"roe": 0.15, "net_margin": 0.20})
        fundamental_config: {check_name: threshold, ...} (e.g., {"min_roe": 0.12})
    
    Returns:
        {
            "fundamental_pass": bool,
            "reasons": [reason codes in canonical order, empty if all passed]
        }
    
    Logic:
    - Validate config keys; raise ValueError if unknown keys found.
    - If config is empty, return pass (spec: "evaluate each configured threshold").
    - For each configured check:
      - Extract data from fundamental_data_item.
      - If data is None, add field-specific MISSING code (e.g., ROE_MISSING).
      - If check fails, add field-specific FAIL code (e.g., ROE_FAIL).
    - Reason codes in canonical order (ROE → Margin → Debt).
    - Overall pass: reasons list is empty; overall fail: reasons list has entries.
    """
    # Validate config keys (explicit, fail-safe)
    validate_config_keys(fundamental_config)
    
    # Empty config means all checks pass (spec: evaluate 0 thresholds → 0 failures)
    if not fundamental_config:
        return {"fundamental_pass": True, "reasons": []}
    
    reasons = []
    
    # Process checks in canonical order: ROE, Margin, Debt
    if "min_roe" in fundamental_config:
        passed, reason = check_roe_threshold(
            fundamental_data_item.get("roe"),
            fundamental_config["min_roe"],
        )
        if reason:
            reasons.append(reason)
    
    if "min_net_margin" in fundamental_config:
        passed, reason = check_net_margin_threshold(
            fundamental_data_item.get("net_margin"),
            fundamental_config["min_net_margin"],
        )
        if reason:
            reasons.append(reason)
    
    if "max_debt_ebitda" in fundamental_config:
        passed, reason = check_debt_ebitda_ceiling(
            fundamental_data_item.get("debt_ebitda"),
            fundamental_config["max_debt_ebitda"],
        )
        if reason:
            reasons.append(reason)
    
    # Reason codes already in canonical order (processed in order above)
    return {
        "fundamental_pass": len(reasons) == 0,
        "reasons": reasons,
    }


def evaluate_fundamental_universe(
    fundamental_data: Dict[str, Dict[str, Any]],
    fundamental_config: Dict[str, float],
) -> Dict[str, Dict[str, Any]]:
    """
    Evaluate fundamental checks for all tickers.
    Validates config once; applies to all tickers.
    
    Returns {
        ticker: {fundamental_pass: bool, reasons: [...]},
        ...
    }
    """
    # Validate config once (fail-safe)
    validate_config_keys(fundamental_config)
    
    results = {}
    for ticker, ticker_data in fundamental_data.items():
        results[ticker] = evaluate_fundamental_checks(ticker, ticker_data, fundamental_config)
    return results
