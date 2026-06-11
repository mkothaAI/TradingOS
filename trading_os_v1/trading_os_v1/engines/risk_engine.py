from typing import List, Optional
from .base import BaseEngine
from .models import MappingEntry


class RiskEngine(BaseEngine):
    """Simple RiskEngine implementing v1-Safe rules from Varsity extraction.

    Implemented rules (from mapping):
    - No trade exceeds 2% of portfolio capital at risk
    - Reduce position size if volatility > 1.5x average
    - Halt trading if monthly drawdown exceeds -2%
    - Enforce stop-loss requirement (check flag)
    """

    def __init__(self, name: str, mappings: List[MappingEntry],
                 position_risk_pct: float = 0.02,
                 volatility_limit_mul: float = 1.5,
                 monthly_drawdown_limit: float = -0.02):
        super().__init__(name, mappings)
        self.position_risk_pct = position_risk_pct
        self.volatility_limit_mul = volatility_limit_mul
        self.monthly_drawdown_limit = monthly_drawdown_limit

    def validate(self):
        # basic check that required rules exist in mappings
        if not any('No trade exceeds' in (m.principle or '') for m in self.mappings):
            # not fatal; mappings may be partial
            pass

    def position_size(self,
                      portfolio_capital: float,
                      stop_distance: float,
                      price: float,
                      volatility: Optional[float] = None,
                      volatility_avg: Optional[float] = None) -> int:
        """Compute position size (number of shares/contracts) given risk rules.

        - `stop_distance` is absolute price distance from entry to stop (same units as price)
        - Risk per share = stop_distance * 1
        - Max risk per trade = portfolio_capital * position_risk_pct
        - If volatility and volatility_avg provided and volatility > volatility_limit_mul * volatility_avg,
          scale down size by (volatility_limit_mul * volatility_avg) / volatility

        Returns integer size (floor).
        """
        if stop_distance <= 0 or price <= 0:
            return 0
        max_risk = portfolio_capital * self.position_risk_pct
        base_size = int(max_risk // stop_distance)
        scale = 1.0
        if volatility is not None and volatility_avg is not None and volatility > 0 and volatility_avg > 0:
            if volatility > (self.volatility_limit_mul * volatility_avg):
                scale = (self.volatility_limit_mul * volatility_avg) / volatility
        size = int(base_size * scale)
        return max(size, 0)

    def should_halt_trading(self, monthly_drawdown_pct: float) -> bool:
        """Return True if monthly drawdown exceeds configured threshold (negative value expected)."""
        return monthly_drawdown_pct <= self.monthly_drawdown_limit

    def require_stop_loss(self, trade_meta: dict) -> bool:
        """Enforce that trade_meta contains a stop-loss flag or price.

        Returns True if stop-loss is present, False otherwise.
        """
        # trade_meta expected keys: 'stop_price' or 'has_stop'
        if 'stop_price' in trade_meta and trade_meta['stop_price'] is not None:
            return True
        if trade_meta.get('has_stop'):
            return True
        return False

    # Futures / margin related checks
    def check_leverage_allowed(self, leverage: float) -> bool:
        """Return True if leverage is within allowed cap (2:1)."""
        try:
            return float(leverage) <= 2.0
        except Exception:
            return False

    def check_margin_utilization(self, current_util_pct: float) -> str:
        """Check margin utilization and return status: 'ok', 'reduce', 'exceeded'.

        - 'ok' if <= 50%
        - 'reduce' if >50% and <=60%
        - 'exceeded' if >60%
        """
        if current_util_pct <= 50.0:
            return 'ok'
        if current_util_pct <= 60.0:
            return 'reduce'
        return 'exceeded'

    def check_expiration_management(self, days_to_expiry: int) -> bool:
        """Return True if within safe window to hold; False if should roll/close.

        Mapping rule: close/roll all futures 5 days before expiration.
        """
        return days_to_expiry > 5

    def check_position_consolidation(self, active_futures_count: int) -> bool:
        """Enforce maximum active futures contracts per account (max 3)."""
        return active_futures_count <= 3
