"""Pure math helpers for technical engine (Phase 3).

All functions are pure and deterministic. They raise `ValueError` for
insufficient history or invalid numeric inputs. Volatility is raw sample
standard deviation (n-1). ATR uses simple moving-average of True Range
(no Wilder smoothing) and requires len(highs) == len(lows) == len(closes)
and at least `window + 1` observations.
"""
from typing import List
import math


def returns_series(closes: List[float]) -> List[float]:
    if len(closes) < 2:
        raise ValueError('returns_series: need at least 2 close prices')
    returns = []
    for i in range(1, len(closes)):
        prev = closes[i - 1]
        if prev == 0:
            raise ValueError('returns_series: previous close is zero')
        returns.append((closes[i] / prev) - 1.0)
    return returns


def sample_variance(values: List[float]) -> float:
    n = len(values)
    if n < 2:
        raise ValueError('sample_variance: need at least 2 observations')
    mean = sum(values) / n
    ssd = sum((x - mean) ** 2 for x in values)
    return ssd / (n - 1)


def volatility_series(returns: List[float], window: int) -> float:
    """Return raw sample standard deviation over last `window` returns.

    Raises ValueError on insufficient data or invalid window.
    """
    if window < 2:
        raise ValueError('volatility_series: window must be >= 2')
    if len(returns) < window:
        raise ValueError('volatility_series: insufficient returns for window')
    slice_ = returns[-window:]
    var = sample_variance(slice_)
    return math.sqrt(var)


def atr_helper(highs: List[float], lows: List[float], closes: List[float], window: int = 14) -> float:
    if not (len(highs) == len(lows) == len(closes)):
        raise ValueError('atr_helper: highs/lows/closes must have same length')
    if len(highs) < window + 1:
        raise ValueError(f'atr_helper: need at least {window+1} observations')

    true_ranges: List[float] = []
    for i in range(1, len(highs)):
        tr = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1])
        )
        true_ranges.append(tr)
    # SMA of last `window` TR values
    tr_window = true_ranges[-window:]
    return sum(tr_window) / window
