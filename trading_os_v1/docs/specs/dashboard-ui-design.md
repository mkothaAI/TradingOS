# Dashboard UI Design Note

## Purpose
This dashboard is an operator-facing, trading-grade status surface for observing provider health, eligibility, evidence lineage, composition results, synthesized verdicts, and post-entry monitoring in real time.

The backend remains the source of truth. The UI should consume backend-owned contracts only and should not derive its own business logic for provider health, evidence quality, or eligibility.
The UI must not infer trading logic from presentation-only state. It should render backend-owned freshness labels, advisory follow-up surfaces, and monitoring alerts without recomputing policy.

## Scope
In scope for the first dashboard slice:
- Provider health grid
- Eligibility/status table
- Evidence/provenance timeline
- Composition/fallback panel
- Live quote/watch panel placeholder
- Diagnostics drawer or side panel
- Synthesized verdict summary and explanation panel
- Advisory follow-up panel for asking a named agent or the verdict a question
- Options analysis panel placeholder
- Monitoring/watchtower panel placeholder for post-entry alerts

Out of scope for now:
- Streamlit
- React/Next.js implementation
- Order entry or execution controls
- Broker connectivity
- Charting implementation
- Authentication and user management
- Causal/research orchestration

## Recommended Architecture
Use a thin dashboard view-model layer on top of the existing backend contracts.

Backend ownership:
- Provider health summaries
- Eligibility verdicts
- Evidence summaries and provenance artifacts
- Composition outcomes
- Streaming transport payloads

UI ownership later:
- Panel layout and rendering
- Filtering, sorting, and local affordances
- Visual theming and responsiveness

Recommended boundary:
- Backend emits transport payloads and dashboard-facing view models.
- Dashboard renders those payloads without recomputing eligibility or evidence status.

## View-Model Boundaries
The dashboard should consume small, deterministic view models derived from backend contracts:
- Dashboard summary card
- Provider status row
- Evidence timeline item
- Composition result panel

These should be backend-owned, framework-agnostic, and serializable.

## Panel Definitions

### 1. Provider Health Grid
Source contracts:
- `HealthSnapshot`
- `EligibilitySnapshot`

Transport:
- SSE

User action:
- Inspect provider and capability status at a glance

Deferred:
- Inline editing, filtering rules, and custom alerting

### 2. Eligibility / Status Table
Source contracts:
- `EligibilitySnapshot`
- `HealthSnapshot`
- `EvidenceSummary`

Transport:
- SSE

User action:
- Compare health and eligibility by provider and capability

Deferred:
- User-defined scoring or overrides

### 3. Evidence / Provenance Timeline
Source contracts:
- `EvidenceSummary`

Transport:
- SSE

User action:
- Inspect raw versus normalized evidence counts, evidence IDs, and time bounds

Deferred:
- Artifact diffing UI and raw payload viewers

### 4. Composition / Fallback Panel
Source contracts:
- `CompositionOutcome`

Transport:
- SSE

User action:
- Review provider selection, fallback selection, and partial failures

Deferred:
- Manual override controls and routing policies

### 5. Live Quote / Watch Panel Placeholder
Source contracts:
- Future quote/tick stream payloads

Transport:
- Browser remains on SSE
- Backend bridges the Twelve Data websocket quote feed into SSE quote/watch updates

User action:
- Watch the backend-owned live quote stream without local quote logic

Deferred:
- Any quote visualization or market interaction features

The panel contract stays backend-owned and intentionally small: a primary symbol plus a fixed multi-symbol watchlist, last price, provider/source, update timestamp, operator-facing status/copy, freshness/severity cues, feed/stream status, stale/live state, reconnect attempts/backoff, and last error if the feed is recovering or disconnected.
The panel must explicitly label whether the displayed evidence is real-time, delayed, stale, or snapshot.

### 6. Synthesized Verdict / Explanation Panel
Source contracts:
- Decision payloads
- Explanation payloads

Transport:
- SSE

User action:
- Review the final symbolic verdict and the cited rationale without changing the verdict itself

Deferred:
- Manual overrides and policy editing

### 7. Advisory Follow-Up Panel
Source contracts:
- Planned follow-up payloads
- Explanation payloads
- Decision payloads

Transport:
- SSE

User action:
- Ask a follow-up question about a ticker analysis to a specific advisory agent or to the synthesized verdict

Deferred:
- Free-form autonomous chat and policy generation

### 8. Options Analysis Panel
Source contracts:
- Planned options payloads
- Explanation payloads

Transport:
- SSE

User action:
- Inspect strike, expiry, implied volatility, greeks, liquidity, and spread quality in a structured options view

Deferred:
- Options execution controls and broker interaction

### 9. Monitoring / Watchtower Panel
Source contracts:
- Planned monitoring payloads
- Decision payloads
- Explanation payloads

Transport:
- SSE

User action:
- Track thesis breakage, stop-loss breaches, volatility changes, macro shocks, and options-specific risk changes after entry

Deferred:
- Automated policy overrides and execution actions

### 10. Diagnostics Drawer / Side Panel
Source contracts:
- Diagnostics bundle
- Health snapshot
- Evidence summary
- Eligibility snapshot
- Composition outcome

Transport:
- SSE

User action:
- Drill into current provider state, recent errors, and provenance context

Deferred:
- Deep interactive debugging tools

## Transport Guidance
Use SSE for one-way dashboard updates:
- Provider health
- Eligibility
- Evidence
- Diagnostics
- Composition updates
- Verdict summaries
- Follow-up answers
- Monitoring alerts

Use WebSocket only for live quote/tick panels or explicitly interactive low-latency streams.

Do not broaden WebSocket usage beyond live market streaming at this stage.

## What Remains Backend-Only
- Eligibility and health classification
- Evidence persistence and lineage
- Provider selection and fallback policy
- Composition execution logic
- Error classification and retry decisions
- Symbolic verdict authority and deterministic gating
- Monitoring alert generation and alert severity assignment
- Options risk classification and freshness labeling

## Next Implementation Slice
The next implementation slice should be a UI shell that renders these backend contracts without recomputing them, starting with the provider health grid, synthesized verdict panel, and diagnostics drawer fed by SSE payloads.