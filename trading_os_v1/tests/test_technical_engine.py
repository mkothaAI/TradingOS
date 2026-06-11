import pytest
from trading_os_v1.engines.technical_engine import TechnicalEngineImpl


def make_bars(n=20, start=100.0):
    import datetime
    bars = []
    close = start
    for i in range(n):
        o = close
        c = close * (1 + (0.01 if i % 5 == 0 else 0.0))
        h = max(o, c) * 1.01
        l = min(o, c) * 0.99
        v = 1000 + (i * 10)
        bars.append({'open': o, 'high': h, 'low': l, 'close': c, 'volume': v, 'timestamp': datetime.datetime.now()})
        close = c
    return bars


def test_generate_signals_basic():
    te = TechnicalEngineImpl('tech', [])
    bars = make_bars(20)
    res = te.generate_signals('TST', bars)
    assert 'signal' in res
    assert 'indicators' in res
    # volume_ma should be > 0
    assert res['indicators']['volume_ma'] > 0
