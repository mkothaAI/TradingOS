"""Thin deterministic assembler for Decision engine (Phase 4).

Responsibilities:
- Map upstream payload to primitives expected by core.evaluate_* functions
- Aggregate upstream errors into reason codes
- Forward `size_info` for BUY_CANDIDATE only (must be valid)
- Return deterministic `DecisionItem` dict (no side effects)
"""
from typing import Dict, Any
from backend.engines.decision.core import evaluate_entry_rules, evaluate_exit_rules, BUY, HOLD, NO_TRADE, SELL


def _extract_tech_entry(technical_signals: Dict[str, Any]) -> Any:
    """Extract tech_entry primitive from technical_signals.

    Preference order:
    - if `tech_entry` provided explicitly use it
    - else if `ma_cross` provided use that
    - else default to 0
    """
    if technical_signals is None:
        return None
    if 'tech_entry' in technical_signals:
        return technical_signals['tech_entry']
    if 'ma_cross' in technical_signals:
        return technical_signals['ma_cross']
    return 0


def assemble_decision_request(payload: Dict[str, Any], policy_config: Dict[str, Any] = None) -> Dict[str, Any]:
    """Map raw payload into primitives for decision core.

    Minimal assumptions: payload is a dict containing optional keys:
    `technical_signals`, `fundamental_pass`, `risk_assessment`, `event_flags`, `portfolio_state`.
    This assembler does not perform deep schema validation; it maps and
    aggregates upstream error indicators deterministically.
    """
    result: Dict[str, Any] = {}

    technical = payload.get('technical_signals')
    if technical is None:
        result['technical_error'] = 'MISSING_TECHNICAL'
        tech_entry = None
    else:
        if isinstance(technical, dict) and technical.get('error'):
            result['technical_error'] = technical.get('error')
        tech_entry = _extract_tech_entry(technical)

    # Fundamental
    fund_pass = payload.get('fundamental_pass', True)

    # Risk
    risk = payload.get('risk_assessment')
    risk_ok = False
    size_info = None
    if risk is None:
        result['risk_error'] = 'MISSING_RISK'
    else:
        if isinstance(risk, dict) and risk.get('error'):
            result['risk_error'] = risk.get('error')
        size_info = risk.get('size_info') if isinstance(risk, dict) else None
        if isinstance(size_info, dict) and size_info.get('allowed_qty', 0) > 0:
            risk_ok = True

    # Events
    events = payload.get('event_flags') or {}
    event_block = bool(events.get('blackout', False))

    # Portfolio / existing position info
    portfolio = payload.get('portfolio_state') or {}
    existing_position = bool(portfolio.get('existing_position', False))
    position_id = portfolio.get('position_id')
    stop_loss_hit = bool(portfolio.get('stop_loss_hit', False))

    result.update({
        'tech_entry': tech_entry,
        'fund_pass': fund_pass,
        'risk_ok': risk_ok,
        'event_block': event_block,
        'size_info': size_info,
        'existing_position': existing_position,
        'position_id': position_id,
        'stop_loss_hit': stop_loss_hit,
    })

    return result


def compute_decision(payload: Dict[str, Any], policy_config: Dict[str, Any] = None) -> Dict[str, Any]:
    """Compute final DecisionItem dict from assembled payload.

    Rules:
    - If existing_position True, evaluate exit rules and give exit precedence.
    - Otherwise evaluate entry rules.
    - BUY_CANDIDATE must include valid `size_info` with `allowed_qty>0`.
    - NO_TRADE may include null/absent `size_info`.
    """
    asm = assemble_decision_request(payload, policy_config)

    # handle explicit upstream errors mapped to NO_TRADE
    reason_codes = []
    if asm.get('technical_error'):
        reason_codes.append(asm['technical_error'])
    if asm.get('risk_error'):
        reason_codes.append(asm['risk_error'])

    existing = asm.get('existing_position', False)

    if existing:
        # exit precedence
        decision_token, exit_reasons = evaluate_exit_rules(existing, asm.get('stop_loss_hit', False), bool(asm.get('tech_entry') == -1))
        reason_codes.extend(exit_reasons)
        out = {'decision_token': decision_token, 'reason_codes': reason_codes, 'applied_rules': [], 'size_info': None}
        if decision_token == SELL:
            out['position_id'] = asm.get('position_id')
        return out

    # If upstream technical produced an explicit error, map to NO_TRADE
    if asm.get('technical_error'):
        return {'decision_token': NO_TRADE, 'reason_codes': reason_codes + [asm.get('technical_error')], 'applied_rules': [], 'size_info': None}

    # entry path
    te = asm.get('tech_entry')
    if te is None:
        # missing technical -> NO_TRADE
        return {'decision_token': NO_TRADE, 'reason_codes': reason_codes + ['MISSING_TECHNICAL'], 'applied_rules': [], 'size_info': None}

    try:
        decision_token, entry_reasons = evaluate_entry_rules(int(te), bool(asm.get('fund_pass', True)), bool(asm.get('risk_ok', False)), bool(asm.get('event_block', False)))
    except ValueError:
        return {'decision_token': NO_TRADE, 'reason_codes': reason_codes + ['INVALID_TECH_ENTRY'], 'applied_rules': [], 'size_info': None}

    reason_codes.extend(entry_reasons)

    out = {'decision_token': decision_token, 'reason_codes': reason_codes, 'applied_rules': []}

    if decision_token == BUY:
        # forward size_info, must be valid
        size_info = asm.get('size_info')
        if not (isinstance(size_info, dict) and size_info.get('allowed_qty', 0) > 0):
            # Convert to NO_TRADE if missing/invalid sizing
            return {'decision_token': NO_TRADE, 'reason_codes': reason_codes + ['INVALID_SIZE_INFO'], 'applied_rules': [], 'size_info': None}
        out['size_info'] = size_info
    else:
        out['size_info'] = asm.get('size_info')  # may be None

    return out
