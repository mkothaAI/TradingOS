"""Position sizing functions for risk management.

Phase 2: Business-level sizing models implementing trading constraints.
"""
from typing import Tuple, Optional


def position_size_total_equity(total_equity: float, per_trade_risk_pct: float, 
                               stop_distance_per_share: float) -> int:
    """Compute position size using total equity model.
    
    Convention: per_trade_risk_pct (Varsity examples: 1-2%) is example-derived.
    Requires human confirmation before becoming production default.
    
    Formula:
    - risk_amount = total_equity * per_trade_risk_pct
    - qty = floor(risk_amount / stop_distance_per_share)
    
    Args:
        total_equity: portfolio equity (float, > 0)
        per_trade_risk_pct: risk per trade as % of equity (float, e.g., 0.01)
        stop_distance_per_share: stop distance per share (float, > 0)
        
    Returns:
        integer number of shares
        
    Raises:
        ValueError: if total_equity, per_trade_risk_pct, or stop_distance invalid
    """
    if total_equity <= 0:
        raise ValueError(f'position_size_total_equity: total_equity must be > 0, got {total_equity}')
    if per_trade_risk_pct < 0:
        raise ValueError(f'position_size_total_equity: per_trade_risk_pct must be >= 0, got {per_trade_risk_pct}')
    if stop_distance_per_share <= 0:
        raise ValueError(f'position_size_total_equity: stop_distance_per_share must be > 0, got {stop_distance_per_share}')
    
    risk_amount = total_equity * per_trade_risk_pct
    qty = int(risk_amount / stop_distance_per_share)
    
    return max(0, qty)


def position_size_percentage_volatility(total_equity: float, per_trade_risk_pct: float,
                                       atr_value: float, atr_multiplier: float) -> int:
    """Compute position size using ATR-based volatility model.
    
    Convention: atr_multiplier (Varsity examples: 2.0 for 2*ATR stop) is example-derived.
    Requires human confirmation before becoming production default.
    
    Formula:
    - stop_distance_per_share = atr_value * atr_multiplier
    - qty = position_size_total_equity(total_equity, per_trade_risk_pct, stop_distance_per_share)
    
    Args:
        total_equity: portfolio equity (float, > 0)
        per_trade_risk_pct: risk per trade as % (float, >= 0)
        atr_value: ATR value from atr_helper (float, > 0)
        atr_multiplier: multiplier for ATR to get stop distance (float, > 0)
        
    Returns:
        integer number of shares
        
    Raises:
        ValueError: if any inputs invalid
    """
    if atr_value <= 0:
        raise ValueError(f'position_size_percentage_volatility: atr_value must be > 0, got {atr_value}')
    if atr_multiplier <= 0:
        raise ValueError(f'position_size_percentage_volatility: atr_multiplier must be > 0, got {atr_multiplier}')
    
    stop_distance_per_share = atr_value * atr_multiplier
    return position_size_total_equity(total_equity, per_trade_risk_pct, stop_distance_per_share)


def position_size_percentage_margin(total_equity: float, max_margin_pct: float, 
                                   current_price: float) -> int:
    """Compute position size constrained by margin availability.
    
    Formula:
    - available_for_position = total_equity * max_margin_pct
    - qty = floor(available_for_position / current_price)
    
    Args:
        total_equity: portfolio equity (float, > 0)
        max_margin_pct: max position as % of equity (float, > 0)
        current_price: current stock price (float, > 0)
        
    Returns:
        integer number of shares
        
    Raises:
        ValueError: if any inputs invalid
    """
    if total_equity <= 0:
        raise ValueError(f'position_size_percentage_margin: total_equity must be > 0, got {total_equity}')
    if max_margin_pct <= 0:
        raise ValueError(f'position_size_percentage_margin: max_margin_pct must be > 0, got {max_margin_pct}')
    if current_price <= 0:
        raise ValueError(f'position_size_percentage_margin: current_price must be > 0, got {current_price}')
    
    available_for_position = total_equity * max_margin_pct
    qty = int(available_for_position / current_price)
    
    return max(0, qty)


def enforce_max_position_cap(allowed_qty: int, total_equity: float, current_price: float,
                            max_position_size_pct: float) -> Tuple[int, Optional[str]]:
    """Apply hard cap on position size as % of portfolio.
    
    Logic: if notional > total_equity * max_position_size_pct, return (0, 'POSITION_CAP_EXCEEDED'),
           else (qty, None)
    
    Args:
        allowed_qty: tentative position size (int)
        total_equity: portfolio equity (float, > 0)
        current_price: current stock price (float, > 0)
        max_position_size_pct: max position as % of portfolio (float, > 0)
        
    Returns:
        (capped_qty: int, reason_code: str or None)
        
    Raises:
        ValueError: if total_equity or current_price invalid
    """
    if total_equity <= 0:
        raise ValueError(f'enforce_max_position_cap: total_equity must be > 0, got {total_equity}')
    if current_price <= 0:
        raise ValueError(f'enforce_max_position_cap: current_price must be > 0, got {current_price}')
    
    notional = allowed_qty * current_price
    max_allowed_notional = total_equity * max_position_size_pct
    
    if notional > max_allowed_notional:
        return (0, 'POSITION_CAP_EXCEEDED')
    
    return (allowed_qty, None)
