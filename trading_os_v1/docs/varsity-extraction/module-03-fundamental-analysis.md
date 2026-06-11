# Module 3: Fundamental Analysis

## Overview
Covers business-level analysis for understanding company health, growth prospects, and valuation. Foundation for identifying quality securities worthy of capital deployment.

## Key Concepts

- **CAGR (Compound Annual Growth Rate)**: Long-term growth metric for revenues, earnings, book value
- **Holistic Business Study**: Understanding entire business ecosystem, not just single metrics
- **Wealth Destructors**: Management failures, bad capital allocation decisions that destroy shareholder value
- **Margin Analysis**: Gross, operating, and net margins indicate business efficiency and pricing power
- **Return on Equity (ROE)**: Measures how effectively management deploys shareholder capital
- **Growth vs. Quality**: High growth without profitability is risky; quality compounds over time
- **Competitive Moat**: Sustainable competitive advantages that protect margins and market position

## Explicit Rules & Principles

1. **Quality Before Growth**: A company with consistent 15% ROE and 8% growth is better than 40% growth with negative ROE
2. **Margin Sustainability**: Improving margins must come from pricing power or efficiency, not accounting tricks
3. **Capital Allocation Rule**: Management's ability to deploy capital wisely determines long-term returns
4. **Debt Analysis**: High debt + declining earnings = distress; manageable debt + growing earnings = leverage benefit
5. **Free Cash Flow Focus**: Accounting earnings can lie; cash flow doesn't; prioritize FCF over reported income
6. **Cyclical vs. Structural Growth**: Cyclical rebounds are not investments; structural improvements are worth studying
7. **Valuation Discipline**: Even good businesses are bad investments at wrong prices; never overpay
8. **Management Quality**: Honest, competent management beats brilliant strategy with dishonest execution
9. **Dividend Analysis**: Sustainable dividends indicate confidence in cash generation; cuts signal distress

## Formulas & Measurable Logic

### Growth Metrics
- **CAGR** = (Ending_Value / Beginning_Value)^(1/Years) - 1
- **Revenue CAGR** = (Revenue_Year_N / Revenue_Year_1)^(1/N-1) - 1
- **Earnings CAGR** = (EPS_Year_N / EPS_Year_1)^(1/N-1) - 1

### Profitability Metrics
- **Gross Margin** = (Revenue - COGS) / Revenue
- **Operating Margin** = EBIT / Revenue
- **Net Margin** = Net Income / Revenue
- **Margin Trend** = Current Margin vs. 5-Year Average (improvement or deterioration)

### Return Metrics
- **Return on Equity (ROE)** = Net Income / Shareholders' Equity
- **Return on Assets (ROA)** = Net Income / Total Assets
- **Return on Invested Capital (ROIC)** = NOPAT / (Debt + Equity)

### Valuation Metrics
- **P/E Ratio** = Stock_Price / EPS
- **Price-to-Book (P/B)** = Market_Cap / Book_Value
- **PEG Ratio** = P/E / Growth_Rate (incorporate growth into valuation)
- **EV/EBITDA** = Enterprise_Value / EBITDA

### Cash Flow Analysis
- **Free Cash Flow (FCF)** = Operating Cash Flow - Capital Expenditures
- **FCF Yield** = FCF / Market Cap
- **FCF Growth** = (FCF_Year_N - FCF_Year_1) / FCF_Year_1

## Psychological Guidance

- **Story Bias**: Compelling narratives can blind investors to deteriorating fundamentals; demand data
- **Management Halo Effect**: Charismatic leaders may hide poor capital allocation; focus on results, not personality
- **Extrapolation Bias**: Past growth does not guarantee future growth; understand why growth occurred
- **Anchoring to Entry Price**: Forget what you paid; evaluate at current fundamentals
- **Recency Bias**: One good quarter doesn't validate long-term thesis; monitor multi-year trends
- **Confirmation Bias**: Actively seek deterioration signals, not just supporting evidence

## Risk-Related Guidance

1. **Deteriorating Margins Risk**: When margins compress despite stable or growing revenue, investigate cause
2. **Debt Escalation Risk**: Growing debt + stagnant earnings = financial distress risk; monitor debt/EBITDA
3. **Capital Allocation Failure**: Acquisitions or buybacks at bubble valuations destroy shareholder wealth
4. **Management Change Risk**: New management with different philosophy can destroy value
5. **Competitive Pressure Risk**: Deteriorating ROIC often signals competitive pressure; reassess moat
6. **Accounting Manipulation Risk**: Watch for changes in revenue recognition, inventory valuation, or provisions
7. **Cyclical Peak Risk**: Don't confuse cyclical earnings peaks with structural improvements
8. **Liquidity Risk**: Even fundamentally sound companies face distress if liquidity dries up

## Implementation Candidates for trading-os-v1

- **Fundamental Health Validator**: Compute ROE, margins, FCF yield; flag if below quality thresholds
- **Trend Analyzer**: Compute CAGR and margin trends; alert if deteriorating below threshold
- **Valuation Screener**: Check P/E, P/B, PEG against sector averages; flag overvaluation
- **Management Quality Flag**: Extract management change events and highlight for manual review
- **Debt Risk Monitor**: Calculate debt/EBITDA ratio; alert if >3.0 or increasing
- **Earnings Quality Check**: Compare reported earnings to FCF; flag large divergences
- **Dividend Sustainability**: Analyze dividend payout ratio relative to FCF; alert if unsustainable
- **Competitive Moat Indicator**: Track ROIC trend; sustained >15% ROIC indicates strong moat

## Educational Only (Do Not Code)

- Deep-dive business model analysis and industry dynamics
- Comparative company analysis and competitive positioning
- Qualitative management assessment and board evaluation
- Industry disruption analysis and structural change assessment
- Detailed financial statement forensics and accounting analysis
- Historical case studies of value creation and destruction

## Candidate Engine Mappings

| Concept | Mapped To | Status |
|---------|-----------|--------|
| ROE & margin quality | Fundamental health check | v1-Candidate |
| CAGR trend analysis | Growth validation | v1-Candidate |
| FCF yield | Valuation validator | v1-Candidate |
| Debt/EBITDA ratio | Risk check | v1-Safe |
| Margin trend | Health indicator | v1-Safe |

## v1-Safe Rules

1. **Quality Gate**: Only consider companies with ROE > 12% and net margin > 5% (quality threshold)
2. **Growth Validation**: Verify reported growth through FCF growth (at least 70% correlation)
3. **Margin Monitoring**: Alert if net margin declines >200bps vs. 5-year average (deterioration signal)
4. **Debt Ceiling**: Flag positions if debt/EBITDA exceeds 3.0 or is increasing
5. **Valuation Discipline**: Apply PEG-based maximum P/E (don't overpay regardless of growth story)
6. **Dividend Safety**: Flag if payout ratio > 60% or declining (potential cut risk)
7. **Management Stability**: Document management changes; require manual re-evaluation if CEO/CFO changes

## Out-of-Scope for v1

- Deep business model forensics and qualitative analysis
- Industry structure and competitive dynamics assessment
- Forward earnings forecasting or revenue projections
- Merger and acquisition impact analysis
- Scenario-based valuation and stress testing
- Detailed financial statement forensics
- ESG (Environmental, Social, Governance) analysis
- Geopolitical and regulatory risk assessment
