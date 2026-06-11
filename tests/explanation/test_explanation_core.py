"""Tests for explanation.core pure functions (Phase 5)."""
import sys
import os
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from backend.engines.explanation.core import map_rule_to_source, generate_explanation, validate_explanation_facts


RULE_MAPPING = {
    'R0001': {'file': 'module-09.md', 'description': 'Expected return', 'line_range': None},
    'R0004': {'file': 'module-02.md', 'description': 'ATR computation', 'line_range': None},
}


def test_map_rule_to_source_found():
    result = map_rule_to_source('R0001', RULE_MAPPING)
    assert result['file'] == 'module-09.md'
    assert result['description'] == 'Expected return'
    assert result['line_range'] is None


def test_map_rule_to_source_not_found():
    result = map_rule_to_source('R9999', RULE_MAPPING)
    assert result['file'] is None
    assert result['description'] == 'unknown'
    assert result['line_range'] is None


def test_generate_explanation_with_rules():
    payload = {
        'decision_token': 'BUY_CANDIDATE',
        'reason_codes': [],
        'size_info': {'allowed_qty': 10},
    }
    exp = generate_explanation(['R0001', 'R0004'], payload, RULE_MAPPING)
    assert 'BUY_CANDIDATE' in exp['explanation_text']
    assert 'R0001' in exp['explanation_text']
    assert 'R0004' in exp['explanation_text']
    assert len(exp['source_links']) == 2


def test_generate_explanation_no_rules():
    payload = {
        'decision_token': 'HOLD',
        'reason_codes': [],
        'size_info': None,
    }
    exp = generate_explanation([], payload, RULE_MAPPING)
    assert 'HOLD' in exp['explanation_text']
    assert 'No explicit rules' in exp['explanation_text']
    assert len(exp['source_links']) == 0


def test_generate_explanation_with_reason_codes():
    payload = {
        'decision_token': 'NO_TRADE',
        'reason_codes': ['FUND_FAIL', 'RISK_FAIL'],
        'size_info': None,
    }
    exp = generate_explanation(['R0002'], payload, RULE_MAPPING)
    assert 'NO_TRADE' in exp['explanation_text']
    assert 'FUND_FAIL' in exp['explanation_text']
    assert 'RISK_FAIL' in exp['explanation_text']


def test_generate_explanation_unmapped_rule():
    payload = {
        'decision_token': 'BUY_CANDIDATE',
        'reason_codes': [],
        'size_info': {'allowed_qty': 5},
    }
    exp = generate_explanation(['R0001', 'R9999'], payload, RULE_MAPPING)
    assert 'R0001' in exp['explanation_text']
    assert 'R9999' in exp['explanation_text']
    assert 'source not found' in exp['explanation_text']
    assert len(exp['source_links']) == 2
    assert exp['source_links'][1]['file'] is None


def test_generate_explanation_deterministic():
    payload = {
        'decision_token': 'BUY_CANDIDATE',
        'reason_codes': [],
        'size_info': {'allowed_qty': 10},
    }
    exp1 = generate_explanation(['R0001'], payload, RULE_MAPPING)
    exp2 = generate_explanation(['R0001'], payload, RULE_MAPPING)
    assert exp1['explanation_text'] == exp2['explanation_text']
    assert exp1['source_links'] == exp2['source_links']


def test_validate_explanation_facts_valid():
    payload = {
        'decision_token': 'BUY_CANDIDATE',
        'reason_codes': ['TECH_ENTRY'],
        'size_info': {'allowed_qty': 10},
    }
    exp_text = "Decision: BUY_CANDIDATE. Reasons: TECH_ENTRY. Rule R0001 applied. Approved quantity: 10 shares."
    is_valid, violations = validate_explanation_facts(exp_text, ['R0001'], payload, RULE_MAPPING)
    assert is_valid
    assert len(violations) == 0


def test_validate_explanation_facts_missing_decision_token():
    payload = {
        'decision_token': 'BUY_CANDIDATE',
        'reason_codes': [],
        'size_info': None,
    }
    exp_text = "Rule R0001 applied."
    is_valid, violations = validate_explanation_facts(exp_text, ['R0001'], payload, RULE_MAPPING)
    assert not is_valid
    assert any('missing_decision_token' in v for v in violations)


def test_validate_explanation_facts_missing_rule_id():
    payload = {
        'decision_token': 'BUY_CANDIDATE',
        'reason_codes': [],
        'size_info': None,
    }
    exp_text = "Decision: BUY_CANDIDATE. R0004 applied."
    is_valid, violations = validate_explanation_facts(exp_text, ['R0001'], payload, RULE_MAPPING)
    assert not is_valid
    assert any('missing_rule_id' in v for v in violations)
