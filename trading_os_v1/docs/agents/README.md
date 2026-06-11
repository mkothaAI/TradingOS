# trading_os_v1 Agent Prompt Pack

This directory defines the advisory-only agent surface for ticker analysis follow-up, options analysis, monitoring, and verdict synthesis.

Shared rules
- Agents are advisory only.
- The symbolic gate is the final authority.
- No agent may replace deterministic validation, invent policy, or override the backend verdict.
- Every answer must stay grounded in the approved evidence context and use the canonical freshness labels: real_time, delayed, stale, snapshot.
- Follow-up answers must remain traceable to a ticker analysis, a named advisory agent, or the synthesized verdict.

Canonical role map
- market-structure.agent.md: price action, trend, structure, and key levels.
- fundamental.agent.md: business quality, earnings context, and financial context.
- macro.agent.md: macro regime, rates, liquidity, and event context.
- bull-thesis.agent.md: upside case construction with explicit evidence and assumptions.
- bear-thesis.agent.md: downside case construction with explicit evidence and assumptions.
- risk-manager.agent.md: risk framing, sizing constraints, stop-loss, invalidation, and capital preservation.
- discipline.agent.md: process discipline, checklists, waiting rules, and no-trade enforcement.
- options-structure.agent.md: strike, expiry, premium structure, liquidity, and spread quality.
- volatility-greeks.agent.md: implied volatility and greek interpretation for options analysis.
- monitoring-watchtower.agent.md: post-entry monitoring and alert triggers.
- verdict-synthesis.agent.md: combine evidence into an explainable advisory summary.
- symbolic-gate.agent.md: final deterministic authority and policy gate.

Prompt-pack conventions
- Keep every prompt original and non-copied.
- Use only the approved vocabulary from the spec and rules files.
- Ask for evidence, assumptions, timestamps, thresholds, and freshness labels when relevant.
- Prefer refusal or needs-review language over unsupported conclusions.
- Never infer trading logic from UI presentation alone.

Handoff rule
- The output of any advisory agent is input to the synthesized verdict or the symbolic gate, never a replacement for either.