# Module 9: Risk Management & Trading Psychology

## Overview
Critical module covering portfolio risk quantification, correlation analysis, position sizing, and psychological factors affecting trading decisions. Core to capital preservation.

## Key Concepts

- **Portfolio Variance**: Measure of total portfolio risk across holdings
- **Correlation Matrix**: Quantifies how different assets move together (diversification foundation)
- **Expected Return Calculation**: Weighted average of individual asset returns
- **Volatility & Standard Deviation**: Measures price dispersion and risk magnitude
- **Diversification Benefit**: Negative correlations reduce portfolio volatility below weighted average
- **Behavioral Finance**: Psychological biases drive trading decisions and often cause losses
- **Reflexivity vs. Reflectivity**: Market participants' beliefs and actions create feedback loops

## Explicit Rules & Principles

1. **Portfolio Expected Return**: E(R_p) = Sum(W_i * R_i) for each position i with weight W_i and return R_i
2. **Risk Aggregation**: Portfolio variance ≠ Sum(Individual Variances) due to correlation effects
3. **Diversification Works Only with Negative Correlation**: Positive correlation amplifies portfolio risk
4. **Leverage Amplifies Both Returns and Risks**: Margin use increases variance proportionally
5. **Rebalancing Rule**: Reset portfolio weights to target allocations periodically (quarterly/annually)
6. **Position Sizing Rule**: No single position should exceed acceptable portfolio volatility threshold
7. **Loss Cutting Rule**: Eliminate losing positions if conviction thesis is invalidated
8. **Psychological Discipline**: Emotional discipline is more important than analytical skill

## Formulas & Measurable Logic

### Portfolio Risk Metrics
- **Portfolio Expected Return** = W₁R₁ + W₂R₂ + ... + WₙRₙ
- **Portfolio Variance** = Σᵢ(Wᵢ²σᵢ²) + 2Σᵢ<ⱼ(WᵢWⱼρᵢⱼσᵢσⱼ)
  - Where ρᵢⱼ is correlation between assets i and j
- **Portfolio Standard Deviation** = √(Portfolio Variance)
- **Maximum Drawdown Tolerance** = Psychological + Financial Maximum Loss
- **Position Sizing** = Risk_Capital / (Stop_Loss_Distance * Contract_Size)

### Correlation Analysis
- **Correlation Coefficient** (ρ): Ranges from -1 (perfect inverse) to +1 (perfect positive)
  - ρ = -1: Ideal diversification (but rare)
  - ρ = 0: Independent assets
  - ρ = +1: Perfect correlation (no diversification benefit)
- **Covariance** = ρᵢⱼ × σᵢ × σⱼ

### Risk Metrics
- **Sharpe Ratio** = (R_portfolio - R_riskfree) / σ_portfolio (excess return per unit of risk)
- **Value at Risk (VaR)** = Maximum expected loss at given confidence level
- **Expected Shortfall** = Average loss beyond VaR threshold

## Psychological Guidance

- **Loss Aversion**: Humans fear losses 2-3x more than gains; plan for this in position sizing
- **Confirmation Bias**: Seek disconfirming evidence actively; don't just gather supporting information
- **Overconfidence**: Reduce position size when feeling most confident (paradoxical but protective)
- **Sunk Cost Fallacy**: Past losses are irrelevant to future decisions; don't "average down" out of desperation
- **Regret Aversion**: FOMO (fear of missing out) causes bad entries; wait for setup confirmation
- **Anchoring**: Forget entry price; focus on current risk-reward, not distance to entry
- **Reflexivity in Markets**: Your positions affect market psychology; position yourself accordingly
- **Emotional Discipline > Analytical Skill**: Ability to follow plan beats perfect analysis

## Risk-Related Guidance

1. **Portfolio Volatility Ceiling**: Define maximum acceptable daily/monthly drawdown percentage (e.g., 2% max daily loss)
2. **Position Sizing**: Risk no more than 1-2% of capital per trade
3. **Correlation Risk**: Reduce position size when holdings become too correlated (diversification fails)
4. **Leverage Prohibition**: Avoid margin/leverage unless married to defined risk derivatives
5. **Stop-Loss Enforcement**: Mechanical stop-losses prevent emotional extensions of losing positions
6. **Rebalancing Discipline**: Stick to rebalancing schedule even when strongly opposed (removes emotion)
7. **Drawdown Recovery**: After significant losses, reduce position size until psychological recovery occurs
8. **Risk Monitoring**: Track correlation matrix and volatility continuously; rebalance if correlations rise

## Implementation Candidates for trading-os-v1

- **Portfolio Risk Calculator**: Compute expected return, variance, and Sharpe ratio for proposed trades
- **Correlation Monitoring**: Track correlation matrix of current holdings; alert if diversification decays
- **Position Sizer**: Calculate maximum position size given portfolio risk ceiling and stop-loss distance
- **Volatility Adjuster**: Reduce position size automatically when portfolio or asset volatility spikes
- **Maximum Drawdown Enforcer**: Halt new trades if portfolio has exceeded defined drawdown threshold
- **Rebalancing Engine**: Generate rebalancing orders when weights drift beyond target bands
- **Risk Snapshot**: Include volatility, Sharpe ratio, VaR in decision results
- **Psychological Checkpoint**: Pre-trade validation that trader has not violated discipline (stop-loss honored, etc.)

## Educational Only (Do Not Code)

- Deep behavioral finance research and case studies
- Psychological profiles and risk tolerance questionnaires
- Trading psychology coaching and mentorship frameworks
- Historical trader biographies and lessons learned
- Market psychology crowd behavior analysis
- Comparative psychology across market regimes

## Candidate Engine Mappings

| Concept | Mapped To | Status |
|---------|-----------|--------|
| Portfolio variance | Risk Snapshot | v1-Safe |
| Correlation matrix | Position validation | v1-Safe |
| Sharpe ratio | Risk metric reporting | v1-Safe |
| Volatility adjustment | Position sizing | v1-Safe |
| Drawdown ceiling | Trade gating | v1-Safe |
| Loss-cutting rule | Position exit criteria | v1-Safe |

## v1-Safe Rules

1. **No trade** exceeds 2% of portfolio capital at risk
2. **Calculate volatility** continuously; reduce position size if volatility > 1.5x average
3. **Compute correlation** among current holdings quarterly; alert if > 0.7 average correlation
4. **Enforce stop-losses** mechanically; never override without explicit user confirmation + documented reason
5. **Halt trading** if realized losses exceed monthly drawdown ceiling (e.g., -2% of portfolio)
6. **Report Sharpe ratio** and expected return in every trade decision
7. **Rebalance** when portfolio weights drift >20% from targets
8. **Track maximum drawdown** and reduce future position size proportionally until recovery

## Out-of-Scope for v1

- Personalized psychological profiling or coaching
- Advanced derivatives strategies (options spreads, complex hedges)
- Custom correlation forecasting models
- Behavioral finance research or academic studies
- Market regime prediction and adaptive strategies
- Exotic risk metrics (CVaR, Worst-Case scenarios with forward-looking assumptions)
- Leverage or margin management (keep leverage banned in v1)
