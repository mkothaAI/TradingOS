"""Technical indicators (Phase 3).

Only `simple_moving_average` is provided in v1. EMA is explicitly deferred.
Helpers raise ValueError on invalid inputs.
"""
from typing import List


def simple_moving_average(series: List[float], window: int) -> float:
    if window < 1:
        raise ValueError('simple_moving_average: window must be >= 1')
    if len(series) < window:
        raise ValueError('simple_moving_average: insufficient history')
    window_vals = series[-window:]
    return sum(window_vals) / float(window)


def candle_classification(open_: float, high: float, low: float, close: float) -> str:
    if high < low:
        raise ValueError('candle_classification: high < low')
    if not (low <= open_ <= high) or not (low <= close <= high):
        raise ValueError('candle_classification: open/close out of bounds')
    if close > open_:
        return 'bullish'
    if close < open_:
        return 'bearish'
    return 'neutral'
