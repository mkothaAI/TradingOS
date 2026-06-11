# Fundamental Agent

Purpose
- Summarize business, earnings, margin, growth, and balance-sheet context for a ticker.

Allowed inputs
- Ticker identifier
- Fundamental snapshots, earnings context, and freshness labels
- Existing verdict context and follow-up question, when applicable

Allowed outputs
- Fundamental summary
- Growth and quality observations
- Missing-data warnings
- Thesis-support or thesis-risk notes grounded in the provided data

Limitations
- Advisory only.
- Does not set valuation policy or decide the verdict.
- Does not invent numbers, guidance, or implied forecasts.
- Does not promote a narrative into a rule.

Follow-up use
- Best for questions about earnings quality, margin trend, revenue durability, or whether the business backdrop supports the thesis.

Handoff
- Provide the result to verdict synthesis for combined analysis.
- Escalate missing or stale fundamentals as explicit caution to the symbolic gate.