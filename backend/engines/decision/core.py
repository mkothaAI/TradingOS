"""Pure decision logic (entry and exit) for Phase 4.

Both functions are pure, deterministic, accept primitive inputs, and return
a tuple `(decision_token, reason_codes)` where `decision_token` is one of
the allowed tokens. They raise `ValueError` for invalid inputs.

Entry logic: `evaluate_entry_rules` treats `tech_entry == -1` as non-entry
and returns `HOLD` (deterministic choice for v1).
"""
from typing import List, Tuple


BUY = 'BUY_CANDIDATE'
SELL = 'SELL_EXIT_CANDIDATE'
HOLD = 'HOLD'
NO_TRADE = 'NO_TRADE'


def evaluate_entry_rules(tech_entry: int, fund_pass: bool, risk_ok: bool, event_block: bool) -> Tuple[str, List[str]]:
    """Evaluate entry-only conditions.

    tech_entry must be one of {-1,0,1}. For v1, -1 is treated as non-entry
    and maps to HOLD rather than an error.
    Returns (decision_token, reason_codes).
    """
    if tech_entry not in (-1, 0, 1):
        raise ValueError('evaluate_entry_rules: invalid tech_entry')

    # Non-entry values map to HOLD for entry evaluation
    if tech_entry in (0, -1):
        return HOLD, []

    # tech_entry == 1: check other booleans
    reasons: List[str] = []
    if not fund_pass:
        reasons.append('FUND_FAIL')
    if not risk_ok:
        reasons.append('RISK_FAIL')
    if event_block:
        reasons.append('EVENT_BLOCK')

    if reasons:
        return NO_TRADE, reasons

    return BUY, []


def evaluate_exit_rules(existing_position: bool, stop_loss_hit: bool, tech_exit_signal: bool) -> Tuple[str, List[str]]:
    """Evaluate exit-only conditions.

    If `existing_position` is False and an exit is requested, return NO_TRADE
    with reason `NO_POSITION`.
    """
    if not isinstance(existing_position, bool) or not isinstance(stop_loss_hit, bool) or not isinstance(tech_exit_signal, bool):
        raise ValueError('evaluate_exit_rules: invalid input types')

    reasons: List[str] = []

    if not existing_position:
        # No position to exit
        if stop_loss_hit or tech_exit_signal:
            return NO_TRADE, ['NO_POSITION']
        return NO_TRADE, ['NO_POSITION']

    # existing_position == True
    if stop_loss_hit:
        return SELL, ['STOP_LOSS']
    if tech_exit_signal:
        return SELL, ['TECH_EXIT']

    return HOLD, []
