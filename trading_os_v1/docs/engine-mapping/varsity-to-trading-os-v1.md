Purpose
-------
This document converts the principles and explicit rules extracted from the Zerodha Varsity PDFs (all source markdowns located under `trading_os_v1/docs/varsity-extraction/`) into deterministic, auditable requirements for `trading_os_v1`.

It is strictly derived from files inside `trading_os_v1/docs/varsity-extraction/` and does not introduce any external material. Where the extracted files conflict or provide only illustrative examples, the conflict is noted and not resolved by assumption.

V1 scope
--------
- Market: US markets only (implementation constraint for V1).
- Strategy class: swing-trading candidates only.
- Data timing: end-of-day analytics plus pre-market / overnight signals only.
- Integrations: no broker integration; no order execution.
- Decision style: deterministic decisions only.
- AI role: explanation, summarization and future-event extraction support only. AI may generate human-readable explanations and surface candidate events for review; it must not make final deterministic decisions.

Engine mapping
--------------
Notes: Each engine mapping below lists: (1) relevant Varsity modules (files under `docs/varsity-extraction/`), (2) extracted principles (faithful to the extracted text), (3) direct v1 rules candidates (deterministic and implementable in v1), (4) optional later ideas, (5) not suitable for automation items.

Universe engine
- Relevant extracted files: `module-01-introduction-to-stock-markets.md`, `module-03-fundamental-analysis.md`, `module-07-markets-and-taxation.md`.
- Extracted principles:
  - Basic universe selection guidance: diversify to reduce unsystematic risk; prefer a broad set of tickers rather than concentration (text references ~20 stocks diversification effect).
- Direct v1 rules candidates:
  - Maintain a tradable universe list with metadata (market, sector, ticker). Implement a configurable sector-exposure cap (e.g., no more than X% per sector) as the translation of "diversify" guidance.
- Optional later ideas:
  - Fundamental screening rules derived from `module-03` (e.g., revenue growth, margin floor) after mapping to US equivalents.
- Not suitable for automation:
  - Subjective stock selection rationale and narrative analyst judgement.

Fundamental engine
- Relevant files: `module-03-fundamental-analysis.md`, `module-13.md` (Financial Modelling).
- Extracted principles:
  - Fundamental analysis is holistic: earnings, margins, and growth matter.
- Direct v1 rules candidates:
  - Compute simple financial ratios (growth, margins) and implement pass/fail thresholds as configurable checks.
- Optional later ideas:
  - Financial-model-derived signals from `module-13` used as human-reviewed inputs.
- Not suitable for automation:
  - Qualitative narrative judgements.

Technical engine
- Relevant files: `module-02-technical-analysis.md`, `module-06-option-strategies.md`, `module-10-trading-systems.md`.
- Extracted principles:
  - Candle direction classification; moving averages; ATR as volatility measure; MA-cross style signals; pair-trade/spread ideas in trading systems.
- Direct v1 rules candidates:
  - EOD computations: daily returns, 14-day ATR, simple moving averages, MA-cross signals, basic momentum thresholds. Emit structured signals for Decision engine.
- Optional later ideas:
  - Pair-trade detection and automated spread monitoring.
- Not suitable for automation:
  - Visual chart interpretation requiring subjective human review.

Event engine
- Relevant files: `module-01-introduction-to-stock-markets.md`, `module-07-markets-and-taxation.md`, `module-05-options-theory-for-professional-trading.md`.
- Extracted principles:
  - Corporate events (earnings announcements) and regulatory/taxation events can affect positions and should be flagged.
- Direct v1 rules candidates:
  - Ingest scheduled events (earnings) and tag affected tickers for pre-market gating and decision impact analysis (flag-only; no automatic action).
- Optional later ideas:
  - AI-assisted event severity scoring (human-verified).
- Not suitable for automation:
  - Inferring event veracity from untrusted sources; AI must not invent facts.

Risk engine
- Relevant files: `module-09-risk-management-trading-psychology.md`, `module-04-futures-trading.md`, `module11_personal-finance.md`.
- Extracted principles (faithful excerpts):
  - Expected return arithmetic (E(Rp) = Σ w_i * E(R_i)); daily return variance calculation; covariance steps; variance–covariance matrix (XT X); correlation matrix; portfolio variance; portfolio annualization; equity curve normalization; Value at Risk (VaR) via empirical percentile (95% example); position sizing methods (total equity, reduced total equity, percentage margin, percentage volatility using ATR); Kelly's criterion formula (Kelly% = W - [(1-W)/R]); stop-loss, margin and M2M considerations for futures.
- Direct v1 rules candidates:
  - Implement numeric functions: daily returns; variance; covariance; variance–covariance matrix; correlation matrix; portfolio variance; annualization; empirical VaR (configurable confidence, default 95% as present in source); ATR-based percentage-volatility sizing; percentage-margin and total/reduced-equity sizing models; Kelly% computation as in extracted formula.
  - Provide simulation checks that reject candidate trades violating configured exposure or margin caps (simulation/advisory only).
- Optional later ideas:
  - Provide optimization suggestions (solver-based efficient frontier) as human-reviewed outputs.
- Not suitable for automation:
  - Automatically changing sizing models without human confirmation; psychological coaching.

Decision engine
- Relevant files: `module-10-trading-systems.md`, `module-02-technical-analysis.md`, `module-09-risk-management-trading-psychology.md`.
- Extracted principles:
  - Decisions require technical signal + fundamental pass + risk-adjusted sizing; system should be conservative and output NO-TRADE when constraints fail.
- Direct v1 rules candidates:
  - Deterministic pipeline: require (technical signal == true) AND (fundamental pass == true) AND (risk sizing constraints satisfied) → candidate trade. Decision outputs: BUY_CANDIDATE / SELL_EXIT_CANDIDATE / HOLD / NO_TRADE and `size_info` from Risk engine.
- Optional later ideas:
  - Weighted scoring and multi-objective ranking of candidate trades.
- Not suitable for automation:
  - Replacing human judgment for ambiguous or borderline signals.

Future product-surface addendum
- The approved product shape also includes a follow-up layer where users can question a named advisory agent or the synthesized verdict about a ticker analysis.
- It includes an options-analysis surface that will surface strike, expiry, implied volatility, greeks, liquidity, and spread quality as structured advisory context.
- It includes a monitoring/watchtower surface for post-entry thesis breakage, stop-loss breaches, volatility changes, macro shocks, and options-specific risk changes.
- These surfaces are planned product vocabulary only; they do not change the deterministic decision authority described above.

Explanation engine
- Relevant files: `module-09-risk-management-trading-psychology.md`, `module-02-technical-analysis.md`, supporting modules.
- Extracted principles:
  - Explanations should be sourced and cite the specific module when describing formulas (expected return, variance, VaR, Kelly, position sizing) and list behavioral biases.
- Direct v1 rules candidates:
  - Produce deterministic, source-cited explanations for each decision (list applied rules and their source module file from `docs/varsity-extraction/`). AI may be used only to rephrase and summarize; all claims must include citations.
- Optional later ideas:
  - AI-assisted generation of training material from extracted text (human-reviewed).
- Not suitable for automation:
  - Using AI-produced explanations as covert rules for decision making without human approval.

Approved vocabulary note
- Use the canonical terms `symbolic verdict`, `advisory agent`, `synthesized verdict`, `follow-up question`, `options profile`, `monitoring condition`, and explicit freshness labels (`real_time`, `delayed`, `stale`, `snapshot`) in later prompt-pack and contract work.

Principle classification table (representative entries)
-------------------------------------------------
principle | source module | category | engine | v1 status | notes
---------:|:--------------:|:--------:|:------:|:---------:|:-----
E(Rp) = Σ w_i * E(R_i) | module-09-risk-management-trading-psychology.md | formula | Risk engine | direct | numeric example present in extracted file
Compute daily returns & variance | module-09-risk-management-trading-psychology.md | deterministic rule | Risk engine | direct | step-by-step example
Variance–covariance matrix (XT X) | module-09-risk-management-trading-psychology.md | formula | Risk engine | direct | Excel array instructions included
Correlation = covariance / (σ_x*σ_y) | module-09-risk-management-trading-psychology.md | formula | Risk engine | direct | present in extracted text
VaR (empirical, 95% example) | module-09-risk-management-trading-psychology.md | deterministic rule | Risk engine | direct | default 95% example; configurable
Kelly% = W - [(1-W)/R] | module-09-risk-management-trading-psychology.md | formula | Risk engine | direct | worked example included
ATR-based volatility sizing | module-09-risk-management-trading-psychology.md & module-02-technical-analysis.md | deterministic rule | Technical / Risk | direct | ATR example present
Diversify; unsystematic risk flattens after ~20 stocks | module-01-introduction-to-stock-markets.md & module-09-risk-management-trading-psychology.md | concept | Universe engine | later | convert to numeric cap as configuration
Excel Solver optimization steps | module-08/module-09 extracts | explanation-only | Explanation / Decision | exclude | workbook not supplied; UI steps are guidance only
Behavioral biases list | module-09-risk-management-trading-psychology.md | psychology | Explanation engine | exclude | explanation-only, not deterministic

(The above table is representative. All explicit formulas and deterministic rules discovered in `docs/varsity-extraction/` are catalogued in the full internal mapping source. Conflicts between extracted files are recorded in the 'notes' column rather than being resolved by assumption.)

Hard boundaries for trading_os_v1
--------------------------------
- AI cannot invent market facts or numeric values not present in local data or the extracted files. All assertions in outputs must be traceable to either a local data source or a cited extracted module file.
- AI cannot override deterministic rules produced by Risk/Decision engines. Any override requires explicit human confirmation and a logged rationale.
- "NO-TRADE" is a valid and expected output from the Decision engine.
- Broker integration and execution are out of scope for V1; system outputs are advisory/simulative only.
- Psychological coaching or personalized trader therapy is out of scope; Explanation engine may describe biases but not implement remediation.

Recommended first implementation order
------------------------------------
1. Risk engine — implement core numeric building blocks (daily returns, variance, covariance, variance–covariance matrix, correlation, portfolio variance, annualization, empirical VaR, ATR, position sizing models, Kelly%) and unit tests.
2. Technical engine — implement EOD signals (MA, ATR, candle classification, volatility bands) used by Decision engine.
3. Decision engine — deterministic pipeline consuming Technical + Fundamental (simple pass/fail) + Risk sizing; outputs BUY_CANDIDATE / SELL_EXIT_CANDIDATE / HOLD / NO_TRADE and `size_info`.
4. Explanation engine — deterministic, source-cited explanations and templated summaries for decisions.
5. Universe engine — basic universe filters and diversification constraints (configurable).
6. Fundamental engine — add simple ratio checks and pass/fail rules.
7. Event engine — scheduled-event ingestion and tagging (earnings). Keep event-driven gating as advisory only.

Notes & next steps
------------------
- This file was produced using only the extracted module files in `trading_os_v1/docs/varsity-extraction/` and the QA summary produced by the QA script. No external websites or non-local sources were consulted.
- Conflicts and illustrative examples in extracted files are noted rather than resolved; if you want specific illustrative thresholds adopted (e.g., per-trade caps), supply the canonical numbers or indicate preference to convert illustrative examples into defaults.

Approval: this draft is saved now at `trading_os_v1/docs/engine-mapping/varsity-to-trading-os-v1.md`.
