# Zerodha Varsity Extraction Index

## Purpose
This directory contains principle and rule extractions from the Zerodha Varsity educational modules. Each module is analyzed for:
- Key concepts and principles
- Explicit rules and measurable logic
- Psychological and risk guidance
- Implementation candidates for trading-os-v1
- Educational-only concepts (not to be automated)

## Extraction Status

### ✅ Completed Extractions

#### Core Trading Foundation
- **[Module 1: Introduction to Stock Markets](module-01-introduction-to-stock-markets.md)**
  - Foundational concepts: risk-return relationship, capital preservation, inflation adjustment
  - v1 Implementation: Real-return validators, capital preservation gates
  - Status: Complete

- **[Module 2: Technical Analysis](module-02-technical-analysis.md)**
  - Candlestick patterns, volume confirmation, support/resistance identification
  - v1 Implementation: Pattern detector, trend classifier, volatility adjuster
  - Status: Complete

- **[Module 3: Fundamental Analysis](module-03-fundamental-analysis.md)**
  - Business quality metrics: ROE, margins, FCF, debt levels
  - v1 Implementation: Fundamental health validator, trend analyzer, quality gates
  - Status: Complete

#### Risk & System Design
- **[Module 4: Futures Trading](module-04-futures-trading.md)**
  - Position sizing, margin management, hedging mechanics, leverage limits
  - v1 Implementation: Position sizer, margin monitor, expiration tracker
  - Status: Complete

- **[Module 9: Risk Management & Trading Psychology](module-09-risk-management-trading-psychology.md)**
  - Portfolio variance, correlation analysis, position sizing, psychological discipline
  - v1 Implementation: Portfolio risk calculator, correlation monitor, position sizer, volatility adjuster
  - Status: Complete

- **[Module 10: Trading Systems](module-10-trading-systems.md)**
  - Pair trading, mean reversion, spread analysis, deterministic rules
  - v1 Implementation: Pair validator, spread calculator, signal generator, regime detector
  - Status: Complete

#### Operational & Taxation
- **[Module 7: Markets and Taxation](module-07-markets-and-taxation.md)**
  - Tax classification, capital gains treatment, loss optimization, documentation
  - v1 Implementation: Tax classifier, liability calculator, cost basis tracker, wash-sale detector
  - Status: Complete

### 📋 Planned (Not Yet Extracted)

- **Module 5: Options Theory for Professional Trading**
  - Expected: Option pricing, Greeks, volatility surfaces, extrinsic vs. intrinsic value
  - v1 Note: Options are out of scope for v1 (complexity); educational reference only

- **Module 6: Option Strategies**
  - Expected: Spreads, straddles, strangles, risk management in options
  - v1 Note: Options are out of scope for v1; educational reference only

- **Module 8: Currency & Commodity Futures**
  - Expected: Product-specific hedging, basis trading, market structure
  - v1 Note: Likely out of scope for v1 (focus on equities); reference for futures principles

- **Module 11: Personal Finance Part 1**
  - Expected: Wealth creation, goal-based planning, insurance vs. investment
  - v1 Note: Educational only; personal finance planning is out of scope for trading system

- **Module 13: Financial Modelling**
  - Expected: DCF, valuation models, scenario analysis, sensitivity analysis
  - v1 Note: Educational reference; forward-looking modeling out of scope for v1

- **Module 14: Personal Finance - Insurance**
  - Expected: Insurance products, risk mitigation, policy selection
  - v1 Note: Educational only; insurance is outside trading system scope

- **Module 12: Innerworth - Mind over Markets**
  - Status: No content files (empty directory)

---

## Cross-Module Dependency Map

### Foundation → Implementation Pipeline
```
Module 1 (Risk-Return)
    ↓
Module 2 (Signal Generation) + Module 3 (Quality Gate)
    ↓
Module 10 (System Design) + Module 9 (Risk Management)
    ↓
Module 4 (Execution Mechanics)
    ↓
Module 7 (Tax Optimization)
```

---

## trading-os-v1 Implementation Roadmap

### Phase 1: Core Decision Engine (Modules 1, 2, 3)
- **Real-return validators**: Enforce positive real returns (Module 1)
- **Signal generation**: Candlestick + trend + volume (Module 2)
- **Fundamental quality gates**: ROE, margin, FCF checks (Module 3)
- **Output**: BUY_CANDIDATE, SELL_CANDIDATE, HOLD, NO_TRADE decisions

### Phase 2: Risk Management (Module 9 + Module 4)
- **Portfolio risk calculator**: Variance, correlation, Sharpe ratio (Module 9)
- **Position sizer**: Enforce 1-2% risk per trade (Module 9)
- **Margin monitor**: Track utilization for futures (Module 4)
- **Volatility adjuster**: Scale position size dynamically (Module 9)
- **Output**: Risk Snapshot included in decision result

### Phase 3: Trading Systems (Module 10)
- **Pair trading validator**: Correlation check + spread analysis
- **Mean reversion signal**: Z-score thresholds for entry/exit
- **Regime detector**: Flag when system assumptions break
- **Output**: System-generated trades with entry/exit rules

### Phase 4: Execution & Governance (Module 4 + Module 7)
- **Futures mechanics**: Position size, margin, expiration management (Module 4)
- **Tax planning**: Cost basis tracking, holding period, tax reserve (Module 7)
- **Documentation**: Audit trail for compliance
- **Output**: Fully documented trade with tax implications

---

## v1-Safe Rules Summary

### Capital Preservation (Module 1)
1. ✅ Do not execute trades if capital < emergency reserve
2. ✅ Calculate and display real returns (nominal - inflation)
3. ✅ Enforce positive real return threshold

### Signal Generation (Module 2)
1. ✅ Classify candles as bullish/bearish
2. ✅ Require volume confirmation (> 1.5x average)
3. ✅ Identify support/resistance from recent extrema
4. ✅ Classify trend state (uptrend, downtrend, consolidation)

### Fundamental Quality (Module 3)
1. ✅ Only trade securities with ROE > 12% & net margin > 5%
2. ✅ Verify growth through FCF (>70% correlation with reported earnings)
3. ✅ Alert if net margin declines >200bps vs. 5-year average
4. ✅ Flag if debt/EBITDA > 3.0 or increasing

### Risk Management (Module 9)
1. ✅ No trade exceeds 2% of portfolio capital at risk
2. ✅ Reduce position size if volatility > 1.5x average
3. ✅ Alert if correlation among holdings > 0.7 average
4. ✅ Halt trading if monthly losses > 2% of portfolio
5. ✅ Enforce stop-losses mechanically (no override without documentation)

### Pair Trading (Module 10)
1. ✅ Require correlation ρ > 0.7 over 252 days
2. ✅ Enter when Z-score > 2.0; exit when Z-score < 0.5
3. ✅ Close if correlation drops below 0.5
4. ✅ No subjective override of system rules

### Futures Mechanics (Module 4)
1. ✅ Maximum 2:1 leverage (strictly enforced)
2. ✅ Margin utilization stays < 50%; 60% triggers reduction
3. ✅ Close/roll all futures 5 days before expiration
4. ✅ Trade only contracts with 1M+ average daily volume

### Taxation (Module 7)
1. ✅ Allocate 25-30% of profits to tax reserve
2. ✅ Track cost basis for all positions
3. ✅ Monitor holding periods (flag when >1 year)
4. ✅ Maintain documentation for 6+ years

---

## Out-of-Scope for v1 (By Module)

| Category | Out-of-Scope | Reason |
|----------|--------------|--------|
| **Module 1** | Behavioral coaching, life-stage planning | Editorial/personal; not algorithmic |
| **Module 2** | Exotic patterns, visual intuition | Too subjective; requires domain judgment |
| **Module 3** | Forward earnings forecasting, M&A analysis | Predictive; out of scope for v1 |
| **Module 4** | Volatility forecasting, complex spreads | ML/statistical infrastructure needed |
| **Module 5, 6** | Options pricing, Greeks, spreads | High complexity; deferred to v2 |
| **Module 7** | Tax law interpretation, litigation, international structures | Legal; jurisdiction-specific |
| **Module 9** | Psychological profiling, behavioral coaching | Personal services; not algorithmic |
| **Module 10** | Cointegration-based pair finding, machine learning | Statistical infrastructure; not in v1 |
| **Module 11, 13, 14** | Personal finance planning, insurance, financial modeling | Outside trading system scope |

---

## Key Principles Integrated into trading-os-v1

### 1. Capital Preservation First
- Real returns must exceed inflation (Module 1)
- Position sizing capped at 1-2% risk per trade (Module 9)
- Monthly drawdown ceiling at 2% (Module 9)

### 2. Evidence-Based Decisions
- Signal requires volume confirmation (Module 2)
- Fundamental quality gate (ROE, margin, FCF) (Module 3)
- Pair trading requires correlation >0.7 (Module 10)

### 3. Deterministic Rules
- No subjective override without documentation (Module 10)
- Mechanical stop-losses (Module 9)
- Automated position sizing and leverage limits (Module 4)

### 4. Risk-Return Alignment
- Higher risk requires higher return (Module 1)
- Volatility-adjusted position sizing (Module 9)
- Leverage capped at 2:1 (Module 4)

### 5. Continuous Monitoring
- Correlation tracking (Module 9)
- Margin utilization (Module 4)
- Holding period tracking (Module 7)
- Regime detection (Module 10)

---

## File Organization

```
docs/varsity-extraction/
├── README.md (this file)
├── module-01-introduction-to-stock-markets.md
├── module-02-technical-analysis.md
├── module-03-fundamental-analysis.md
├── module-04-futures-trading.md
├── module-07-markets-and-taxation.md
├── module-09-risk-management-trading-psychology.md
├── module-10-trading-systems.md
└── [Planned: modules 5, 6, 8, 11, 13, 14]
```

---

## How to Use This Extraction

### For Implementation Teams
- **Phase 1**: Read Module 1, 2, 3 extractions; implement signal generation pipeline
- **Phase 2**: Read Module 9, 4 extractions; implement risk management and position sizing
- **Phase 3**: Read Module 10 extraction; implement pair trading or mean reversion systems
- **Phase 4**: Read Module 7 extraction; implement tax tracking and compliance

### For Risk Review
- Consult **Module 9 (Risk Management)** for risk framework
- Consult **Module 4 (Futures)** for leverage and margin rules
- Consult **Module 1 (Capital Preservation)** for real-return validation

### For Trading Rules
- Consult **v1-Safe Rules** section in each module for specific, measurable rules
- Each rule is mapped to source module and marked as v1-Safe or v1-Candidate
- Candidate rules may require additional infrastructure before implementation

---

## Notes on Extraction

- **Principles**: Extracted from Zerodha Varsity PDFs without reproducing large sections
- **Rules**: Stated explicitly or inferred from context; no hallucination
- **Formulas**: Transcribed faithfully; include references to source modules
- **Status**: All extractions are point-in-time summaries; updates may occur if PDFs are revised
- **Scope**: Focused on trading system mechanics; educational-only content excluded

---

## Next Steps

1. ✅ Extractions 1-4, 7, 9-10 complete
2. ⏳ Extract Modules 5, 6, 8 (options and commodities; likely lower priority)
3. ⏳ Extract Modules 11, 13, 14 (personal finance; educational reference only)
4. 🔨 Implementation: Use Phase 1-4 roadmap to build trading-os-v1 modules
5. 🔄 Validation: Test each rule against historical data before going live
