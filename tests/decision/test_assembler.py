"""Tests for the Decision assembler/orchestrator."""
import sys
import os
import json
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from backend.engines.decision.assembler import assemble_decision_request, compute_decision

FIX_DIR = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'decision')


def load_fixture(name):
    path = os.path.join(FIX_DIR, name)
    with open(path, 'r') as f:
        return json.load(f)


def test_assembler_buy_for_new_position():
    payload = load_fixture('request_buy_happy.json')
    out = compute_decision(payload)
    assert out['decision_token'] == 'BUY_CANDIDATE'
    assert out.get('size_info') is not None
    assert out['size_info']['allowed_qty'] > 0


def test_assembler_no_trade_may_have_null_size_info():
    payload = load_fixture('request_fund_fail.json')
    out = compute_decision(payload)
    assert out['decision_token'] == 'NO_TRADE'
    # size_info may be None or absent
    assert ('size_info' not in out) or out['size_info'] is None


def test_assembler_existing_position_exit():
    payload = load_fixture('existing_position_stop.json')
    out = compute_decision(payload)
    assert out['decision_token'] == 'SELL_EXIT_CANDIDATE'
    assert out.get('position_id') == 'pos-123'


def test_assembler_aggregates_reasons():
    # construct payload with fund fail and missing risk
    p = load_fixture('request_fund_fail.json')
    # also simulate risk error explicitly
    p['risk_assessment'] = None
    out = compute_decision(p)
    assert out['decision_token'] == 'NO_TRADE'
    assert 'FUND_FAIL' in out['reason_codes'] or 'MISSING_RISK' in out['reason_codes']


def test_assembler_upstream_error_becomes_no_trade():
    payload = load_fixture('request_insufficient_tech.json')
    out = compute_decision(payload)
    assert out['decision_token'] == 'NO_TRADE'
    assert 'INSUFFICIENT_HISTORY' in ' '.join(out.get('reason_codes', [])) or 'MISSING_TECHNICAL' in out.get('reason_codes', [])
