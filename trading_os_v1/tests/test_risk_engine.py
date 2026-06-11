from trading_os_v1.engines.risk_engine import RiskEngine


def test_position_size_basic():
    re = RiskEngine('risk', [])
    portfolio = 50000
    stop_distance = 2.0
    price = 100.0
    size = re.position_size(portfolio, stop_distance, price, volatility=0.04, volatility_avg=0.02)
    # max risk = 1000; base size = 500; volatility scale 0.75 => 375
    assert size == 375


def test_halt_trading():
    re = RiskEngine('risk', [])
    assert re.should_halt_trading(-0.03) is True
    assert re.should_halt_trading(-0.01) is False
