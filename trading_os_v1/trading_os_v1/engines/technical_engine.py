from typing import List, Dict, Any
import statistics
from .base import BaseEngine
from .models import MappingEntry


class TechnicalEngineImpl(BaseEngine):
    """Concrete TechnicalEngine implementing rules from Module 02 v1-Safe Rules.

    Implemented rules:
    - Classify candle bullish/bearish
    - Compute volume moving average and flag breakouts >1.5x
    - Identify support/resistance as recent extrema
    - Calculate trend state (HH & HL => uptrend; LL & LH => downtrend)
    - Compute volatility (stddev of returns)
    """

    def __init__(self, name: str, mappings: List[MappingEntry], lookback: int = 20):
        super().__init__(name, mappings)
        self.lookback = lookback

    def validate(self):
        return True

    def generate_signals(self, symbol: str, price_bars: List[Dict[str, Any]]) -> Dict[str, Any]:
        """price_bars: list of dicts with keys open, high, low, close, volume, timestamp

        Returns dict with indicators and boolean signals.
        """
        if not price_bars:
            return {}
        bars = price_bars[-self.lookback:]
        last = bars[-1]

        # Candle classification
        candle = 'bullish' if last['close'] > last['open'] else ('bearish' if last['close'] < last['open'] else 'doji')

        # Volume MA
        volumes = [b['volume'] for b in bars if b.get('volume') is not None]
        vol_ma = statistics.mean(volumes) if volumes else 0
        vol_confirm = False
        if vol_ma > 0 and last['volume'] > 1.5 * vol_ma:
            vol_confirm = True

        # Support/Resistance
        highs = [b['high'] for b in bars]
        lows = [b['low'] for b in bars]
        support = min(lows) if lows else None
        resistance = max(highs) if highs else None

        # Trend classification using simple HH/HL & LL/LH over last 3 bars
        trend = 'consolidation'
        if len(bars) >= 3:
            h1, h2, h3 = bars[-3]['high'], bars[-2]['high'], bars[-1]['high']
            l1, l2, l3 = bars[-3]['low'], bars[-2]['low'], bars[-1]['low']
            if h3 > h2 > h1 and l3 > l2 > l1:
                trend = 'uptrend'
            elif h3 < h2 < h1 and l3 < l2 < l1:
                trend = 'downtrend'

        # Volatility: stddev of returns
        closes = [b['close'] for b in bars]
        returns = []
        for i in range(1, len(closes)):
            prev = closes[i - 1]
            if prev != 0:
                returns.append((closes[i] - prev) / prev)
        vol = statistics.pstdev(returns) if returns else 0.0

        # Volatility adjuster factor (for position sizing)
        vol_factor = 1.0
        # Caller (Risk engine) will apply scaling; we compute ratio vs. avg vol
        # Use rolling average vol as vol_avg
        vol_avg = vol if vol > 0 else 0.0

        indicators = {
            'candle': candle,
            'volume_ma': vol_ma,
            'volume_confirm': vol_confirm,
            'support': support,
            'resistance': resistance,
            'trend': trend,
            'volatility': vol,
            'volatility_avg': vol_avg,
        }

        # Basic signal: breakout if close > resistance and volume_confirm
        signal = None
        reasons = []
        if resistance is not None and last['close'] > resistance and vol_confirm:
            signal = 'BREAKOUT_BUY'
            reasons.append('breakout above resistance with volume confirmation')
        elif trend == 'uptrend' and candle == 'bullish' and vol_confirm:
            signal = 'TREND_FOLLOW_BUY'
            reasons.append('uptrend with bullish candle and volume confirmation')
        else:
            signal = 'NO_SIGNAL'

        return {
            'symbol': symbol,
            'last_close': last['close'],
            'signal': signal,
            'reasons': reasons,
            'indicators': indicators,
        }
