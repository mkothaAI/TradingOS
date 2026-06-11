# Module 2: Technical Analysis

## Overview
Comprehensive technical analysis instruction covering candlestick patterns, price actions, and chart-based analysis for identifying trade opportunities.

## Key Concepts

- **OHLC Data**: Open, High, Low, Close prices form the basis of technical analysis
- **Candlestick Patterns**: Bullish and bearish formations signal potential price direction
- **Price Action**: Market reaction to support/resistance levels is predictive
- **Trend Identification**: Uptrend, downtrend, sideways consolidation as market states
- **Volume Analysis**: Confirms price movements and identifies breakout strength
- **Support & Resistance**: Key price levels where reversals or continuations occur

## Explicit Rules & Principles

1. **Bullish Day Definition**: Close > Open (green candle) indicates buyer strength
2. **Bearish Day Definition**: Close < Open (red candle) indicates seller strength
3. **Doji Pattern**: Open ≈ Close with long wicks = indecision, potential reversal signal
4. **Gap Up/Down**: Opening price differs significantly from previous close = strong sentiment shift
5. **Volume Confirmation**: Strong moves must be accompanied by above-average volume to be valid
6. **Trend Line Breaks**: Break of established trend line signals potential trend reversal
7. **Support/Resistance Bounce**: Price should bounce off established levels, not break through easily
8. **Higher Highs & Higher Lows**: Uptrend continues; lower highs & lower lows confirm downtrend

## Formulas & Measurable Logic

### Candlestick Metrics
- **Body Size** = |Close - Open|
- **Upper Wick** = High - max(Open, Close)
- **Lower Wick** = min(Open, Close) - Low
- **Range** = High - Low

### Pattern Recognition Thresholds
- **Long Body**: Range > Average_Range (last 20 periods)
- **Long Wick**: Wick_Length > Body_Size * 2
- **Doji**: |Close - Open| < Range * 0.1 (near indecision threshold)

### Support/Resistance Levels
- **Pivot Point** = (High + Low + Close) / 3
- **Support** = Recent lows where price reversed upward
- **Resistance** = Recent highs where price reversed downward

## Psychological Guidance

- Technical patterns reflect collective market psychology (fear, greed, indecision)
- Volume spikes indicate strong conviction; low volume moves may reverse suddenly
- Patience in waiting for confirmation candles reduces false signals
- Avoiding "reading into" random noise is as important as pattern recognition
- Recognize that past patterns do not guarantee future performance

## Risk-Related Guidance

- **Dealing with Unexpected Price Moves**: Pre-defined stop-losses are essential before entering trades
- **Risk in Pattern Initiation**: Early pattern recognition risks increased whipsaws; wait for confirmation
- **Volume Risk**: Low-volume breakouts have higher failure rates
- **Gap Risk**: Overnight gaps can exceed stop-loss protection; limit position size accordingly
- **Volatility Risk**: Higher volatility reduces pattern reliability; reduce position size or skip setups

## Implementation Candidates for trading-os-v1

- **Candlestick Pattern Detector**: Identify doji, hammer, shooting star, engulfing patterns from OHLC data
- **Trend State Classifier**: Classify current market as uptrend, downtrend, or consolidation
- **Support/Resistance Identifier**: Detect recent pivot points and key levels for trade placement
- **Volume Confirmer**: Check that breakouts exceed average volume threshold before signaling
- **Pattern Validity Checker**: Enforce confirmation rules (e.g., 2-candle confirmation before trade signal)
- **Volatility Adjuster**: Scale position size based on current volatility relative to average

## Educational Only (Do Not Code)

- Deep historical pattern catalogs and their probabilities (domain knowledge, not algorithmic)
- Visual chart reading skills and intuition development
- Market microstructure and order flow analysis
- Advanced charting techniques and exotic patterns
- Comparative effectiveness of different timeframes

## Candidate Engine Mappings

| Concept | Mapped To | Status |
|---------|-----------|--------|
| Bullish/Bearish candles | Indicator Snapshot | v1-Safe |
| Volume confirmation | Trade validation | v1-Safe |
| Support/Resistance levels | Entry/Exit levels | v1-Candidate |
| Trend classification | Market state (indicator) | v1-Safe |
| Pattern detection | Signal generation | v1-Candidate |

## v1-Safe Rules

1. Classify each candle as bullish (close > open) or bearish (close < open)
2. Compute volume moving average and flag breakouts exceeding threshold
3. Identify support/resistance as recent local extrema within lookback window
4. Calculate and report trend state (uptrend: HH & HL, downtrend: LL & LH)
5. Require volume confirmation for trade signals (breakout volume > 1.5x average)
6. Always include support/resistance levels in trade decision reasoning

## Out-of-Scope for v1

- Exotic pattern recognition (head-and-shoulders, butterfly, etc.) without clear triggering rules
- Subjective trend line drawing and interpretation
- Seasonal or cyclical pattern analysis
- Comparative effectiveness studies across markets/assets
- Visual chart rendering or visualization backend
- Real-time technical analysis dashboard features
