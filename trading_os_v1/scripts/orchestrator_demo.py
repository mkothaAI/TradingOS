import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / 'trading_os_v1'))

from trading_os_v1.engines import (
    SimpleUniverseEngine,
    SimpleFundamentalEngine,
    TechnicalEngineImpl,
    RiskEngine,
    SimpleDecisionEngine,
    SimpleExplanationEngine,
    load_all_engines,
)


def orchestrate_single(symbol: str, price_bars, fundamentals, portfolio_capital=100000.0, monthly_drawdown=-0.01):
    # Load mappings (not used heavily by simple impls but kept for completeness)
    md = Path.cwd() / 'trading_os_v1' / 'docs' / 'engine-mapping' / 'varsity-to-trading_os_v1.md'
    mappings = load_all_engines(str(md))

    universe = SimpleUniverseEngine('universe', mappings.get('Universe Engine (Security Selection)', []))
    fundamental = SimpleFundamentalEngine('fundamental', mappings.get('Fundamental Engine (Business Quality Validation)', []))
    technical = TechnicalEngineImpl('technical', mappings.get('Technical Engine (Price/Volume Signal Generation)', []), lookback=20)
    risk = RiskEngine('risk', mappings.get('Risk Engine (Position Sizing, Portfolio Risk)', []))
    decision = SimpleDecisionEngine('decision', mappings.get('Decision Engine (Trade Logic & System Rules)', []))
    explain = SimpleExplanationEngine('explain', mappings.get('Explanation Engine (Reasoning, Reporting, Audit Trail)', []))

    # Universe step
    universe_symbols = universe.evaluate_universe({'symbols': [symbol]})
    if symbol not in universe_symbols:
        return {'decision': 'NO_TRADE', 'reason': 'Not in universe'}

    # Fundamental step
    fund_res = fundamental.score_fundamentals(symbol, fundamentals)

    # Technical step
    tech_res = technical.generate_signals(symbol, price_bars)

    # Risk checks
    risk_halt = risk.should_halt_trading(monthly_drawdown)

    # Decision
    decision_input = [{'fundamental': fund_res, 'technical': tech_res, 'risk_halt': risk_halt}]
    dec = decision.decide(decision_input)

    # Explanation
    explanation = explain.explain(dec)

    return {
        'symbol': symbol,
        'fundamental': fund_res,
        'technical': tech_res,
        'risk_halt': risk_halt,
        'decision': dec,
        'explanation': explanation,
    }


def main():
    # Prefer local CSV feeder if present
    import csv, datetime
    data_dir = Path.cwd() / 'trading_os_v1' / 'trading_os_v1' / 'data'
    bars = []
    ohlcv_csv = data_dir / 'sample_ohlcv.csv'
    if ohlcv_csv.exists():
        with ohlcv_csv.open() as f:
            reader = csv.DictReader(f)
            for r in reader:
                bars.append({'open': float(r['open']), 'high': float(r['high']), 'low': float(r['low']), 'close': float(r['close']), 'volume': int(r['volume']), 'timestamp': datetime.datetime.fromisoformat(r['timestamp'])})
    else:
        # fallback synthetic
        close = 100.0
        for i in range(30):
            o = close
            c = close * (1 + (0.01 if i % 5 == 0 else 0.0))
            h = max(o, c) * 1.01
            l = min(o, c) * 0.99
            v = 1000 + (i * 10)
            bars.append({'open': o, 'high': h, 'low': l, 'close': c, 'volume': v, 'timestamp': datetime.datetime.now()})
            close = c

    fundamentals = {'roe': 15.0, 'net_margin': 8.0, 'debt_ebitda': 1.5}
    # override fundamentals from CSV if available
    fund_csv = data_dir / 'sample_fundamentals.csv'
    if fund_csv.exists():
        with fund_csv.open() as f:
            reader = csv.DictReader(f)
            for r in reader:
                if r['symbol'] == 'AAPL':
                    fundamentals = {'roe': float(r['roe']), 'net_margin': float(r['net_margin']), 'debt_ebitda': float(r['debt_ebitda'])}

    res = orchestrate_single('AAPL', bars, fundamentals, portfolio_capital=100000.0, monthly_drawdown=-0.01)
    print('Orchestrator result:')
    print(res['decision'])
    print('Explanation:\n', res['explanation'])


if __name__ == '__main__':
    main()
