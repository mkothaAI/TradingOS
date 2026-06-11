# Module 10: Trading Systems

## Overview
Covers systematic approaches to trading, including pair trading methodologies, reaction to news events, and deterministic rule-based systems. Core to algorithmic trading design.

## Key Concepts

- **Pair Trading**: Identifying and trading two correlated assets to exploit temporary divergence
- **Statistical Arbitrage**: Trading based on statistical relationships rather than fundamental analysis
- **Mean Reversion**: Assets that diverge from average tend to return to mean
- **Spread Trading**: Long one asset, short another; profit from spread compression/expansion
- **News Reaction Patterns**: Markets have systematic reactions to news events (PSU recapitalization case study)
- **System Discipline**: Follow rules mechanically; avoid subjective override
- **Backtesting**: Historical validation of system performance before live deployment

## Explicit Rules & Principles

1. **Pair Selection Rule**: Identify two assets with historically high correlation (ρ > 0.7)
2. **Tracking Method**: Calculate spread between two prices over time
3. **Straight Line Method**: Project historical trend line and identify deviations from expected value
4. **Entry Signal**: Enter when spread deviates >2σ (two standard deviations) from mean
5. **Exit Signal**: Exit when spread returns to mean or within 0.5σ
6. **Position Sizing in Pairs**: Size positions so P&L is symmetric (lose on one, gain proportionally on other)
7. **News Reaction Rule**: Markets systematically overreact or underreact to news; exploit the pattern
8. **System Override Prohibition**: Never violate system rules due to emotional conviction
9. **Rebalancing Rule**: Adjust pair ratios if historical correlation breaks down

## Formulas & Measurable Logic

### Pair Trading Metrics
- **Spread** = Closing_Price_Asset1 - Closing_Price_Asset2
- **Spread Mean** = Average(Spread) over lookback period (e.g., 252 days)
- **Spread Std Dev** = StdDev(Spread)
- **Z-Score** = (Current_Spread - Mean) / StdDev
- **Entry Threshold**: |Z-Score| > 2.0 (indicate spread has deviated significantly)
- **Exit Threshold**: |Z-Score| < 0.5 (mean reversion has occurred)

### Spread-Based Position Sizing
- **Hedge Ratio** = σ₁ / σ₂ (volatility ratio)
- **Position_Size_Asset1** = Capital / (Price1 * Hedge_Ratio)
- **Position_Size_Asset2** = Capital / Price2 (offsetting position)

### News Reaction Metrics
- **Reaction Intensity** = |Price_Change_on_News| / Average_Daily_Range
- **Holding Period**: Determine typical decay time of news impact (hours, days, weeks)
- **Reversal Probability**: Historical likelihood that initial overreaction reverses

## Psychological Guidance

- **System Trust**: Requires discipline to follow automated rules even when they feel wrong
- **Curve-Fitting Temptation**: Resist over-optimizing backtest parameters to match past data
- **News Bias**: Avoid letting headlines override statistical signals
- **Correlation Decay**: Understand that historical relationships can break; monitor continuously
- **Regime Shifts**: Recognize when market conditions invalidate system assumptions
- **Drawdown Resilience**: Accept that all systems have periods of underperformance
- **Objectivity**: Remove emotion from entry/exit; follow signals mechanically

## Risk-Related Guidance

1. **Correlation Breakdown Risk**: When pair correlation collapses, losses can be unlimited; enforce correlation monitoring
2. **Spread Widening Risk**: Spreads can widen beyond 3σ; define maximum acceptable loss and stop out
3. **Liquidity Risk**: Ensure both assets in pair have sufficient volume to exit without slippage
4. **News Gap Risk**: Large overnight gaps can skip through stop-loss levels; limit position size
5. **Leverage Risk**: Pair trading often involves margin; never exceed 2:1 leverage; enforce strict limits
6. **Regime Risk**: System loses validity when market regime shifts (e.g., crisis, regime change); disable system and analyze
7. **Execution Risk**: Ensure both legs execute simultaneously; asynchronous execution introduces additional risk
8. **Drawdown Ceiling**: Define maximum system drawdown; pause system if exceeded, analyze, and reset

## Implementation Candidates for trading-os-v1

- **Pair Correlation Tracker**: Monitor correlation between asset pairs continuously; alert if drops below threshold
- **Spread Calculator**: Compute spread, mean, std dev, and Z-score for identified pairs
- **Entry/Exit Signal Generator**: Generate signals when Z-score crosses thresholds
- **Pair Validator**: Check both assets have adequate liquidity, similar trading hours, and high correlation
- **Spread Dashboard**: Display historical spread chart with mean bands and Z-score levels
- **News Event Reactor**: Identify news events in data; track price reaction pattern
- **System Backtester**: Historical testing of pair trading rules on past data
- **Regime Detector**: Identify market regime shifts; suspend system when detected
- **P&L Attribution**: Break down P&L by component (mean reversion, news reaction, slippage)

## Educational Only (Do Not Code)

- Historical case studies of pair trading breakdowns (LTCM, correlations in crises)
- Advanced statistical arbitrage techniques (cointegration, factor models)
- Multi-leg strategies and complex hedging
- Machine learning for pattern discovery
- Advanced backtesting and stress testing methodologies
- Portfolio-level system coordination

## Candidate Engine Mappings

| Concept | Mapped To | Status |
|---------|-----------|--------|
| Pair correlation tracking | Position validation | v1-Safe |
| Spread calculation & Z-score | Signal generation | v1-Safe |
| Mean reversion signal | Trade decision | v1-Candidate |
| News reaction patterns | Event-based signals | v1-Candidate |
| System discipline enforcement | Trade execution gate | v1-Safe |

## v1-Safe Rules

1. **Pair Requirement**: All multi-leg strategies require correlation check (ρ > 0.7 over last 252 days)
2. **Spread Monitoring**: Calculate and report spread Z-score for every pair position
3. **Entry Rules**: Generate signal only when Z-score > 2.0 for mean reversion trades
4. **Exit Rules**: Close position when Z-score < 0.5 or loss exceeds defined threshold
5. **Liquidity Check**: Verify both assets have minimum average daily volume before entry
6. **Correlation Decay Halt**: If correlation drops below 0.5, close position and alert trader
7. **No Subjective Override**: Mechanical enforcement of system rules; document any manual override with reason
8. **Regime Validation**: Include regime shift detection; flag when system assumptions may be invalid

## Out-of-Scope for v1

- Complex multi-leg spread strategies (3+ leg structures)
- Cointegration-based pair finding (requires statistical/ML infrastructure)
- Machine learning for pattern discovery or system adaptation
- Dynamic leverage adjustment based on volatility
- Portfolio-level spread correlation analysis
- Advanced stress testing and scenario analysis
- News sentiment analysis and classification
- Real-time news feed integration
- High-frequency trading tactics
