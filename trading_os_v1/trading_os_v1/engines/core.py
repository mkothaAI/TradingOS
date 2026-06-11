from typing import List, Dict, Any, Optional

from .base import BaseEngine
from .models import MappingEntry


class UniverseEngine(BaseEngine):
    def evaluate_universe(self, market_data: Dict[str, Any]) -> List[str]:
        """Return list of candidate symbols after applying universe filters."""
        raise NotImplementedError


class FundamentalEngine(BaseEngine):
    def score_fundamentals(self, symbol: str, fundamentals: Dict[str, Any]) -> Dict[str, Any]:
        """Return fundamental scores and pass/fail flags."""
        raise NotImplementedError


class TechnicalEngine(BaseEngine):
    def generate_signals(self, symbol: str, price_bars: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Return list of technical signals for a symbol."""
        raise NotImplementedError


class EventEngine(BaseEngine):
    def handle_event(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process incoming events (news, corporate actions) and emit alerts/signals."""
        raise NotImplementedError


class DecisionEngine(BaseEngine):
    def decide(self, candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Make trade decisions given candidate signals, fundamentals, and risk snapshots."""
        raise NotImplementedError


class ExplanationEngine(BaseEngine):
    def explain(self, decision: Dict[str, Any]) -> str:
        """Return human-readable rationale and audit trail for a decision."""
        raise NotImplementedError
