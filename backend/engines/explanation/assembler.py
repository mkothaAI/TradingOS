"""Thin deterministic assembler for Explanation engine (Phase 5).

No rule inference. No timestamps.
"""
from typing import Dict, Any
from backend.engines.explanation.core import generate_explanation
from backend.engines.explanation.mapping import load_rule_mapping


def assemble_explanation_request(decision_item: Dict[str, Any], rule_mapping: Dict[str, Any] = None) -> Dict[str, Any]:
    """Map Decision engine output into explanation generation inputs.

    No rule inference. applied_rules is used as-is or defaults to empty list.
    """
    if rule_mapping is None:
        rule_mapping = load_rule_mapping()

    # Extract fields from decision_item
    decision_token = decision_item.get('decision_token')
    reason_codes = decision_item.get('reason_codes', [])
    size_info = decision_item.get('size_info')
    applied_rules = decision_item.get('applied_rules', [])  # Use as-is, no inference

    decision_payload = {
        'decision_token': decision_token,
        'reason_codes': reason_codes,
        'size_info': size_info,
    }

    return {
        'applied_rules': applied_rules,
        'decision_payload': decision_payload,
        'rule_mapping': rule_mapping,
    }


def build_explanation_response(explanation_dict: Dict[str, Any], ticker: str = None) -> Dict[str, Any]:
    """Format explanation output into ExplanationResponse structure.

    No timestamps added. source_citation_policy metadata included.
    """
    return {
        'ticker': ticker,
        'explanation_text': explanation_dict.get('explanation_text'),
        'source_links': explanation_dict.get('source_links', []),
        'source_citation_policy': 'facts_only_explicit_rules_only',
    }


def compute_explanation(decision_item: Dict[str, Any], rule_mapping: Dict[str, Any] = None, ticker: str = None) -> Dict[str, Any]:
    """Compute final explanation response from decision_item.

    No timestamps. No rule inference.
    """
    asm = assemble_explanation_request(decision_item, rule_mapping)
    explanation_dict = generate_explanation(
        asm['applied_rules'],
        asm['decision_payload'],
        asm['rule_mapping']
    )
    return build_explanation_response(explanation_dict, ticker)
