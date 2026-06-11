# trading-os-v1/tests/test_models.py
"""Unit tests for Pydantic models in trading-os-v1"""

import pytest
from pydantic import ValidationError
from trading_os_v1.models import (
    SymbolRequest, PriceBar, IndicatorSnapshot, 
    RiskSnapshot, DecisionResult
)

def test_symbol_request_valid():
    """Test valid SymbolRequest model"""
    model = SymbolRequest(symbol="AAPL", timeframe="1d")
    assert model.symbol == "AAPL"
    assert model.timeframe == "1d"

def test_symbol_request_invalid_symbol():
    """Test invalid symbol in SymbolRequest"""
    with pytest.raises(ValidationError):
        SymbolRequest(symbol="123", timeframe="1d")

def test_symbol_request_invalid_timeframe():
    """Test invalid timeframe in SymbolRequest"""
    with pytest.raises(ValidationError):
        SymbolRequest(symbol="AAPL", timeframe="1m")

def test_price_bar_valid():
    """Test valid PriceBar model"""
    model = PriceBar(
        open=100.0, high=105.0, low=95.0, close=102.0,
        volume=10000, timestamp="2026-05-15T12:00:00Z"
    )
    assert model.open == 100.0
    assert model.timestamp.isoformat() == "2026-05-15T12:00:00+00:00"

def test_price_bar_missing_required_field():
    """Test missing required field in PriceBar"""
    with pytest.raises(ValidationError):
        PriceBar(open=100.0, high=105.0, low=95.0, close=102.0, volume=10000)

def test_indicator_snapshot_valid():
    """Test valid IndicatorSnapshot model"""
    model = IndicatorSnapshot(
        rsi=65.0,
        macd={"line": 1.2, "signal": 0.8, "histogram": 0.4},
        sma_50=110.0,
        sma_200=100.0,
        momentum=15.0
    )
    assert model.rsi == 65.0
    assert model.macd["line"] == 1.2

def test_indicator_snapshot_invalid_field():
    """Test invalid field in IndicatorSnapshot"""
    with pytest.raises(ValidationError):
        IndicatorSnapshot(rsi="invalid", macd={"line": 1.2})

def test_risk_snapshot_valid():
    """Test valid RiskSnapshot model"""
    model = RiskSnapshot(
        volatility=0.15,
        sharpe_ratio=2.0,
        max_drawdown=0.25,
        risk_reward_ratio=3.0
    )
    assert model.volatility == 0.15
    assert model.sharpe_ratio == 2.0

def test_risk_snapshot_invalid_field():
    """Test invalid field in RiskSnapshot"""
    with pytest.raises(ValidationError):
        RiskSnapshot(volatility="invalid", sharpe_ratio=2.0)

def test_decision_result_valid():
    """Test valid DecisionResult model"""
    model = DecisionResult(
        symbol="AAPL",
        decision_state="NO_TRADE",
        reasons=["Insufficient data"],
        indicator_snapshot=IndicatorSnapshot(rsi=50.0),
        risk_snapshot=RiskSnapshot(volatility=0.1)
    )
    assert model.symbol == "AAPL"
    assert model.decision_state == "NO_TRADE"

def test_decision_result_invalid_state():
    """Test invalid decision state in DecisionResult"""
    with pytest.raises(ValidationError):
        DecisionResult(
            symbol="AAPL",
            decision_state="INVALID_STATE",
            reasons=["Invalid state"],
            indicator_snapshot=IndicatorSnapshot(rsi=50.0),
            risk_snapshot=RiskSnapshot(volatility=0.1)
        )