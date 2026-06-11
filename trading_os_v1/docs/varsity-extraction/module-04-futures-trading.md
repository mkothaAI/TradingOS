# Module 4: Futures Trading

## Overview
Introduces futures contracts, derivatives, hedging strategies, and mechanics of leveraged trading. Essential for understanding derivatives-based risk management and position sizing.

## Key Concepts

- **Derivatives**: Financial contracts whose value is derived from underlying assets
- **Forward vs. Futures**: Forward is OTC, customized; Futures are exchange-traded, standardized
- **Lot Size**: Standardized quantity per contract; affects position sizing and capital requirements
- **Contract Value**: Lot Size × Futures Price = total notional exposure
- **Hedging**: Using derivatives to reduce risk of adverse price movements
- **Leverage**: Futures require only margin (fraction of notional); amplifies both gains and losses
- **Mark-to-Market (M2M)**: Daily P&L settlement; losses may trigger margin calls
- **Basis Risk**: Difference between spot and futures price; relevant for hedging effectiveness

## Explicit Rules & Principles

1. **Contract Standardization Rule**: Futures have fixed lot sizes, expiration dates, and settlement procedures
2. **Margin Requirement Rule**: Initial margin must be maintained; shortfall triggers margin call
3. **Daily Settlement Rule**: All P&L settled daily; no overnight positions can escape M2M adjustments
4. **Leverage Rule**: Never exceed 2:1 total leverage on futures positions (capital preservation)
5. **Hedging Principle**: Use futures to reduce risk of underlying cash position, not to speculate
6. **Expiration Rule**: Monitor expiration dates; roll or close positions before final settlement
7. **Liquidity Rule**: Trade only active contract months; avoid illiquid contracts with wide spreads
8. **Correlation Hedging**: Use asset futures with high correlation to underlying; track basis daily

## Formulas & Measurable Logic

### Position Sizing in Futures
- **Contract Value** = Lot Size × Futures Price
- **Notional Exposure** = Number of Contracts × Lot Size × Futures Price
- **Margin Required** = Notional Exposure × Margin_Rate (typically 5-15%)
- **Position Size** = Available_Capital × Leverage_Limit / Notional_Price_Per_Contract

### Hedging Calculations
- **Hedge Ratio** = (σ_Spot / σ_Futures) × (Correlation)
- **Number of Contracts to Hedge** = (Portfolio_Value / Contract_Value) × Hedge_Ratio
- **Basis** = Spot Price - Futures Price
- **Basis Risk** = Change in Basis during holding period

### P&L Mechanics
- **Daily P&L** = (New Price - Previous Price) × Lot Size × Number of Contracts
- **Unrealized P&L** = (Mark_Price - Entry_Price) × Lot Size × Contracts
- **Realized P&L** = (Exit_Price - Entry_Price) × Lot Size × Contracts - Commissions

### Margin Management
- **Margin Utilization** = (Margin_Used / Available_Margin) × 100%
- **Margin Call Threshold**: Typically 50% margin utilization triggers alert
- **Liquidation Risk**: 75%+ utilization means forced closure on adverse move

## Psychological Guidance

- **Leverage Temptation**: Futures leverage makes gains feel achievable; resist over-sizing
- **Daily Settlement Pressure**: Daily losses can trigger emotional panic; prepare for volatility
- **Margin Spiral**: Margin calls can force liquidation at worst prices; maintain 30%+ buffer
- **Hedging Discipline**: Hedging feels like "leaving money on the table" when price moves favorably; maintain discipline anyway
- **Expiration Anxiety**: Approaching expiration can create artificial price movements; avoid last trading days
- **Overconfidence in Leverage**: Easy access to leverage breeds overconfidence; treat as liability, not asset

## Risk-Related Guidance

1. **Margin Call Risk**: Define acceptable margin utilization (max 50%); never exceed 60%
2. **Leverage Amplification**: Futures losses scale with leverage; 2:1 leverage means 2x losses in downdraft
3. **Gap Risk**: Overnight gaps can skip through stop-loss levels; reduce futures position size vs. cash
4. **Liquidity Risk**: Closing large futures positions quickly can incur significant slippage
5. **Expiration Risk**: Avoid holding through final settlement; roll to next contract 1 week before expiration
6. **Counterparty Risk**: While exchange-cleared, basis risk and hedging mismatches still exist
7. **Correlation Breakdown**: Hedging assumes historical correlation; monitor daily and adjust if correlation collapses
8. **Roll Risk**: When rolling to next contract month, avoid trading at wide basis/spread

## Implementation Candidates for trading-os-v1

- **Position Size Calculator**: Given capital, margin requirement, and futures price, calculate max position size
- **Margin Monitor**: Track margin utilization continuously; alert at 40%, 50%, 60% thresholds
- **Contract Expiration Tracker**: Flag contracts approaching expiration; recommend rolling or closing
- **Basis Calculator**: For hedging strategies, compute and monitor basis daily
- **Hedge Effectiveness Validator**: Verify correlation and hedge ratio; alert if correlation drops below 0.5
- **Leverage Limit Enforcer**: Prevent positions that exceed 2:1 total leverage
- **Margin Call Alert System**: Notify trader if margin utilization approaches liquidation threshold
- **Liquidity Checker**: Verify contracts have minimum average daily volume before trading

## Educational Only (Do Not Code)

- Advanced derivatives structures (options on futures, swaptions, etc.)
- Theoretical pricing models (Black-Scholes, binomial trees)
- Volatility term structure and contango/backwardation analysis
- Complex hedging scenarios and multi-leg strategies
- Historical derivatives crises and lessons learned
- Comparative analysis of hedging instruments and their tradeoffs

## Candidate Engine Mappings

| Concept | Mapped To | Status |
|---------|-----------|--------|
| Position sizing | Trade execution gate | v1-Safe |
| Margin utilization | Risk monitoring | v1-Safe |
| Contract expiration | Position management | v1-Safe |
| Basis risk | Hedge validator | v1-Candidate |
| Leverage limit | Portfolio risk cap | v1-Safe |

## v1-Safe Rules

1. **No Futures Position** can exceed 2:1 leverage ratio (strictly enforced)
2. **Margin Utilization** must stay below 50% at all times; 60% triggers reduction requirement
3. **Expiration Management**: All futures positions closed or rolled 5 days before expiration
4. **Hedge Requirement**: Futures positions only if hedging underlying cash position or part of defined system
5. **Liquidity Gate**: Trade only contracts with minimum 1M average daily volume
6. **Basis Monitoring**: For hedging strategies, track basis daily; recalculate hedge ratio weekly
7. **Stop-Loss Enforcement**: Mechanical stop-loss set immediately on entry; never extended after entry
8. **Position Consolidation**: Maximum 3 active futures contracts per account; forces discipline

## Out-of-Scope for v1

- Exotic derivatives (options on futures, variance swaps, etc.)
- Volatility forecasting and trading volatility directly
- Complex multi-leg spreads and arbitrage strategies
- Leverage >2:1 or margin borrowing beyond basic futures margin
- Algorithmic/high-frequency execution strategies
- Theoretical pricing and delta hedging
- Cross-market arbitrage and basis trading
- Interest rate derivatives and macro hedging
