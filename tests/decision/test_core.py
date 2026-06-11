"""Unit tests for decision.core pure functions."""
import sys
import os
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from backend.engines.decision.core import evaluate_entry_rules, evaluate_exit_rules, BUY, HOLD, NO_TRADE, SELL


def test_evaluate_entry_buy_happy_path():
    d, reasons = evaluate_entry_rules(1, True, True, False)
    assert d == BUY
    assert reasons == []


def test_evaluate_entry_no_trade_on_fund_fail():
    d, reasons = evaluate_entry_rules(1, False, True, False)
    assert d == NO_TRADE
    assert 'FUND_FAIL' in reasons


def test_evaluate_entry_no_trade_on_risk_fail():
    d, reasons = evaluate_entry_rules(1, True, False, False)
    assert d == NO_TRADE
    assert 'RISK_FAIL' in reasons


def test_evaluate_entry_hold_when_no_tech_entry():
    d, reasons = evaluate_entry_rules(0, True, True, False)
    assert d == HOLD


def test_evaluate_entry_tech_entry_minus_one_treated_as_hold():
    # v1 deterministic choice: -1 treated as non-entry
    d, reasons = evaluate_entry_rules(-1, True, True, False)
    assert d == HOLD


def test_evaluate_entry_invalid_tech_entry_raises():
    with pytest.raises(ValueError):
        evaluate_entry_rules(2, True, True, False)


class TestExitRules:
    def test_evaluate_exit_sell_on_stop_loss(self):
        d, reasons = evaluate_exit_rules(True, True, False)
        assert d == SELL
        assert 'STOP_LOSS' in reasons

    def test_evaluate_exit_sell_on_tech_exit(self):
        d, reasons = evaluate_exit_rules(True, False, True)
        assert d == SELL
        assert 'TECH_EXIT' in reasons

    def test_evaluate_exit_hold_when_no_exit(self):
        d, reasons = evaluate_exit_rules(True, False, False)
        assert d == HOLD

    def test_evaluate_exit_no_position_returns_no_trade(self):
        d, reasons = evaluate_exit_rules(False, True, False)
        assert d == NO_TRADE
        assert 'NO_POSITION' in reasons

    def test_evaluate_exit_invalid_inputs_raise(self):
        with pytest.raises(ValueError):
            evaluate_exit_rules('yes', False, False)
