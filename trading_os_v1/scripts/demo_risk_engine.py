from pathlib import Path
from trading_os_v1.engines import load_all_engines, RiskEngine


def main():
    md = Path.cwd() / 'trading_os_v1' / 'docs' / 'engine-mapping' / 'varsity-to-trading_os_v1.md'
    engines = load_all_engines(str(md))
    # Find Risk Engine section by title
    risk_title = next((t for t in engines.keys() if t.lower().startswith('risk engine')), None)
    if not risk_title:
        print('Risk Engine mapping not found')
        return
    mapping = engines[risk_title].mappings
    re = RiskEngine(risk_title, mapping)
    # sample inputs
    portfolio = 100000.0
    price = 50.0
    stop_distance = 2.0
    volatility = 0.04
    volatility_avg = 0.02
    size = re.position_size(portfolio, stop_distance, price, volatility, volatility_avg)
    print(f'Computed position size: {size} units (portfolio={portfolio}, stop={stop_distance})')
    dd = -0.025
    print('Should halt trading (monthly -2.5%)?', re.should_halt_trading(dd))
    print('Require stop-loss for trade with no stop:', re.require_stop_loss({}))
    print('Require stop-loss for trade with stop_price=48:', re.require_stop_loss({'stop_price':48}))
    # Futures/margin checks
    print('Leverage 1.5 allowed?', re.check_leverage_allowed(1.5))
    print('Leverage 2.5 allowed?', re.check_leverage_allowed(2.5))
    print('Margin util 45% =>', re.check_margin_utilization(45.0))
    print('Margin util 55% =>', re.check_margin_utilization(55.0))
    print('Margin util 65% =>', re.check_margin_utilization(65.0))
    print('Days to expiry 10 => should hold?', re.check_expiration_management(10))
    print('Days to expiry 3 => should hold?', re.check_expiration_management(3))
    print('Active futures 2 => consolidation ok?', re.check_position_consolidation(2))
    print('Active futures 4 => consolidation ok?', re.check_position_consolidation(4))


if __name__ == '__main__':
    main()
