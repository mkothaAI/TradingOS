# My Trading OS v1 Specification

## Project Mission
My Trading OS is a capital preservation-focused trading analysis tool that provides data-driven insights for US equities using daily candlestick data. The system prioritizes risk management by preferring "no-trade" outcomes when evidence is inconclusive, ensuring users never expose capital unnecessarily.

## Approved Product Shape
- The backend symbolic/verdict layer remains the final authority for any trade outcome or gating decision.
- Advisory agents may support follow-up questions about a ticker analysis, but their prose output never becomes policy.
- The product shape includes structured planning outputs for entry, timing, stop-loss, hold time, waiting time, sizing, capital allocation, invalidation, and monitoring conditions.
- Options are a first-class analysis surface, including strike, expiry, implied volatility, greeks, liquidity, and spread quality.
- Evidence and market-state descriptions must explicitly label real-time, delayed, stale, or snapshot status.
- Post-entry monitoring is part of the product plan and must cover thesis breakage, stop-loss breaches, volatility shifts, macro shocks, and options-specific risk changes.

## Core Principles
- **Capital Preservation First**: No trade should ever risk capital
- **Evidence-Based Decisions**: No-trade is preferred when analysis is incomplete
- **Deterministic Rules**: Final trade decisions must follow strict, auditable logic
- **AI as Analyst, Not Trader**: AI summarizes news but does not invent prices/indicators/trade decisions or replace deterministic verdicts

## v1 Scope
### In-Scope
- US equities (NASDAQ, NYSE, etc.) analysis
- Daily candlestick data analysis
- Deterministic trade decision rules
- News summary integration (non-interpretive)
- Basic portfolio performance tracking

### Out-of-Scope
- Real-time market data integration
- Broker API connectivity
- AI price prediction or indicator generation
- Automated trading execution
- Cryptocurrency analysis
- Weekly/monthly candle analysis

## User Stories
1. **As a trader**, I want to view daily candlestick analysis for US equities so I can assess potential trades
2. **As an investor**, I want to see risk metrics for proposed trades so I can make informed decisions
3. **As an analyst**, I want AI to summarize relevant news articles so I can contextualize market movements
4. **As a developer**, I want clear trade decision rules so I can audit and improve the system
5. **As an operator**, I want to ask follow-up questions to a specific analysis agent or to the synthesized verdict so I can inspect the reasoning behind a ticker assessment

## Acceptance Criteria
### News Analysis
```
Given: A news article about Company X
When: The article is processed by the system
Then: The system should summarize the article's key points without interpretation
```

### Trade Decision
```
Given: A stock with bullish candle pattern and positive news
When: The system analyzes the data
Then: The system should recommend "BUY_CANDIDATE" with risk metrics
```

### No-Trade Scenario
```
Given: Incomplete technical analysis and conflicting news
When: The system evaluates the position
Then: The system should recommend "NO_TRADE" with explanation
```

## Glossary
| Term | Definition |
|------|------------|
| BUY_CANDIDATE | Technical indicators suggest potential bullish opportunity |
| SELL_CANDIDATE | Technical indicators suggest potential bearish opportunity |
| HOLD | Current position shows no clear trade signal |
| NO_TRADE | Insufficient evidence to make a trade recommendation |

## System Requirements
- Runs as a local analysis tool with no internet connection
- Uses only historical data for analysis
- Provides detailed audit logs for all decisions
- Includes visualizations of candlestick patterns
- Exports analysis reports in PDF format
- Labels evidence and freshness explicitly as real-time, delayed, stale, or snapshot wherever market data or supporting evidence is shown
- Supports post-entry monitoring outputs for thesis breakage, stop-loss breaches, volatility changes, and options-specific risk changes