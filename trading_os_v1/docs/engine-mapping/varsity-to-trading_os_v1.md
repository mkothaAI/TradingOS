# Varsity → trading_os_v1 Engine Mapping

Source: mappings created strictly from files in `docs/varsity-extraction/` (modules 01,02,03,04,07,09,10).

Guidelines used:
- Each mapping cites the source module and the exact extracted rule or principle from that file.
- Status values: `direct for v1`, `optional later`, `not suitable for automation`, `explanation-only` (for subjective items requiring human review).
- No new rules were invented; only principles and v1-Safe Rules from the extraction files were used.

---

## Universe Engine (Security Selection)
- Principle: "Only consider companies with ROE > 12% and net margin > 5% (quality threshold)" — Source: Module 03 (Fundamental Analysis) — Status: direct for v1 — Notes: exact v1-Safe rule for candidate filtering.

- Principle: "Trade only contracts with minimum 1M average daily volume" — Source: Module 04 (Futures Trading) — Status: direct for v1 — Notes: applies to futures; use as liquidity gate.

- Principle: "Liquidity Check: Verify both assets have minimum average daily volume before entry" — Source: Module 10 (Trading Systems) — Status: direct for v1 — Notes: used for pair/trading-system universe filtering.

---

## Fundamental Engine (Business Quality Validation)
- Principle: "Quality Gate: Only consider companies with ROE > 12% and net margin > 5%" — Source: Module 03 — Status: direct for v1 — Notes: primary fundamental filter.

- Principle: "Verify reported growth through FCF growth (at least 70% correlation)" — Source: Module 03 — Status: direct for v1 — Notes: implement as correlation check between reported growth and FCF series where data available.

- Principle: "Flag positions if debt/EBITDA exceeds 3.0 or is increasing" — Source: Module 03 — Status: direct for v1 — Notes: straight numeric threshold for debt risk screening.

- Principle: "Valuation Discipline: Apply PEG-based maximum P/E (don't overpay regardless of growth story)" — Source: Module 03 — Status: optional later — Notes: requires forward-earnings or growth inputs; implement when forecast data available.

- Principle: "Flag if payout ratio > 60% or declining" — Source: Module 03 — Status: direct for v1 — Notes: dividend safety check.

- Principle: "Document management changes; require manual re-evaluation if CEO/CFO changes" — Source: Module 03 — Status: explanation-only — Notes: subjective/qualitative; human review required.

---

## Technical Engine (Price/Volume Signal Generation)
- Principle: "Classify each candle as bullish (close > open) or bearish (close < open)" — Source: Module 02 (Technical Analysis) — Status: direct for v1 — Notes: basic indicator construction.

- Principle: "Compute volume moving average and flag breakouts exceeding threshold" and "Require volume confirmation for trade signals (breakout volume > 1.5x average)" — Source: Module 02 — Status: direct for v1 — Notes: implement volume confirmer and moving-average threshold.

- Principle: "Identify support/resistance as recent local extrema within lookback window" — Source: Module 02 — Status: direct for v1 — Notes: provide levels to Decision and Explanation engines.

- Principle: "Calculate and report trend state (uptrend: HH & HL, downtrend: LL & LH)" — Source: Module 02 — Status: direct for v1 — Notes: trend classifier used in signal gating.

- Principle: "Require pattern confirmation rules (e.g., 2-candle confirmation before trade signal)" — Source: Module 02 (Pattern Validity Checker) — Status: optional later — Notes: rule appears as candidate; implement when sequence logic added.

- Principle: "Volatility Adjuster: Scale position size based on current volatility relative to average" — Source: Module 02 — Status: direct for v1 — Notes: feed into Risk engine.

- Principle: "Deep historical pattern catalogs and visual chart reading skills" — Source: Module 02 (Educational Only) — Status: not suitable for automation — Notes: human learning.

---

## Event Engine (News & Corporate Events)
- Principle: "Document management changes; require manual re-evaluation if CEO/CFO changes" — Source: Module 03 — Status: optional later — Notes: requires event feed and human review workflow.

- Principle: "Wash Sale Avoidance: Alert if selling security at loss and buying similar security within 30 days" — Source: Module 07 (Markets and Taxation) — Status: direct for v1 — Notes: transaction-rule based alert implementable from trade records.

- Principle: "News reaction patterns" — Source: Module 10 — Status: not suitable for automation — Notes: extraction lists as candidate but no news ingest rules; cannot implement from current docs.

---

## Risk Engine (Position Sizing, Portfolio Risk)
- Principle: "No trade exceeds 2% of portfolio capital at risk" — Source: Module 09 (Risk Management) — Status: direct for v1 — Notes: primary position sizing cap.

- Principle: "Calculate volatility continuously; reduce position size if volatility > 1.5x average" — Source: Module 09 — Status: direct for v1 — Notes: volatility-adjusted sizing.

- Principle: "Compute correlation among current holdings quarterly; alert if > 0.7 average correlation" — Source: Module 09 — Status: direct for v1 — Notes: portfolio-level diversification monitor.

- Principle: "Enforce stop-losses mechanically; never override without explicit user confirmation + documented reason" — Source: Module 09 — Status: direct for v1 — Notes: enforcement policy; override requires Explanation/human review.

- Principle: "Halt trading if realized losses exceed monthly drawdown ceiling (e.g., -2% of portfolio)" — Source: Module 09 — Status: direct for v1 — Notes: hard stop gating trading activity.

- Principle: "Report Sharpe ratio and expected return in every trade decision" — Source: Module 09 — Status: direct for v1 — Notes: metrics to compute and include in Explanation engine output.

- Principle: "Leverage cap 2:1 and margin utilization must stay below 50% (60% triggers reduction)" — Source: Module 04 — Status: direct for v1 — Notes: futures-specific risk rules; enforced by Risk engine.

- Principle: "Expiration Management: All futures positions closed or rolled 5 days before expiration" — Source: Module 04 — Status: direct for v1 — Notes: operational rule for position lifecycle.

---

## Decision Engine (Trade Logic & System Rules)
- Principle: "Do not execute trades if capital is below minimum emergency reserve" — Source: Module 01 (Introduction) — Status: direct for v1 — Notes: pre-trade gating rule.

- Principle: "Validate that proposed returns justify the risk exposure" (Risk-return validator) — Source: Module 01 — Status: direct for v1 — Notes: quantitative check; feed from Risk and Fundamental engines.

- Principle: "Pair Requirement: All multi-leg strategies require correlation check (ρ > 0.7 over last 252 days)" — Source: Module 10 — Status: direct for v1 — Notes: entry gating for pair systems.

- Principle: "Spread Monitoring: Calculate and report spread Z-score for every pair position" and "Entry Rules: Generate signal only when Z-score > 2.0; Exit when Z-score < 0.5" — Source: Module 10 — Status: direct for v1 — Notes: deterministic system rules implemented in Decision engine.

- Principle: "Require volume confirmation for trade signals (breakout volume > 1.5x average)" — Source: Module 02 — Status: direct for v1 — Notes: technical gating for Decision engine.

- Principle: "Valuation Discipline: Apply PEG-based maximum P/E" — Source: Module 03 — Status: optional later — Notes: needs forward earnings/growth inputs; can influence Decision engine when available.

- Principle: "No subjective override of system rules; manual override must be documented" — Source: Module 10 & 09 — Status: direct for v1 — Notes: policy enforced by Decision + Explanation engines.

---

## Explanation Engine (Reasoning, Reporting, Audit Trail)
- Principle: "Calculate and display real return expectations (nominal - inflation)" — Source: Module 01 — Status: direct for v1 — Notes: include in trade rationale.

- Principle: "Include support/resistance levels in trade decision reasoning" — Source: Module 02 — Status: direct for v1 — Notes: expose levels and their origin to explanation output.

- Principle: "Cost Basis: Record purchase price + all transaction costs + taxes for each position" — Source: Module 07 — Status: direct for v1 — Notes: required for tax reporting and audits.

- Principle: "Tax Reserve: Allocate 25-30% of trading profits to tax reserve; update quarterly" — Source: Module 07 — Status: direct for v1 — Notes: recommend as part of account-level reporting.

- Principle: "Report Sharpe ratio and expected return in every trade decision" — Source: Module 09 — Status: direct for v1 — Notes: metrics included in Explanation output.

- Principle: "Document any manual override with reason" — Source: Module 10 & 09 — Status: direct for v1 — Notes: audit trail requirement; Explanation engine stores override metadata.

- Principle: "Management Stability: Document management changes; require manual re-evaluation if CEO/CFO changes" — Source: Module 03 — Status: explanation-only — Notes: flag for human review and narrative explanation rather than automated decision-making.

---

## Notes and Constraints
- All mapped items above are strictly taken from the `v1-Safe Rules`, `Candidate Engine Mappings`, `Implementation Candidates`, and other explicit rule sections found in the module files inside `docs/varsity-extraction/`.
- Where a rule in the extraction explicitly requires external feeds or forecasting (for example forward earnings for PEG), the mapping marks it `optional later` rather than `direct for v1` to avoid inventing data requirements.
- Subjective, qualitative guidance (management assessment, visual chart reading, behavioral coaching) is marked `explanation-only` or `not suitable for automation`.

---

## Next Steps
1. I will mark the second todo as completed and the third as in-progress once you confirm this file looks correct.
2. If you want, I can also produce JSON or CSV exports of this mapping to drive scaffolding code.


