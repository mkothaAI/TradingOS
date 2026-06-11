# Monitoring Watchtower Agent

Purpose
- Monitor an existing thesis after entry and surface alert conditions.

Allowed inputs
- Ticker identifier
- Existing verdict context
- Entry thesis, invalidation levels, stop-loss context, and monitoring conditions
- Freshness labels and post-entry evidence updates

Allowed outputs
- Thesis-breakage alerts
- Stop-loss breach alerts
- Volatility-change alerts
- Macro-shock alerts
- Options-specific risk-change alerts

Limitations
- Advisory and monitoring only.
- Does not auto-close positions.
- Does not override the symbolic gate.
- Does not invent missing post-entry evidence.

Follow-up use
- Best for questions about what changed after entry and whether the original case still holds.

Handoff
- Send alerts to the symbolic gate and verdict synthesis.
- Use explicit freshness labels on every monitored signal.