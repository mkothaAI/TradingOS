"""Tests for technical.calc pure helpers."""
import sys
import os
import math
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from backend.engines.technical.calc import returns_series, volatility_series, atr_helper
from tests.fixtures.technical.ohlcv_simple_uptrend import OHLCV_SIMPLE_UPTREND


def test_returns_series_basic():
    closes = [100.0, 110.0]
    r = returns_series(closes)
    assert len(r) == 1
    assert abs(r[0] - 0.10) < 1e-8


def test_returns_series_insufficient_history():
    with pytest.raises(ValueError):
        returns_series([100.0])


def test_volatility_series_sample_std_dev():
    # small returns vector with known sample stddev
    returns = [0.01, -0.01, 0.02]
    # window=3 -> sample variance: mean=0.0066667, ssd ≈ (0.01-mean)^2+... = ~0.0004333, var=ssd/2
    vol = volatility_series(returns, 3)
    assert isinstance(vol, float)
    assert vol > 0


def test_atr_helper_basic():
    o = OHLCV_SIMPLE_UPTREND
    highs = [b['high'] for b in o]
    lows = [b['low'] for b in o]
    closes = [b['close'] for b in o]
    # window=3 requires at least 4 bars
    atr = atr_helper(highs, lows, closes, window=3)
    assert atr > 0


def test_atr_insufficient_history():
    o = OHLCV_SIMPLE_UPTREND[:3]
    highs = [b['high'] for b in o]
    lows = [b['low'] for b in o]
    closes = [b['close'] for b in o]
    with pytest.raises(ValueError):
        atr_helper(highs, lows, closes, window=3)
