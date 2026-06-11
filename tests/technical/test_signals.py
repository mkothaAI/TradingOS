"""Tests for MA-cross and momentum signals."""
import sys
import os
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from backend.engines.technical.signals import ma_cross_signal, momentum_signal
from tests.fixtures.technical.ohlcv_sma_cross import OHLCV_SMA_CROSS
from tests.fixtures.technical.ohlcv_simple_uptrend import OHLCV_SIMPLE_UPTREND


def closes_from_ohlcv(ohlcv):
    return [b['close'] for b in ohlcv]


def test_ma_cross_signal_short_crosses_long():
    closes = closes_from_ohlcv(OHLCV_SMA_CROSS)
    # Use short=5, long=20; fixture crafted to produce a positive cross
    sig = ma_cross_signal(closes, short_window=5, long_window=20)
    assert sig == 1


def test_ma_cross_signal_no_cross():
    closes = closes_from_ohlcv(OHLCV_SIMPLE_UPTREND)
    # Not enough length for long window+1 to compute cross comparison -> expect ValueError
    # Here closes has length 6 and long_window=5 requires long_window+1=6, so it is sufficient
    # Therefore we assert no cross (neutral signal)
    sig = ma_cross_signal(closes, short_window=3, long_window=5)
    assert sig == 0


def test_momentum_signal_positive():
    closes = closes_from_ohlcv(OHLCV_SIMPLE_UPTREND)
    # window=3: compare close[-4] to close[-1]
    m = momentum_signal(closes, window=3, threshold=0.01)
    assert m is True


def test_momentum_signal_negative():
    # small fluctuation fixture
    closes = closes_from_ohlcv(OHLCV_SIMPLE_UPTREND[:4])
    with pytest.raises(ValueError):
        # insufficient history for window=5
        momentum_signal(closes, window=5)
