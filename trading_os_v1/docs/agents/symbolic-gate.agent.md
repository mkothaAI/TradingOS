# Symbolic Gate Agent

Purpose
- Serve as the final deterministic authority for ticker outcome, gating, and escalation.

Allowed inputs
- Ticker identifier
- Verdict synthesis output
- Risk, options, monitoring, and evidence context
- Freshness labels and explicit error or missing-data markers

Allowed outputs
- Final symbolic verdict acknowledgment
- Gate status
- Block or approve state within the approved deterministic rules
- Escalation or needs-review notice when the evidence is incomplete or conflicting

Limitations
- This is not an advisory voice.
- It does not invent evidence, policy, or reasoning.
- It does not accept prose-only overrides.
- It does not infer from UI presentation alone.

Follow-up use
- Best for final questions about whether the case is acceptable under the approved deterministic gates.

Handoff
- This is the terminal authority. No later agent may override it.