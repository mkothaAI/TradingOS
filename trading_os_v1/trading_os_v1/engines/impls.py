from typing import Dict, Any, List
from .core import UniverseEngine, FundamentalEngine, TechnicalEngine, DecisionEngine, ExplanationEngine
from .models import MappingEntry


class SimpleUniverseEngine(UniverseEngine):
    def evaluate_universe(self, market_data: Dict[str, Any]) -> List[str]:
        # Pass-through: return symbols provided in market_data
        return market_data.get('symbols', [])
    def validate(self):
        return True


class SimpleFundamentalEngine(FundamentalEngine):
    def score_fundamentals(self, symbol: str, fundamentals: Dict[str, Any]) -> Dict[str, Any]:
        # Apply v1-Safe rules from Module 3: ROE>12%, margin>5%, debt/EBITDA<=3
        roe = fundamentals.get('roe', 0.0)
        margin = fundamentals.get('net_margin', 0.0)
        debt_ebitda = fundamentals.get('debt_ebitda', None)
        passed = (roe > 12.0) and (margin > 5.0) and (debt_ebitda is None or debt_ebitda <= 3.0)
        notes = []
        if not passed:
            if roe <= 12.0:
                notes.append('ROE below threshold')
            if margin <= 5.0:
                notes.append('Net margin below threshold')
            if debt_ebitda is not None and debt_ebitda > 3.0:
                notes.append('High debt/EBITDA')
        return {'symbol': symbol, 'passed': passed, 'notes': notes}
    def validate(self):
        return True


class SimpleDecisionEngine(DecisionEngine):
    def decide(self, candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
        # Candidates expected to contain one dict with keys: fundamental, technical, risk_halt
        c = candidates[0]
        tech = c.get('technical', {})
        fund = c.get('fundamental', {})
        risk_halt = c.get('risk_halt', False)
        risk_engine = c.get('risk_engine')
        reasons = []
        if risk_halt:
            return {'decision_state': 'NO_TRADE', 'reasons': ['Risk halt active']}

        if not fund.get('passed'):
            return {'decision_state': 'NO_TRADE', 'reasons': fund.get('notes', [])}

        signal = tech.get('signal')
        # Aggregate signals: require at least one buy signal; future: could weight signals
        buy_signals = ['BREAKOUT_BUY', 'TREND_FOLLOW_BUY']
        if signal in buy_signals:
            reasons.append('Technical signal: ' + signal)
            # risk-adjusted sizing if risk_engine provided
            size_info = None
            if risk_engine is not None:
                # require stop_distance passed in tech reasons (example) or default
                stop_distance = tech.get('indicators', {}).get('last_close', 1) - tech.get('indicators', {}).get('support', 0)
                if stop_distance <= 0:
                    stop_distance = 1.0
                size = risk_engine.position_size(portfolio_capital=c.get('portfolio_capital', 100000.0),
                                                 stop_distance=stop_distance,
                                                 price=tech.get('last_close', 1.0),
                                                 volatility=tech.get('indicators', {}).get('volatility'),
                                                 volatility_avg=tech.get('indicators', {}).get('volatility_avg'))
                size_info = {'size': size}
                reasons.append(f'Position size computed: {size}')
            return {'decision_state': 'BUY_CANDIDATE', 'reasons': reasons, 'size_info': size_info}

        return {'decision_state': 'HOLD', 'reasons': ['No actionable signal']}
    def validate(self):
        return True


class SimpleExplanationEngine(ExplanationEngine):
    def explain(self, decision: Dict[str, Any]) -> str:
        lines = [f"Decision: {decision.get('decision_state')}"]
        for r in decision.get('reasons', []):
            lines.append(f"- {r}")
        return '\n'.join(lines)
    def validate(self):
        return True
