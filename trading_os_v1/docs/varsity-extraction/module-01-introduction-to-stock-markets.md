# Module 1: Introduction to Stock Markets

## Overview
Foundational module covering inflation, savings, wealth creation, and market basics. Establishes the principle that capital preservation and long-term wealth creation require understanding risk and returns.

## Key Concepts

- **Inflation Impact**: Savings held in low-yield instruments lose purchasing power over time
- **Monthly Surplus**: Foundation for wealth creation; disciplined saving required before investing
- **Risk-Return Relationship**: Core principle that higher risk must correlate with higher returns
- **Long-term Wealth Destruction**: Poor investment choices can systematically erode capital
- **Time Value of Money**: Compounding effect over extended periods

## Explicit Rules & Principles

1. Risk and Return are positively correlated—higher expected returns require accepting higher risk
2. Wealth destruction occurs when investment returns fail to outpace inflation
3. Before investing, ensure a disciplined monthly surplus exists (foundational cash flow)
4. Long-term investing requires understanding the relationship between risk tolerance and return expectations
5. Capital preservation comes before capital appreciation in the investment hierarchy

## Formulas & Measurable Logic

- **Real Return** = Nominal Return - Inflation Rate
- **Wealth Destruction** occurs when: Investment Return < Inflation Rate
- **Purchasing Power Loss** = Initial_Capital * (1 - Real_Return)^Years

## Psychological Guidance

- Recognize that "low risk = low return" is not a market myth but a fundamental principle
- Understand personal risk tolerance before deploying capital
- Avoid the psychological trap of seeking returns without accepting corresponding risks
- Build emotional discipline around loss acceptance as part of long-term investing

## Risk-Related Guidance

- Never invest capital needed for emergency expenses (maintain 6-12 month reserve)
- Inflation-adjusted returns are the true measure of wealth preservation
- Negative real returns (below inflation) mean capital is being eroded regardless of nominal gains
- Risk acceptance must be proportional to time horizon (longer horizon can tolerate higher volatility)

## Implementation Candidates for trading-os-v1

- **Inflation adjuster module**: Calculate real returns and flag when nominal gains don't exceed inflation
- **Capital preservation threshold**: Enforce minimum return targets based on inflation rate
- **Risk-return validator**: Verify that proposed trades have risk-reward ratios consistent with market expectations
- **Surplus validation**: Pre-trade check that trader has adequate non-investment capital reserves

## Educational Only (Do Not Code)

- Historical examples of wealth destruction (company-specific, market-specific cases)
- Behavioral psychology of investors facing inflation
- Comparative investment vehicle analysis (stocks vs. bonds vs. real estate)
- Life-stage investment philosophy

## Candidate Engine Mappings

| Concept | Mapped To | Status |
|---------|-----------|--------|
| Real Returns > Inflation | Risk Snapshot validation | v1-Safe |
| Risk-Return correlation | Decision validation | v1-Safe |
| Surplus requirement | Pre-trade validation | v1-Safe |

## v1-Safe Rules

1. Do not execute trades if capital is below minimum emergency reserve (flag in decision result)
2. Calculate and display real return expectations (nominal - inflation)
3. Validate that proposed returns justify the risk exposure
4. Enforce positive real return threshold in portfolio analysis

## Out-of-Scope for v1

- Behavioral finance deep dives beyond risk tolerance assessment
- Comparative investment vehicle optimization
- Inflation forecasting or prediction
- Psychological coaching for traders
- Detailed wealth creation planning (outside trading mechanics)
