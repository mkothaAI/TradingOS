"""Signal generators (Phase 3).

Pure deterministic functions that raise ValueError on invalid inputs.
"""
from typing import List
from backend.engines.technical.indicators import simple_moving_average


def ma_cross_signal(closes: List[float], short_window: int, long_window: int) -> int:
    if short_window < 1 or long_window < 1:
        raise ValueError('ma_cross_signal: windows must be >= 1')
    if short_window >= long_window:
        raise ValueError('ma_cross_signal: short_window must be < long_window')
    if len(closes) < long_window + 1:
        # Need at least long_window+1 to compare t and t-1
        raise ValueError('ma_cross_signal: insufficient history')

    # compute SMA_short(t) and SMA_long(t) and their previous values
    sma_short_t = simple_moving_average(closes, short_window)
    sma_long_t = simple_moving_average(closes, long_window)

    # previous period: drop last close
    prev_series = closes[:-1]
    sma_short_prev = simple_moving_average(prev_series, short_window)
    sma_long_prev = simple_moving_average(prev_series, long_window)

    # crossing logic: short crosses above long => +1; crosses below => -1
    if sma_short_prev <= sma_long_prev and sma_short_t > sma_long_t:
        return 1
    if sma_short_prev >= sma_long_prev and sma_short_t < sma_long_t:
        return -1
    return 0


def momentum_signal(closes: List[float], window: int, threshold: float = 0.0) -> bool:
    if window < 1:
        raise ValueError('momentum_signal: window must be >= 1')
    if len(closes) < window + 1:
        raise ValueError('momentum_signal: insufficient history')
    past = closes[-(window + 1)]
    now = closes[-1]
    if past == 0:
        raise ValueError('momentum_signal: past close is zero')
    ret = (now / past) - 1.0
    return ret >= threshold
