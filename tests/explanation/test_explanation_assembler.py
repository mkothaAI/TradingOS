"""Tests for explanation.assembler (Phase 5)."""
import sys
import os
import json
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from backend.engines.explanation.assembler import assemble_explanation_request, build_explanation_response, compute_explanation

FIX_DIR = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'explanation')


def load_fixture(name):
    path = os.path.join(FIX_DIR, name)
    with open(path, 'r') as f:
        return json.load(f)


RULE_MAPPING = {
    'R0001': {'file': 'module-09.md', 'description': 'Expected return', 'line_range': None},
    'R0002': {'file': 'module-09.md', 'description': 'Portfolio variance', 'line_range': None},
    'R0004': {'file': 'module-02.md', 'description': 'ATR computation', 'line_range': None},
}


def test_assembler_buy_happy():
    decision = load_fixture('decision_buy_happy.json')
    asm = assemble_explanation_request(decision, RULE_MAPPING)
    assert 'applied_rules' in asm
    assert 'decision_payload' in asm
    assert 'rule_mapping' in asm
    assert asm['applied_rules'] == ['R0001', 'R0004']


def test_assembler_empty_applied_rules():
    decision = load_fixture('empty_applied_rules.json')
    asm = assemble_explanation_request(decision, RULE_MAPPING)
    assert asm['applied_rules'] == []


def test_assembler_no_inference():
    # Verify that no rules are inferred from decision_token or reason_codes
    decision = {'decision_token': 'BUY_CANDIDATE', 'reason_codes': ['TECH_ENTRY'], 'applied_rules': []}
    asm = assemble_explanation_request(decision, RULE_MAPPING)
    # applied_rules should still be empty (no inference from TECH_ENTRY)
    assert asm['applied_rules'] == []


def test_build_explanation_response():
    explanation = {
        'explanation_text': 'Decision: BUY_CANDIDATE.',
        'source_links': [{'rule_id': 'R0001', 'file': 'module-09.md', 'line_range': None}],
    }
    resp = build_explanation_response(explanation, ticker='AAPL')
    assert resp['ticker'] == 'AAPL'
    assert resp['explanation_text'] == 'Decision: BUY_CANDIDATE.'
    assert len(resp['source_links']) == 1
    assert 'source_citation_policy' in resp


def test_compute_explanation_no_timestamp():
    decision = load_fixture('decision_buy_happy.json')
    result = compute_explanation(decision, RULE_MAPPING, ticker='AAPL')
    # Verify no timestamp in explanation_text
    import re
    timestamp_pattern = r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'
    assert not re.search(timestamp_pattern, result['explanation_text'])


def test_compute_explanation_full_flow():
    decision = load_fixture('decision_no_trade.json')
    result = compute_explanation(decision, RULE_MAPPING, ticker='MSFT')
    assert result['ticker'] == 'MSFT'
    assert 'NO_TRADE' in result['explanation_text']
    assert 'FUND_FAIL' in result['explanation_text']
    assert len(result['source_links']) == 1
