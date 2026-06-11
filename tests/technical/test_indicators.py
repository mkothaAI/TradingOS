"""Tests for SMA and candle classification."""
import sys
import os
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from backend.engines.technical.indicators import simple_moving_average, candle_classification
from tests.fixtures.technical.ohlcv_simple_uptrend import OHLCV_SIMPLE_UPTREND


def test_simple_moving_average_basic():
    closes = [1.0, 2.0, 3.0, 4.0, 5.0]
    sma = simple_moving_average(closes, 3)
    # last 3 = [3,4,5] -> mean = 4.0
    assert abs(sma - 4.0) < 1e-12


def test_simple_moving_average_constant_series():
    vals = [5.0] * 10
    sma = simple_moving_average(vals, 5)
    assert abs(sma - 5.0) < 1e-12


def test_sma_insufficient_history():
    with pytest.raises(ValueError):
        simple_moving_average([1.0, 2.0], 3)


def test_candle_classification_basic():
    b = OHLCV_SIMPLE_UPTREND[0]
    cl = candle_classification(b['open'], b['high'], b['low'], b['close'])
    assert cl == 'bullish'


def test_candle_classification_equal_open_close():
    cl = candle_classification(100.0, 101.0, 99.0, 100.0)
    assert cl == 'neutral'
