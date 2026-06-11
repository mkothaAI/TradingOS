# Principle Classification Table — complete mapping

Source: generated from files in `trading_os_v1/docs/varsity-extraction/` (extracted Varsity modules). Each row below maps an explicit formula, rule or clearly-stated principle found in the extracted files to a category, an engine owner, and a conservative v1 status.

Columns: principle | source module (file) | category | engine | v1 status | notes

---

E(Rp) = Σ W_i * R_i | [module-09-risk-management-trading-psychology.md](../varsity-extraction/module-09-risk-management-trading-psychology.md) | formula | Risk engine | direct | Explicit expected-return formula and numeric example in module 9

Portfolio variance = Σ_i(W_i^2 σ_i^2) + 2 Σ_{i<j}(W_i W_j ρ_{ij} σ_i σ_j) | [module-09-risk-management-trading-psychology.md](../varsity-extraction/module-09-risk-management-trading-psychology.md) | formula | Risk engine | direct | Explicit variance–covariance formula with explanation

Portfolio standard deviation = sqrt(Portfolio variance) | [module-09-risk-management-trading-psychology.md](../varsity-extraction/module-09-risk-management-trading-psychology.md) | formula | Risk engine | direct | Present in module 9

Covariance = ρ_{ij} × σ_i × σ_j | [module-09-risk-management-trading-psychology.md](../varsity-extraction/module-09-risk-management-trading-psychology.md) | formula | Risk engine | direct | Explicit in correlation / covariance section

Correlation coefficient (ρ) ∈ [-1, +1] interpretation | [module-09-risk-management-trading-psychology.md](../varsity-extraction/module-09-risk-management-trading-psychology.md) | concept | Risk / Universe | later | Concept present; converting to numeric policy left to config

Value at Risk (VaR): empirical percentile method (95% example) | [module-09-risk-management-trading-psychology.md](../varsity-extraction/module-09-risk-management-trading-psychology.md) | deterministic rule | Risk engine | direct (configurable) | Module 9 shows empirical VaR and 95% example; default confidence treated as example

Expected Shortfall (average loss beyond VaR) | [module-09-risk-management-trading-psychology.md](../varsity-extraction/module-09-risk-management-trading-psychology.md) | formula | Risk engine | direct | Described in module 9

Sharpe Ratio = (R_portfolio - R_riskfree) / σ_portfolio | [module-09-risk-management-trading-psychology.md](../varsity-extraction/module-09-risk-management-trading-psychology.md) | formula | Risk engine / Explanation | direct | Present in module 9

Position sizing (example formula): Position_Sizing = Risk_Capital / (Stop_Loss_Distance * Contract_Size) | [module-09-risk-management-trading-psychology.md](../varsity-extraction/module-09-risk-management-trading-psychology.md) | deterministic rule | Risk engine | direct | Explicit example formula in module 9

Position sizing guideline: risk no more than 1-2% of capital per trade (example) | [module-09-risk-management-trading-psychology.md](../varsity-extraction/module-09-risk-management-trading-psychology.md) | rule/example | Risk engine | later | Presented as guidance/example in module 9; treat as illustrative unless confirmed

Kelly percentage: Kelly% = W - [(1-W)/R] | [module-09-risk-management-trading-psychology.md](../varsity-extraction/module-09-risk-management-trading-psychology.md) | formula | Risk engine | later / optional-capped | Present in module 9 but marked LATER / simulation-only per mapping rules

ATR (14-day) computation and use as volatility measure | [module-02-technical-analysis.md](../varsity-extraction/module-02-technical-analysis.md), [module-09-risk-management-trading-psychology.md](../varsity-extraction/module-09-risk-management-trading-psychology.md) | formula / rule | Technical / Risk | direct | ATR example present; use as input to volatility-based sizing

Simple moving average (MA) = mean(close_{t-N+1..t}) — MA-cross signals | [module-02-technical-analysis.md](../varsity-extraction/module-02-technical-analysis.md) | deterministic rule | Technical engine | direct | MA concept and MA-cross approach described; numeric windows are configurable

Candle classification (bullish if close > open, bearish if close < open) — example usages | [module-02-technical-analysis.md](../varsity-extraction/module-02-technical-analysis.md) | concept / visual | Technical engine | later | Visual pattern interpretation marked LATER unless explicitly converted to numeric rules

Contract value (futures) = Lot_size × Futures_price | [module-04-futures-trading.md](../varsity-extraction/module-04-futures-trading.md) | formula | Risk / Universe | direct | Explicit example in futures module

Margin / M2M concepts and margin calculator references | [module-04-futures-trading.md](../varsity-extraction/module-04-futures-trading.md), [module-09-risk-management-trading-psychology.md](../varsity-extraction/module-09-risk-management-trading-psychology.md) | concept / deterministic rule | Risk engine | later | Margin concepts present; implementation depends on market specifics and broker data (out-of-scope for execution)

Diversification: unsystematic risk reduces with >~20 stocks (illustrative) | [module-01-introduction-to-stock-markets.md](../varsity-extraction/module-01-introduction-to-stock-markets.md), [module-09-risk-management-trading-psychology.md](../varsity-extraction/module-09-risk-management-trading-psychology.md) | concept | Universe + Risk policy | later | Present as empirical observation; move to shared Universe+Risk policy

Efficient frontier / Excel Solver optimization steps (solver usage) | [module-08-portfolio-optimization?](../varsity-extraction/) | explanation-only | Explanation / Decision | exclude | Workbook UI and Excel steps are guidance only; underlying math (mean-variance) is noted elsewhere

Value normalization / Equity curve (normalize portfolio to Rs.100 example) | [module-06-equity-curve?](../varsity-extraction/) | concept / example | Explanation / Risk | direct | Equity curve normalization example present in module text (implementation straightforward)

VaR percentile counting method (select least value within top X% observations) | [module-09-risk-management-trading-psychology.md](../varsity-extraction/module-09-risk-management-trading-psychology.md) | deterministic rule | Risk engine | direct | Text describes empirical percentile selection (95% example)

Position sizing models: Total Equity, Reduced Total Equity, Percentage Margin, Percentage Volatility | [module-09-risk-management-trading-psychology.md](../varsity-extraction/module-09-risk-management-trading-psychology.md) | deterministic rules | Risk engine | direct | Explicitly enumerated in module 9; implement as configurable models

Stop-loss enforcement as a discipline and mechanical rule | [module-09-risk-management-trading-psychology.md](../varsity-extraction/module-09-risk-management-trading-psychology.md) | rule | Decision / Risk | direct | Module emphasizes mechanical stop-loss; treat as enforcement policy (configurable)

Rebalancing schedule (reset to target allocations periodically — quarterly/annually) | [module-09-risk-management-trading-psychology.md](../varsity-extraction/module-09-risk-management-trading-psychology.md) | rule | Universe / Decision | direct | Present as explicit recommendation

Pair-trade spread = price_A - k * price_B (pair trading conceptual formula) | [module-10-trading-systems.md](../varsity-extraction/module-10-trading-systems.md) | concept / deterministic rule | Technical / Decision | later | Pair-trade concepts exist; convert to concrete numeric detection rules later

Net cash flow for simple option transactions = sum(credits) - sum(debits) (illustrative) | [module-05-options-theory-for-professional-trading.md](../varsity-extraction/module-05-options-theory-for-professional-trading.md) | formula | Fundamental / Explanation | direct | Present in options module as simple accounting example

Personal-finance simple formulas (e.g., Yearly interest = Principal × Rate) | [module11_personal-finance.md](../varsity-extraction/module11_personal-finance.md) | formula | Explanation | exclude | Educational examples; not directly used by trading engines

Behavioral biases list (anchoring, recency/regency bias, confirmation, bandwagon, loss aversion, illusion of control, hindsight bias) | [module-09-risk-management-trading-psychology.md](../varsity-extraction/module-09-risk-management-trading-psychology.md) | psychology | Explanation engine | exclude | Explanation-only; useful for UX and training, not deterministic

"Limit futures lots per 100k" (illustrative) | [module-09-risk-management-trading-psychology.md](../varsity-extraction/module-09-risk-management-trading-psychology.md) & [module-04-futures-trading.md](../varsity-extraction/module-04-futures-trading.md) | example rule | Risk engine | later | Illustrative threshold; requires normalization to US lot sizes before adoption

---

Notes
- This table is intentionally conservative: it lists explicit formulas and clear deterministic rules found in the extracted modules. Where Varsity provides illustrative thresholds, UI/UX advice, or Excel steps, those entries are marked LATER or EXCLUDE and recorded as notes rather than being promoted to immediate production defaults.
- Conflicts between different extracted files (different illustrative examples/thresholds) are recorded in the notes column and left for human resolution.

Planned product vocabulary addendum
- Follow-up question, synthesized verdict, options profile, monitoring condition, and explicit freshness labels are approved repo vocabulary for later prompt-pack and contract work.
- These terms are product-shape terms rather than extracted Varsity rules; they remain advisory and planning-only until a later schema/contract phase.

Next step (upon approval): convert this markdown into a machine-readable CSV or JSON used by engine scaffolding to seed tests and implementations.
