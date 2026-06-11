"""Data contracts for the trading analysis system."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Literal, Optional
import re

from pydantic import BaseModel, Field, field_validator


_SYMBOL_PATTERN = re.compile(r"^[A-Z]{1,5}$")


class SymbolRequest(BaseModel):
    """Validated symbol request used by the package layer."""

    symbol: str
    timeframe: str = Field(default="1d")

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, value: str) -> str:
        if not _SYMBOL_PATTERN.fullmatch(value):
            raise ValueError("symbol must contain 1 to 5 uppercase letters")
        return value

    @field_validator("timeframe")
    @classmethod
    def validate_timeframe(cls, value: str) -> str:
        if value != "1d":
            raise ValueError("timeframe must be '1d'")
        return value


class PriceBar(BaseModel):
    """Standardized daily candlestick bar."""

    open: float
    high: float
    low: float
    close: float
    volume: int
    timestamp: datetime


class IndicatorSnapshot(BaseModel):
    """Technical indicator values for a symbol."""

    rsi: Optional[float] = None
    macd: Dict[str, float] = Field(default_factory=dict)
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None
    momentum: Optional[float] = None


class RiskSnapshot(BaseModel):
    """Risk metrics for a candidate decision."""

    volatility: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    risk_reward_ratio: Optional[float] = None


class DecisionResult(BaseModel):
    """Deterministic analysis output."""

    symbol: str
    decision_state: Literal["BUY_CANDIDATE", "SELL_CANDIDATE", "HOLD", "NO_TRADE"]
    reasons: List[str] = Field(default_factory=list)
    indicator_snapshot: IndicatorSnapshot
    risk_snapshot: RiskSnapshot