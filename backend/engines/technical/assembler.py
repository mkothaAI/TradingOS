"""Thin deterministic assemblers for Phase 3 technical engine.

These functions are thin wrappers that call pure helpers. They do NOT
perform schema parsing; they catch `ValueError` from helpers and translate
into assembler-level deterministic flags (e.g., 'INSUFFICIENT_HISTORY').
"""
from typing import List, Dict
from backend.engines.technical.calc import returns_series, atr_helper, volatility_series
from backend.engines.technical.indicators import simple_moving_average, candle_classification
from backend.engines.technical.signals import ma_cross_signal, momentum_signal


def technical_indicators_for_ticker(ohlcv: List[Dict], technical_config: Dict) -> Dict:
    """Compute indicators and signals for a single ticker.

    ohlcv: list of bars (oldest->newest) where each bar is a dict with at least
           'open','high','low','close','volume'. No schema parsing here.
    technical_config: { 'atr_window':int, 'ma_windows':[int], 'momentum_windows':[int], 'momentum_threshold':float }

    Returns a dict with keys: 'indicators', 'signals', and optional 'error'.
    """
    try:
        closes = [b['close'] for b in ohlcv]
        highs = [b['high'] for b in ohlcv]
        lows = [b['low'] for b in ohlcv]
    except Exception as exc:
        return {'indicators': None, 'signals': None, 'error': 'MALFORMED_OHLCV'}

    out: Dict = {'indicators': {}, 'signals': {}}
    # Indicators
    try:
        out['indicators']['returns'] = returns_series(closes)
    except ValueError as e:
        out['error'] = 'INSUFFICIENT_HISTORY'
        out['indicators'] = None
        out['signals'] = {}
        return out

    # ATR
    try:
        atr_w = technical_config.get('atr_window', 14)
        out['indicators']['atr'] = atr_helper(highs, lows, closes, window=atr_w)
    except ValueError:
        out['error'] = 'INSUFFICIENT_HISTORY'
        out['indicators'] = None
        out['signals'] = {}
        return out

    # SMAs
    ma_windows = technical_config.get('ma_windows', [])
    out['indicators']['ma'] = {}
    for w in ma_windows:
        try:
            out['indicators']['ma'][w] = simple_moving_average(closes, w)
        except ValueError:
            out['error'] = 'INSUFFICIENT_HISTORY'
            out['indicators'] = None
            out['signals'] = {}
            return out

    # Volatility for configured windows (raw sample stddev)
    vol_windows = technical_config.get('volatility_windows', [])
    out['indicators']['volatility'] = {}
    for w in vol_windows:
        try:
            rets = out['indicators']['returns']
            out['indicators']['volatility'][w] = volatility_series(rets, w)
        except ValueError:
            out['error'] = 'INSUFFICIENT_HISTORY'
            out['indicators'] = None
            out['signals'] = {}
            return out

    # Signals
    # Candle (last bar)
    last = ohlcv[-1]
    try:
        out['signals']['candle'] = candle_classification(last['open'], last['high'], last['low'], last['close'])
    except ValueError:
        out['signals']['candle'] = 'neutral'

    # MA-cross: require at least two MA windows (short, long)
    if len(ma_windows) >= 2:
        short_w = ma_windows[0]
        long_w = ma_windows[1]
        try:
            out['signals']['ma_cross'] = ma_cross_signal(closes, short_w, long_w)
        except ValueError:
            out['signals']['ma_cross'] = 0
    else:
        out['signals']['ma_cross'] = 0

    # Momentum
    momentum_windows = technical_config.get('momentum_windows', [])
    if momentum_windows:
        w = momentum_windows[0]
        thresh = technical_config.get('momentum_threshold', 0.0)
        try:
            out['signals']['momentum'] = momentum_signal(closes, w, thresh)
        except ValueError:
            out['signals']['momentum'] = False
    else:
        out['signals']['momentum'] = False

    return out


def compute_technical_engine(price_series: Dict[str, List[Dict]], technical_config: Dict) -> Dict[str, Dict]:
    results: Dict[str, Dict] = {}
    for ticker, ohlcv in price_series.items():
        try:
            results[ticker] = technical_indicators_for_ticker(ohlcv, technical_config)
        except Exception:
            # Deterministic fallback per ticker
            results[ticker] = {'indicators': None, 'signals': {}, 'error': 'PROCESSING_ERROR'}
    return results
