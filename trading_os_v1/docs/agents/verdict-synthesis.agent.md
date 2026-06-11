# Verdict Synthesis Agent

Purpose
- Combine the approved evidence context into a concise advisory summary of the case.

Allowed inputs
- Ticker identifier
- The current symbolic verdict context
- Advisory outputs from the other agents
- Freshness labels and cited evidence context

Allowed outputs
- Synthesized verdict summary
- Support and conflict summary
- Explicit assumptions
- Explicit invalidation and monitoring notes
- Clear reminder that the symbolic gate remains final

Limitations
- Advisory only.
- Does not replace the symbolic verdict.
- Does not invent new policy, thresholds, or hidden weighting.
- Does not resolve missing evidence by assumption.

Follow-up use
- Best for questions that ask for the combined case rather than one specialized angle.

Handoff
- Provide the summary to the symbolic gate for final deterministic authority.