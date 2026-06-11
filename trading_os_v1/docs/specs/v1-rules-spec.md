# trading_os_v1 — V1 Rules Specification (derived from Varsity extracts)

This specification is derived only from files in `trading_os_v1/docs/engine-mapping/varsity-to-trading-os-v1.md` and the extracted Varsity module markdowns under `trading_os_v1/docs/varsity-extraction/`.

## 1. Mission
- Capital preservation first: prefer `NO_TRADE` over risky entries when deterministic checks indicate unacceptable risk. (Source: module-09)
- `NO_TRADE` is a valid, auditable system outcome.
- Deterministic-first: all production decision logic must be deterministic and unit-testable. AI is permitted only for explanation rephrasing and optional event extraction support.
- Symbolic/verdict authority is final: advisory agents may explain, question, or summarize, but they do not override deterministic validation.

## 1.1 Canonical vocabulary
- Symbolic verdict: the backend-authored final decision token for a ticker or analysis state.
- Advisory agent: a non-authoritative analysis participant that can answer follow-up questions.
- Synthesized verdict: the backend-owned summary of the deterministic outcome and supporting rules.
- Follow-up question: a user question directed to a specific agent or to the synthesized verdict.
- Invalidation: a condition that breaks the trade thesis and blocks or exits the candidate.
- Monitoring condition: a post-entry state that should be watched for thesis breakage, stop-loss breach, volatility change, macro shock, or options-specific risk change.
- Options profile: structured option-analysis vocabulary including strike, expiry, implied volatility, delta, gamma, theta, vega, rho, liquidity, and spread quality.
- Evidence freshness labels: `real_time`, `delayed`, `stale`, and `snapshot`.

## 2. System scope
- Markets: US markets only (V1 constraint).
- Strategy class: swing candidates only (multi-day holdings).
- Timing: End-of-day (EOD) analytics and pre-market overnight analysis only.
- Integrations: No broker integration or execution in V1; outputs are advisory.
- Interactive multi-agent follow-up is a planned product surface, but it remains advisory and cannot change the final symbolic verdict.
- Options analysis is a first-class planned surface, but it remains descriptive until its own contracts are approved.
- Post-entry monitoring and alerting are part of the product plan, but they remain backend-owned and deterministic.
- Decision outputs: `BUY_CANDIDATE`, `SELL_EXIT_CANDIDATE`, `HOLD`, `NO_TRADE`.

## 3. Data contracts
All timestamps are ISO 8601. Price series are EOD with date association.

- Universe engine inputs
  - `universe_config` (object, required): {allowed_markets: ["US"], sector_caps: {sector:str -> percent:float}, max_universe_size: int}
  - `ticker_metadata` (list): [{ticker, exchange, sector, market_cap, lot_size, tradable}]
  - `as_of_date` (date)

- Fundamental engine inputs
  - `fundamental_data` (map ticker->fundamentals): {revenue, net_income, eps, roe, margins, fiscal_period}
  - `fundamental_config` (object): optional thresholds (config-driven)

- Technical engine inputs
  - `price_series` (map ticker->list[{date,close,open,high,low,volume}]) — min lookback 60 EOD rows
  - `technical_config` (object): {atr_window:int (default 14), ma_windows:[int], momentum_windows:[int]}

- Event engine inputs
  - `scheduled_events` (list): [{ticker, event_type, event_date, source}]
  - `event_config` (object): {earnings_blackout_days_before:int, earnings_blackout_days_after:int, advisory_only:bool}

- Risk engine inputs
  - `portfolio_state` (object): {total_equity, cash, positions:[{ticker, qty, entry_price, side}]}
  - `risk_config` (object): {per_trade_risk_pct, max_position_size_pct, max_leverage, var_confidence (default 0.95), sizing_model}
  - `price_series` as above

- Decision engine inputs
  - `technical_signals`, `fundamental_pass`, `risk_assessment`, `event_flags`, `policy_config`

- Explanation engine inputs
  - `applied_rules`, `data_snapshot`

Planned structured output vocabulary for later contract work:
- Entry planning: `entry_bias`, `timing_window`, `capital_allocation`, `size_plan`
- Risk planning: `stop_loss`, `waiting_time`, `hold_time`, `invalidation_level`
- Monitoring planning: `monitoring_conditions`, `alert_triggers`, `watch_status`
- Options planning: `strike`, `expiry`, `implied_volatility`, `greeks`, `liquidity`, `spread_quality`

All engines must include source citations linking to `trading_os_v1/docs/varsity-extraction/` files for each rule applied.

## 4. Engine requirements

### Universe engine
- Purpose: maintain and filter tradable universe; apply diversification caps.
- Inputs: `universe_config`, `ticker_metadata`, `as_of_date`.
- Outputs: `universe_list`, `universe_stats`.
- Deterministic logic:
  - Filter `tradable==true` and `exchange` ∈ allowed markets.
  - If `max_universe_size` set, truncate by descending `market_cap`.
  - Apply `sector_caps` by removing lowest-market-cap tickers in a sector until cap compliance.
- Failure handling: empty universe → `universe_list=[]`, emit `UNIVERSE_EMPTY`; Decision engine treats as `NO_TRADE`.
- Test cases: assert truncation and sector cap compliance for contrived metadata.

### Fundamental engine
- Purpose: apply configurable pass/fail fundamental checks.
- Inputs: `fundamental_data`, `fundamental_config`.
- Outputs: `fundamental_pass`, `fundamental_reasons`.
- Deterministic logic: evaluate each configured threshold; pass only if all pass. Missing data → fail.
- Failure handling: `MISSING_DATA` reason; `fundamental_pass=false`.
- Test cases: verify pass/fail for sample data and thresholds.

### Technical engine
- Purpose: compute EOD indicators and structured signals.
- Inputs: `price_series`, `technical_config`.
- Outputs per ticker: `indicators` (atr, ma, returns, volatility), `signals` (ma_cross, atr_spike, momentum_pass, candle_classification).
- Deterministic logic:
  - ATR(14) per standard TR method (see module-02).
  - Simple moving averages as configured.
  - MA-cross: +1 when short MA crosses above long MA on current EOD; -1 when opposite; else 0.
  - Candle classification: `bullish` if close>open, `bearish` if close<open, `neutral` otherwise.
- Failure handling: insufficient history → `INSUFFICIENT_HISTORY`, neutral signals.
- Test cases: validate ATR, MA, and MA-cross on synthetic series.

### Event engine
- Purpose: flag scheduled corporate events (earnings) and advisory gating flags.
- Inputs: `scheduled_events`, `event_config`.
- Outputs: `event_flags` per ticker: {earnings_upcoming, blackout, event_list}.
- Deterministic logic: if event date within configured blackout window, set `blackout=true` per config.
- Failure handling: missing events → empty flags; if policy requires events and data missing, proceed advisory-only.
- Test cases: scheduled event within blackout window triggers `blackout`.

### Risk engine
- Purpose: deterministic risk calculations and permissible trade sizes.
- Inputs: `portfolio_state`, `price_series`, `risk_config`.
- Outputs per ticker: `size_info` (allowed_qty, notional, risk_amount, sizing_model_used), `risk_metrics` (var, portfolio_variance, volatility).
- Deterministic logic (implement formulas from module-09):
  - Daily returns: r_t = (close_t / close_{t-1}) - 1.
  - Sample variance and covariance per module-09 formulas.
  - Portfolio variance: Σ_i(W_i^2 σ_i^2) + 2Σ_{i<j} W_i W_j ρ_{ij} σ_i σ_j.
  - Annualize volatility by sqrt(252) (configurable).
  - Empirical VaR by percentile; default confidence 0.95 is example-derived but configurable.
  - Sizing models: `total_equity`, `reduced_total_equity`, `percentage_margin`, `percentage_volatility` (ATR-based) as enumerated in module-09.
  - Kelly% per extracted formula; mark as LATER/optional.
- Failure handling: missing input → `RISK_ERROR`, `allowed_qty=0`; if margin/leverage caps exceeded → `allowed_qty=0` with reason.
- Test cases: compute allowed_qty for contrived price series and portfolio.

### Decision engine
- Purpose: deterministic advisory: `BUY_CANDIDATE` / `SELL_EXIT_CANDIDATE` / `HOLD` / `NO_TRADE`.
- Inputs: `technical_signals`, `fundamental_pass`, `risk_assessment`, `event_flags`, `policy_config`.
- Outputs: `decision`, `size_info`, `applied_rules`.
- Deterministic logic: see Decision matrix (section 6). Missing inputs or engine errors → `NO_TRADE`.
- Failure handling: any engine error or disallowed risk → `NO_TRADE` with reason codes.
- Test cases: composition tests for entry and exit scenarios.

### Explanation engine
- Purpose: deterministic, source-cited explanations for decisions.
- Inputs: `applied_rules`, `data_snapshot`.
- Outputs: `explanation_text`, `citations` (links to extracted module files).
- Deterministic logic: include rule id, short statement, and citation for each applied rule; AI may only rephrase.
- Failure handling: missing citation → statement `source not found` included.
- Test cases: ensure all applied rules have citations in explanation.

### Follow-up layer
- Purpose: allow the user to ask a follow-up question about a ticker analysis, either to a named advisory agent or to the synthesized verdict.
- Inputs: `follow_up_question`, `agent_target`, `verdict_ref`, `evidence_context`, `freshness_labels`.
- Outputs: a traced answer that references the existing verdict and evidence; it must not introduce new policy or replace the symbolic verdict.
- Deterministic logic: all answers must remain advisory, cite the same approved evidence vocabulary, and preserve explicit freshness labels.
- Failure handling: if the follow-up cannot be grounded in the approved evidence or verdict context, return a refusal or a `needs_review` style advisory answer rather than inventing policy.
- Test cases: ask the same question of different agents and verify the verdict remains unchanged.

## 5. Rule catalog
Rules are enumerated in `docs/engine-mapping/principle-classification-table.md` and exported CSV/JSON by `scripts/generate_principle_csv.py`.

Representative entries (rule id | statement | source | source type | engine | v1 status | test idea):
- R0001 | E(Rp) = Σ W_i * E(R_i) | module-09 | formula | Risk | direct | compute E(Rp) for sample weights
- R0002 | Portfolio variance formula | module-09 | formula | Risk | direct | verify with sample covariance matrix
- R0003 | VaR empirical percentile (95%) | module-09 | example-derived | Risk | direct/configurable | compute percentile VaR on sample returns
- R0004 | ATR(14) computation | module-02 | formula | Technical | direct | validate ATR on synthetic TR data
- R0005 | MA-cross entry rule | module-02 | interpretation | Technical | direct | create series with MA cross and assert signal

Full rule table and machine-readable exports are available under `docs/engine-mapping/`.

## 6. Decision matrix (exact combinations)
Inputs per ticker (booleans/values):
- `TECH_ENTRY` ∈ {+1,0,-1}
- `FUND_PASS` ∈ {true,false} (treated as true if fundamental checks are not configured)
- `RISK_OK` ∈ {true,false} (true if `allowed_qty>0` and within caps)
- `EVENT_BLOCK` ∈ {true,false}

Evaluation order and exact outcomes:
1) Entry evaluation:
  - If TECH_ENTRY == +1 AND FUND_PASS == true AND RISK_OK == true AND EVENT_BLOCK == false → `BUY_CANDIDATE` with `size_info` from Risk engine.
  - Else if TECH_ENTRY == +1 AND (FUND_PASS == false OR RISK_OK == false OR EVENT_BLOCK == true) → `NO_TRADE` (include reason codes: FUND_FAIL/RISK_FAIL/EVENT_BLOCK).
2) Exit evaluation (existing positions):
  - If TECH_ENTRY == -1 OR stop-loss condition met (market price ≤ computed stop) → `SELL_EXIT_CANDIDATE`.
  - Else → `HOLD`.
3) Edge cases:
  - Any engine error (INSUFFICIENT_HISTORY, RISK_ERROR, etc.) → `NO_TRADE`.

`NO_TRADE` must be auditable with applied_rules and reason codes.

## 7. Risk policy
- V1 position sizing models: `total_equity`, `reduced_total_equity`, `percentage_margin`, `percentage_volatility` (ATR-based).
- Optional/later: Kelly% (experimental only) and solver-based optimizers.
- Must-default-to-`NO_TRADE` conditions:
  - computed margin requirement or leverage exceeds `risk_config.max_leverage` or `max_position_size_pct`;
  - empirical VaR beyond configured acceptable tail risk.
- Example-derived items (not defaults): per-trade 1–2% risk, ATR multipliers, blackout durations. These require explicit human confirmation to become defaults.

## 8. Event policy
- Earnings gating: Event engine marks earnings; decision engine blocks entries within configured blackout windows when `event_config.advisory_only==false`.
- Blackout numeric defaults in Varsity are example-derived; require explicit config to adopt.
- Event outputs are advisory unless policy configured otherwise.
- Post-entry event monitoring remains part of the future monitoring surface and must surface alert conditions without overriding deterministic verdicts.

## 9. Explanation policy
- Explanations must be source-linked: include rule ids and file citations from `docs/varsity-extraction/`.
- Explanations must not introduce new facts or thresholds.
- AI may rephrase explanation text but must not add rules or numeric defaults.
- Explanations and follow-up answers must explicitly label evidence freshness as real-time, delayed, stale, or snapshot when relevant.

## 10. Acceptance criteria (Gherkin-style)
- Universe engine — Scenario: Filter to allowed markets and max size
  Given `ticker_metadata` with 100 US tickers and `universe_config.max_universe_size=50`
  When Universe engine runs
  Then `universe_list` length is 50 and sector caps are respected

- Technical engine — Scenario: ATR and MA-cross
  Given a synthetic price series with known TRs
  When Technical engine computes ATR(14) and MAs
  Then ATR equals hand-calculated ATR and MA-cross detection matches expected

- Risk engine — Scenario: per-trade sizing
  Given `total_equity=100000`, `per_trade_risk_pct=0.01`, stop_distance=2.0
  When Risk engine computes allowed_qty
  Then `risk.size_info.risk_amount == 1000` and `allowed_qty == floor(1000/2.0)`

- Decision engine — Scenario: Deterministic BUY
  Given technical entry signal, `fundamental_pass==true`, `risk_assessment.allowed_qty>0`, and no event blackout
  When Decision engine runs
  Then output `BUY_CANDIDATE` with `size_info` from Risk engine

## 11. Open questions
- Confirm default `per_trade_risk_pct` (Varsity examples 1–2%) — adopt one as default or require explicit config?
- Confirm `event_config` blackout windows default values.
- Confirm Kelly usage: include as experimental or omit from v1?
- Confirm sector cap policy and default percentages.
- Confirm which fundamental thresholds (if any) should be applied by default in v1.

---
Notes: Numeric examples quoted from Varsity extracts are marked example-derived and must be treated as configuration defaults only after explicit human approval. This spec is intentionally conservative and local-only; all rules map back to extracted module files.
