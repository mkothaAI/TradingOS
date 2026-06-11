Module: Risk Management & Trading Psychology

Source files used:
- trading_os_v1/source/Varsity/9 Risk Management and Trading Psychology/Module 9_Risk Management & Trading Psychology.pdf (full PDF text extracted)

Extraction status:
- status: verified (text extracted)
- extraction_date: 2026-05-15
- extractor: pdfplumber (text-only extraction)

## Module summary
This module covers portfolio-level risk concepts and trader psychology. It explains expected return, variance, covariance, variance–covariance and correlation matrices, portfolio variance and optimization (including solver usage in Excel), equity curves, Value at Risk (VaR), and position sizing techniques (unit-per-fixed-amount, percentage margin, percentage volatility, Kelly's criterion). It also discusses common trading biases and psychological pitfalls.

## Chapter-by-chapter notes
- Chapter 1: Orientation Note (pages 3–5)
  - Source location: page 3–5
  - Key points:
    - The module focuses on Risk Management and Trading Psychology; psychological biases to be covered include anchoring, recency (regency) bias, confirmation bias, bandwagon effect, loss aversion, illusion of control, hindsight bias. (p.5)

- Chapter 2: Risk (Part 1) (pages 6–11)
  - Source location: pages 6–11
  - Key points:
    - "For every rupee of profit made by a trader, there must be a trader losing that rupee." (p.6)
    - Distinguishes unsystematic vs systematic risk; diversification reduces unsystematic risk and the effect flattens after ~20 stocks (p.8–9).
    - Expected return example: E(Rp) = 50% * 20% + 50% * 15% = 17.5% (p.11).

- Chapter 3: Risk (Part 2) – Variance & Covariance (pages 12–17)
  - Source location: pages 12–17
  - Key points:
    - Defines variance: σ² = variance of returns; shows numeric example and calculation steps for daily return variance (p.12–14).
    - Steps to compute covariance between two stocks from daily returns (p.15–17).

- Chapter 4: Variance–Covariance Matrix (pages 20–26)
  - Source location: pages 20–26
  - Key points:
    - Explains construction of the variance–covariance matrix (k x k for k stocks) and discusses XT X and array formulas for Excel (p.22–26).

- Chapter 5: Correlation Matrix & Portfolio Variance (pages 29–37)
  - Source location: pages 29–37
  - Key points:
    - Shows how to derive correlation matrix from variance–covariance and standard deviations; discusses weighted standard deviation and portfolio variance calculation (p.30–36).

- Chapter 6: Equity Curve (pages 38–44)
  - Source location: pages 38–44
  - Key points:
    - Equity curve normalization example (start at Rs.100) and use of STDEV on portfolio daily returns (p.40–44).

- Chapter 7: Expected Returns (pages 45–51)
  - Source location: pages 45–51
  - Key points:
    - Use portfolio variance to estimate ranges for expected returns; annualization examples (p.47–49).

- Chapters 8–9: Portfolio Optimization (pages 52–74)
  - Source location: pages 52–74
  - Key points:
    - Excel Solver usage to minimize variance or maximize returns subject to constraints; efficient frontier discussion (p.52–74).

- Chapter 10: Value at Risk (VaR) (pages 75–86)
  - Source location: pages 75–86
  - Key points:
    - VaR definition (e.g., portfolio VaR as the least value within 95% of observations; example given -1.48% in the text) and methodology using return distribution (p.85).

- Chapters 11–13: Position Sizing for Active Trader (pages 87–107)
  - Source location: pages 87–107
  - Key points:
    - Position sizing techniques discussed: Unit-per-fixed-amount, Percentage Margin, Percentage Volatility, Total Equity vs Reduced Total Equity models (p.95–100).
    - Examples: guidance such as "you would not want to trade more than 1 lot of futures per 100,000 of any asset at any given point." (p.103) and use of ATR for volatility-based sizing (p.106).

- Chapter 14: Kelly's Criterion (pages 108–116)
  - Source location: pages 108–116
  - Key points:
    - Kelly formula presented and applied: "Kelly % = W - [(1-W)/R]" with worked example (p.115–116).

- Chapter 15: Trading Biases (pages 117–122+)
  - Source location: pages 117 onward
  - Key points:
    - Discussion and examples of behavioral biases, intuition, and limits to controlling market outcomes (p.117–122).

## Key principles (verbatim / faithful excerpts)
- "For every rupee of profit made by a trader, there must be a trader losing that rupee." (p.6)
- Diversification reduces unsystematic risk; after ~20 stocks unsystematic risk flattens (p.8–9).
- Expected portfolio return = weighted sum of individual expected returns (example p.11).
- Variance and covariance computation steps for returns (Chap 3, p.12–17).
- Construct variance–covariance and correlation matrices to compute portfolio variance (Chap 4–5, p.20–36).
- Portfolio optimization via solver (Chap 8–9, p.52–74).
- VaR defined as the least value within the top X% of observations (95% example provided) (p.85).
- Position sizing families: Unit-per-fixed-amount; Percentage Margin; Percentage Volatility; Kelly's Criterion (p.95–116).
- Common biases enumerated: anchoring, recency, confirmation, bandwagon, loss aversion, illusion of control, hindsight bias (p.5).

## Deterministic rules candidates (explicit statements present in source)
- Expected return calculation: E(R_p) = Σ w_i * E(R_i) (illustrated with numeric example) (p.11).
- Variance calculation formula and procedure for daily returns (p.12–14).
- Covariance computation steps (p.15–17).
- Correlation matrix derived from variance–covariance matrix divided by product of standard deviations (p.30–33).
- Portfolio variance via matrix operations and weighted standard deviation (p.35–36).
- VaR calculation by percentile of empirical return distribution (95% example) (p.85).
- Kelly's criterion formula: Kelly% = W - [(1 - W) / R] (p.115).
- Position sizing examples: "not more than 1 lot of futures per 100,000" (explicit example, p.103).

## Risk principles
- Distinguish systematic vs unsystematic risk; diversify to reduce unsystematic risk (p.6–9).
- No investment/trade should be considered safe; aim to minimise, not eliminate, systematic risk (p.10).
- Use portfolio variance and correlation to understand aggregated risk (Chap 3–5).
- Use stop-loss, position sizing, reduced-total-equity model to limit exposure (p.95–101).

## Psychology principles
- List of cognitive biases to watch: anchoring, recency (regency), confirmation, bandwagon, loss aversion, illusion of control, hindsight bias (p.5).
- "Recovery trauma": tendency to take larger risks after losses (p.93–94) — discussed as a psychological pitfall.
- Emphasizes discipline in position sizing and avoidance of revenge trading (p.91–94).

## Formulas and measurable logic (quoted when present)
- Expected return (example): E(R_p) = 50% * 20% + 50% * 15% = 17.5% (p.11).
- Variance calculation steps and example leading to σ² = 0.00636 (example walkthrough) (p.13–14).
- Correlation formula: correlation = covariance / (σ_x * σ_y) (p.30–33).
- Portfolio variance via matrix operations (XT X to k x k matrix; see Chap 4, p.22–26).
- VaR: empirical percentile (95% example; Portfolio VaR = least value within 95% of observations, example -1.48%) (p.85).
- Kelly's Criterion: Kelly% = W - [(1-W)/R] with worked numeric example (p.115–116).

## Items suitable for automation
- Compute expected return given weights and asset expected returns (Chap 2, p.11).
- Compute daily returns, variance, covariance, variance–covariance matrix, correlation matrix (Chap 3–5, p.12–36).
- Compute portfolio variance and annualize variance (Chap 5–7, p.35–49).
- Compute VaR from empirical distribution (Chap 10, p.84–86).
- Implement position sizing calculators for: unit-per-fixed-amount, percentage margin, percentage volatility (requires ATR), Kelly's criterion (Chap 11–14, p.95–116).

## Items not suitable for automation (explanation-only / human-review)
- Behavioral coaching, trader psychology remediation, judgment about when a trader "should" take subjective decisions — explanation-only (Chap 1, Chap 15, p.3–5, p.117+).
- Visual charts and Excel screenshots referenced in the PDF (graphs, worksheet interactions) — these are not captured as deterministic rules in text and require human inspection (various pages where images/Excel are referenced).

## Engine mapping candidates
- Risk engine:
  - Portfolio variance calculation (variance–covariance → portfolio variance) — Source: Chap 3–5 (p.12–36) — Status: direct for v1
  - Correlation matrix and correlation alerts — Source: Chap 5 (p.29–36) — Status: direct for v1
  - VaR computation — Source: Chap 10 (p.84–86) — Status: direct for v1
  - Position sizing methods (unit, margin, volatility, Kelly) — Source: Chap 11–14 (p.95–116) — Status: direct for v1 (calculator implementations)

 - Decision engine:
  - Position sizing thresholds and stop-loss enforcement as gating inputs (Chap 11–13) — Status: direct for v1 (when numeric inputs available)

 - Explanation engine:
  - Report metrics: portfolio variance, VaR, expected return, Kelly %, position sizing rationale — Source: multiple chapters — Status: direct for v1

 - Fundamental / Universe / Technical engines:
  - Not primary consumers for this module; map only risk-specific outputs into their decision inputs when available (status: optional later)

## V1 inclusion candidates
- Implement calculators for: daily returns, variance, covariance, correlation matrix, portfolio variance, VaR (95%), ATR-based percentage volatility sizing, Kelly% computation. All are explicit and deterministic in the source (p.12–16, p.29–36, p.84–116).

## V1 exclusion candidates
- Behavioral coaching, psychological remediation workflows, and subjective trader therapy — explicitly narrative in the source and not automatable (Chap 1 & 15).
- Visual/Excel workbook-dependent interactive steps (screenshots/Excel solver UI) — since the workbook is not supplied, interactive Excel steps are out-of-scope for v1 (Chap 8–9 screenshots referenced).

## Open questions / missing material
- Module 12 ("Innerworth - Mind over markets") folder is empty in source; not included here. (manifest-source.md notes missing module 12.)
- Several chapters reference Excel workbooks and graphs (e.g., solver worksheets, frequency tables, EQ curve). The PDF text references these but the underlying workbook and images are not captured as structured data; confirm if you can provide the Excel worksheets or higher-resolution images for precise reproduction (multiple pages, e.g., Chap 4–9, Chap 6, Chap 10).
- Verify acceptable numeric conventions for V1 (e.g., VaR confidence level default 95% vs configurable) — the PDF uses 95% as example but does not prescribe a single default.

## trading_os_v1 implications
This section separates candidate outputs for the `trading_os_v1` system based only on explicit content in the source PDF.

### direct rule candidates
- Compute expected portfolio return as weighted sum of asset expected returns (Chap 2, p.11).
- Compute daily returns, variance, covariance, variance–covariance matrix, and correlation matrix (Chap 3–5, p.12–36).
- Compute portfolio variance and annualize (Chap 5–7, p.35–49).
- Compute VaR empirically (95% example) from return distribution (Chap 10, p.84–86).
- Implement position sizing calculators: unit-per-fixed-amount; percentage margin; percentage volatility (requires ATR input); Kelly's criterion computation (Chap 11–14, p.95–116).
- Enforce simple operational guidance noted in examples (e.g., limit futures lots per account as in example "1 lot per 100,000" — treat as illustrative unless you supply firm thresholds) (p.103).

### explanation-only ideas
- Present behavioral bias list and explanatory excerpts for user-facing documentation and training content (Chap 1 & 15, p.5, p.117+).
- Human-readable descriptions of portfolio optimization steps and screenshots referenced in the PDF (Chap 8–9) — include as part of training/explainers.

### human-review-only ideas
- Any manual override of solver/optimization choices or interpretation of Excel solver outputs should be reviewed by a human (Chap 8–9).
- Decisions requiring subjective judgment (e.g., choosing between total-equity vs reduced-equity model for a trader) — include as human-review prompts (Chap 11–13).

### out-of-scope for v1
- Interactive Excel solver replication (workbook + UI-driven steps) and automatic transcription of images/graphs into deterministic code without the original data files.
- Psychological coaching systems, personalized trader therapy, or subjective advice automation (explicitly narrative in the source).

---

Notes on extraction quality
- This document was generated from a text-only extraction of the PDF using `pdfplumber`. Charts, Excel screenshots and images are referenced in the PDF but not captured as structured data. Where the text references figures or worksheets, those artifacts were not available for direct extraction and are listed under `Open questions`.
