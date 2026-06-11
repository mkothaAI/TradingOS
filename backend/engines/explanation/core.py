"""Pure explanation generation logic (Phase 5).

All functions are deterministic, accept primitives/dicts, and produce
deterministic outputs. No rule inference. No timestamps. No invented line numbers.
"""
from typing import List, Dict, Tuple, Any


def map_rule_to_source(rule_id: str, rule_mapping: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Map a rule_id to its source metadata.

    If rule_id not found in rule_mapping, returns placeholder with file=null.
    Never invents line numbers; uses None for unavailable ranges.
    """
    if rule_id in rule_mapping:
        entry = rule_mapping[rule_id]
        return {
            'file': entry.get('file'),
            'description': entry.get('description', 'unknown'),
            'line_range': entry.get('line_range'),
        }
    # Unmapped rule: return placeholder
    return {
        'file': None,
        'description': 'unknown',
        'line_range': None,
    }


def generate_explanation(applied_rules: List[str], decision_payload: Dict[str, Any], rule_mapping: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Generate deterministic explanation from applied_rules and decision_payload.

    No rule inference. No timestamps.
    applied_rules must be explicitly provided (not inferred from decision_token).
    """
    decision_token = decision_payload.get('decision_token', 'UNKNOWN')
    reason_codes = decision_payload.get('reason_codes', [])
    size_info = decision_payload.get('size_info')

    # Build explanation_text
    lines = []
    lines.append(f"Decision: {decision_token}.")
    
    if reason_codes:
        reason_str = ', '.join(reason_codes)
        lines.append(f"Reasons: {reason_str}.")
    
    if applied_rules:
        lines.append("Rules applied:")
        for rule_id in applied_rules:
            rule_info = map_rule_to_source(rule_id, rule_mapping)
            file_str = rule_info['file'] if rule_info['file'] else 'source not found'
            lines.append(f"  {rule_id}: {rule_info['description']} (source: {file_str})")
    else:
        lines.append("No explicit rules provided in decision.")

    if size_info and isinstance(size_info, dict) and size_info.get('allowed_qty'):
        lines.append(f"Approved quantity: {size_info['allowed_qty']} shares.")

    explanation_text = ' '.join(lines)

    # Build source_links
    source_links = []
    for rule_id in applied_rules:
        rule_info = map_rule_to_source(rule_id, rule_mapping)
        source_links.append({
            'rule_id': rule_id,
            'file': rule_info['file'],
            'line_range': rule_info['line_range'],
        })

    return {
        'explanation_text': explanation_text,
        'source_links': source_links,
    }


def validate_explanation_facts(explanation_text: str, applied_rules: List[str], decision_payload: Dict[str, Any], rule_mapping: Dict[str, Dict[str, Any]]) -> Tuple[bool, List[str]]:
    """Strict validator: check that explanation_text uses only facts from inputs.

    Checks for:
    - decision_token from decision_payload
    - rule_ids from applied_rules
    - reason_codes from decision_payload
    - numeric values from decision_payload (size_info)
    """
    violations = []

    decision_token = decision_payload.get('decision_token', '')
    if decision_token and decision_token not in explanation_text:
        violations.append(f"missing_decision_token: {decision_token}")

    reason_codes = decision_payload.get('reason_codes', [])
    for rc in reason_codes:
        if rc not in explanation_text:
            violations.append(f"missing_reason_code: {rc}")

    for rule_id in applied_rules:
        if rule_id not in explanation_text:
            violations.append(f"missing_rule_id: {rule_id}")

    size_info = decision_payload.get('size_info')
    if size_info and isinstance(size_info, dict) and size_info.get('allowed_qty'):
        qty = size_info['allowed_qty']
        if str(qty) not in explanation_text:
            violations.append(f"missing_quantity: {qty}")

    return len(violations) == 0, violations
