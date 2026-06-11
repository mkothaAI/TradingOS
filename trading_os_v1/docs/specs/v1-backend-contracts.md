# trading_os_v1 — Backend Contracts (V1)

This file defines JSON-like backend contracts for `trading_os_v1` engines. It uses only the v1 rules spec and the Varsity-extracted sources; no new rules are introduced.

1. Purpose
- Define backend service contracts (request/response shapes, shared types, error codes, invariants, and acceptance tests) for `trading_os_v1` engines.
- Contracts are implementation-agnostic JSON-like schemas suitable for backend services.
- This document also establishes the approved product vocabulary for later follow-up, options, and monitoring work. Those surfaces are planned here before any concrete schema or code is added.

2. Service boundaries
- Universe engine: maintain and filter tradable universe; exposes universe list and stats.
- Fundamental engine: evaluate configured fundamental checks; returns pass/fail and reasons.
- Technical engine: compute EOD indicators and structured signals.
- Event engine: ingest scheduled events and emit event flags/advisory.
- Risk engine: compute risk metrics and allowed sizing.
- Decision engine: consume signals and risk to produce deterministic decisions.
- Explanation engine: produce source-linked explanations for decisions.
- Follow-up surface: planned advisory Q&A layer over a specific agent or synthesized verdict.
- Options surface: planned advisory analysis of option structure and risk.
- Monitoring surface: planned post-entry surveillance and alerting view.

3.1 Recommendation runtime status
- Current status: partially live.
- Typed runtime path: live. The runtime source can build typed engine responses, then typed `DecisionInputs`, then typed `DecisionResponse`.
- Genuinely external/runtime-sourced raw fields today:
  - `price_series`
  - `scheduled_events`
- Compatibility-sourced raw fields today:
  - `fundamental_data`
  - `portfolio_state`
- Status definitions:
  - `typed runtime path`: the system uses real typed engine responses and typed `DecisionInputs`, even if some raw bundle fields are still compatibility-sourced.
  - `partially live`: at least one raw bundle field is sourced from a genuine runtime owner, but at least one required raw field is still synthetic or compatibility-sourced.
  - `fully live`: every raw field required by the raw orchestration input bundle is owned by a genuine runtime/external source, and the typed response chain remains intact end to end.

3.1.1 Acceptance criteria for fully live recommendation runtime
- The raw orchestration input bundle must be populated entirely by genuine runtime owners for every required field used by the recommendation path.
- `price_series` must come from a real market-data runtime owner.
- `scheduled_events` must come from a real event runtime owner.
- `fundamental_data` must come from a real fundamentals runtime owner.
- `portfolio_state` must come from a real account/holdings/positions runtime owner.
- The typed chain must remain unchanged: raw bundle -> typed engine responses -> typed `DecisionInputs` -> typed `DecisionResponse` -> recommendation bridge.
- The compatibility fallback path may remain for local/dev use, but the fully live status must only be claimed when the real runtime path is available without falling back.
- Dashboard transport, projection translators, and recommendation bridges must remain view/transport layers only; they may not become the source of truth for runtime ownership.

3. Canonical request/response contracts (JSON-like shapes)

Shared note: all requests include `request_id` (string UUID) and `as_of_date` (ISO 8601). All responses include `request_id`, `as_of_date`, `status` and `errors` (array).

- Universe engine
  - Request:
    {
      "request_id": "UUID",
      "as_of_date": "YYYY-MM-DD",
      "universe_config": { "allowed_markets": ["US"], "sector_caps": {"Technology":0.25}, "max_universe_size": 500 },
      "ticker_metadata": [{ "ticker":"AAPL", "exchange":"NASDAQ", "sector":"Technology", "market_cap": 2000000000, "lot_size":1, "tradable":true }]
    }
  - Response (200 / success):
    {
      "request_id":"UUID",
      "as_of_date":"YYYY-MM-DD",
      "status":"OK",
      "universe_list":[{"ticker":"AAPL","reason_codes":["MARKET_OK","SECTOR_OK"], "metadata":{} }],
      "universe_stats":{"count":100,"sector_exposures":{"Technology":0.23}},
      "errors":[]
    }
  - Failure response:
    { "status":"ERROR", "errors":[{"code":"UNIVERSE_EMPTY","message":"No tradable tickers after filters"}] }

- Fundamental engine
  - Request:
    { "request_id":"UUID", "as_of_date":"YYYY-MM-DD", "fundamental_config":{}, "fundamental_data": {"AAPL":{}} }
  - Response success:
    { "status":"OK", "results": {"AAPL": {"fundamental_pass": true, "reasons": [] } }, "errors": [] }
  - Failure per ticker: `MISSING_DATA`

- Technical engine
  - Request:
    { "request_id":"UUID", "as_of_date":"YYYY-MM-DD", "technical_config": {"atr_window":14,"ma_windows":[10,50]}, "price_series": {"AAPL":[{"date":"YYYY-MM-DD","open":..,"high":..,"low":..,"close":..,"volume":..}] } }
  - Response success:
    { "status":"OK", "indicators": {"AAPL": {"atr":1.23, "ma": {"10":150.12,"50":148.34}, "returns":[], "volatility":0.023 } }, "signals": {"AAPL": {"ma_cross":1, "candle_classification":"bullish", "atr_spike":false } }, "errors": [] }
  - Insufficient history error:
    { "status":"ERROR", "errors":[{"code":"INSUFFICIENT_HISTORY","message":"Require 60 EOD rows for AAPL"}] }

- Event engine
  - Request:
    { "request_id":"UUID", "as_of_date":"YYYY-MM-DD", "ticker_list":["AAPL"], "event_config": { "earnings_blackout_days_before": "example-derived, requires human confirmation", "earnings_blackout_days_after": "example-derived, requires human confirmation", "advisory_only": true }, "scheduled_events": { "AAPL": [ ... ] } }
    - Note: partial blackout config is deterministic; any missing side is treated as 0 days, not disabled.
    - Note: `ticker_list` is authoritative; the response must include every requested ticker even if no events exist.
  - Response:
    { "status":"OK", "event_flags": { "AAPL": { "earnings_upcoming": true, "blackout": false, "events": [] } }, "errors": [] }
    - `event_config` is request-only; it is not repeated in the response.
    - Only earnings events can trigger blackout in v1.

- Risk engine
  - Request:
    {
      "request_id":"UUID",
      "as_of_date":"YYYY-MM-DD",
      "risk_config": { "per_trade_risk_pct": "example-derived, requires human confirmation", "max_position_size_pct": 0.10, "max_leverage": 2.0, "var_confidence": "example-derived, requires human confirmation", "sizing_model": "percentage_volatility" },
      "portfolio_state": { "total_equity": 100000, "cash": 20000, "positions": [] },
      "price_series": { ... }
    }
  - Response success:
    { "status":"OK", "risk_metrics": { "portfolio_var": -0.023, "portfolio_variance": 0.0006, "volatility": 0.024 }, "size_info": { "AAPL": { "allowed_qty": 10, "risk_amount": 1000, "sizing_model_used": "percentage_volatility", "stop_distance": 2.0 } }, "errors": [] }
  - Failure examples: `RISK_ERROR`, `MARGIN_EXCEEDED`

- Decision engine
  - Request:
    {
      "request_id":"UUID",
      "as_of_date":"YYYY-MM-DD",
      "inputs": {
        "technical_signals": { "AAPL": {} },
        "fundamental_pass": { "AAPL": true },
        "risk_assessment": { "AAPL": { "allowed_qty": 10 } },
        "event_flags": { "AAPL": { "blackout": false } }
      },
      "policy_config": {}
    }
  - Response success (decision token MUST be one of the four):
    { "status":"OK", "decisions": { "AAPL": { "decision": "BUY_CANDIDATE", "size_info": { "allowed_qty": 10 }, "applied_rules": ["R0004","R0006"], "reason_codes": ["MA_CROSS","FUND_PASS","RISK_OK"] } }, "errors": [] }
  - If blocked: decision == "NO_TRADE" with `reason_codes` explaining which gate failed.

- Explanation engine
  - Request:
    { "request_id":"UUID", "as_of_date":"YYYY-MM-DD", "decision_payload": { "AAPL": { ... } }, "include_line_links": false }
  - Response:
    {
      "status":"OK",
      "explanations": {
        "AAPL": {
          "explanation_text": "Applied R0004 ATR and R0006 sizing",
          "source_links": [ { "rule_id": "R0006", "file": "docs/varsity-extraction/module-09-risk-management-trading-psychology.md", "line_range": null } ]
        }
      },
      "errors": []
    }
  - Note: `source_links` are best-effort file references; exact line-level traceability may be unavailable and must be indicated.

Planned future payload vocabulary
- Follow-up payloads should carry a `follow_up_question`, `agent_target`, `verdict_ref`, `evidence_context`, and explicit `freshness_labels`.
- Options payloads should carry option structure, implied volatility, greeks, liquidity, and spread-quality fields.
- Monitoring payloads should carry thesis-breakage, stop-loss, volatility-shift, macro-shock, and options-risk alert fields.
- These payload families are approved as product shape but are not yet concrete schemas in this document.

3.1.1 Follow-up interaction family, concrete design

This section defines the first concrete planned family. It is advisory-only and must not alter the symbolic verdict.

FollowUpTarget
- Purpose: identify whether the follow-up is directed at a named advisory agent or at the synthesized verdict.
- Proposed fields:
  - `target_kind`: enum with values `advisory_agent` and `synthesized_verdict`.
  - `target_name`: canonical machine-readable name, such as `market_structure`, `fundamental`, `macro`, `bull_thesis`, `bear_thesis`, `risk_manager`, `discipline`, `options_structure`, `volatility_greeks`, `monitoring_watchtower`, or `verdict_synthesis`.
  - `display_name`: human-readable label for the UI.
  - `is_authoritative`: boolean; must be `false` for advisory agents and `false` for synthesized verdict interactions as well, because the symbolic gate remains final.
  - `topic_tags`: list of canonical topic labels such as `structure`, `fundamentals`, `macro`, `options`, `risk`, `monitoring`, `discipline`.
- Validation rules:
  - `target_kind` is required.
  - `target_name` must match the approved agent or verdict vocabulary.
  - `is_authoritative` must never imply policy authority.
  - The symbolic gate is not a conversational target; it remains an internal final authority.
- Boundary notes:
  - This object is a routing descriptor only.
  - It must not carry policy, decision, or sizing fields.

FreshnessEnvelope
- Purpose: provide a reusable timestamp and freshness wrapper for all follow-up-family payloads and later families.
- Proposed fields:
  - `freshness_label`: enum with values `real_time`, `delayed`, `stale`, `snapshot`.
  - `evidence_timestamp`: UTC datetime for when the evidence was observed or sourced.
  - `received_at`: UTC datetime for when the system received the evidence.
  - `last_updated_at`: UTC datetime or null for the latest known update time.
  - `delay_seconds`: numeric or null; if present, must be non-negative.
  - `staleness_seconds`: numeric or null; if present, must be non-negative.
  - `delay_reason`: optional short text describing delayed or stale provenance.
- Validation rules:
  - `freshness_label` is required and must always be explicit.
  - UTC timestamps are required when present.
  - `real_time` should imply minimal delay and current receipt; `delayed` and `stale` must not be hidden.
  - A UI transport may be live while the envelope remains `delayed` or `stale`.
- Boundary notes:
  - This is the shared freshness primitive for later payload families.
  - It should align conceptually with `ProviderMeta.is_delayed`, `ProviderHealthStatus.staleness_seconds`, and `SourceLink.note` without reusing those types directly.

EvidenceContext
- Purpose: package the evidence a follow-up answer is allowed to cite.
- Proposed fields:
  - `ticker`: the ticker under analysis.
  - `analysis_id`: stable analysis identifier or thread identifier.
  - `verdict_ref`: identifier or token for the current synthesized verdict.
  - `evidence_ids`: list of evidence identifiers used in the answer.
  - `source_links`: list of existing source-link objects or equivalent reference records.
  - `primary_topics`: list of canonical topic labels tied to the evidence.
  - `freshness`: `FreshnessEnvelope`.
  - `evidence_window_start`: UTC datetime or null.
  - `evidence_window_end`: UTC datetime or null.
  - `provenance_summary`: short text summarizing raw versus normalized provenance state.
  - `stale_reason`: optional note when the evidence is delayed, stale, or partially missing.
- Validation rules:
  - `ticker`, `verdict_ref`, and `freshness` are required.
  - At least one of `evidence_ids` or `source_links` must be present.
  - Source links must remain citations only; they must not contain policy or decision text.
  - Missing or stale evidence must be explicit and cannot be compressed into a success-only summary.
- Boundary notes:
  - EvidenceContext is reusable across follow-up, synthesized verdict, and later recommendation payloads.
  - It should align with existing `SourceLink` and dashboard evidence/provenance concepts, but it is an analysis-side context object, not a transport-only view.

FollowUpQuestion
- Purpose: represent a user follow-up question about a ticker analysis.
- Proposed fields:
  - `question_id`: stable identifier for the question.
  - `thread_id`: optional identifier linking multiple questions and answers.
  - `ticker`: ticker under discussion.
  - `target`: `FollowUpTarget`.
  - `question_text`: original user question text.
  - `asked_at`: UTC datetime.
  - `as_of_date`: date for the analysis context.
  - `requested_by`: optional user or session label.
  - `evidence_context`: `EvidenceContext`.
  - `follow_up_mode`: optional enum or string to distinguish direct follow-up, clarification, or retrospective review.
- Validation rules:
  - `ticker`, `target`, `question_text`, `asked_at`, `as_of_date`, and `evidence_context` are required.
  - The question must be advisory in scope; it cannot request policy creation or verdict overrides.
  - The target must be a named advisory agent or the synthesized verdict, not an arbitrary free-form actor.
  - If the evidence is stale or delayed, that label must be preserved in the question context.
- Boundary notes:
  - This is the entry object for interactive follow-up.
  - It does not change the verdict state and must not be treated as an instruction to the symbolic gate.

FollowUpAnswer
- Purpose: represent the grounded advisory answer to a follow-up question.
- Proposed fields:
  - `answer_id`: stable identifier for the answer.
  - `question_id`: link back to the originating `FollowUpQuestion`.
  - `ticker`: ticker under discussion.
  - `target`: `FollowUpTarget` that was answered.
  - `answer_text`: advisory answer text.
  - `answer_type`: enum with values such as `advisory`, `refusal`, `needs_review`.
  - `generated_at`: UTC datetime.
  - `as_of_date`: date for the analysis context.
  - `evidence_context`: `EvidenceContext`.
  - `freshness`: `FreshnessEnvelope`.
  - `supporting_rule_ids`: list of rule or rule-like identifiers cited in the answer, if applicable.
  - `follow_up_summary`: optional short summary for UI display.
- Validation rules:
  - `question_id`, `ticker`, `target`, `answer_text`, `generated_at`, `as_of_date`, `evidence_context`, and `freshness` are required.
  - The answer must stay advisory and cannot modify, replace, or obscure the symbolic verdict.
  - If evidence is incomplete, the answer should prefer refusal or needs-review language over unsupported conclusions.
  - `supporting_rule_ids` are citations only and must not become hidden policy.
- Boundary notes:
  - This object is the output of the follow-up family.
  - It is compatible with later dashboard views, but it remains a domain object first.

Legacy vocabulary alignment for follow-up planning
- `FollowUpQuestion` is conceptually similar to request models in `backend/schemas/models_requests.py`, but it needs richer routing and evidence context than the older generic request shapes.
- `FollowUpAnswer` is conceptually similar to `ExplanationItem` and `ExplanationResponse` in `backend/schemas/decision_models.py` and `backend/schemas/models_responses.py`, but it is broader because it must retain target routing, freshness, and evidence context.
- `EvidenceContext` should reuse the spirit of `SourceLink` from `backend/schemas/shared.py` and the evidence/provenance ideas already present in the trading_os_v1 provider stack, without collapsing into a plain list of citations.
- `FreshnessEnvelope` aligns with `ProviderMeta.is_delayed` and `ProviderHealthStatus.staleness_seconds` conceptually, but it needs to be reusable by non-provider analysis payloads.

3.1.2 Structured analysis / recommendation family, concrete design

This family is advisory-first. It packages the analysis around a ticker and its recommended posture, but it does not replace the symbolic verdict.

TickerAnalysisPackage
- Purpose: top-level analysis container for one ticker and one analysis context.
- Proposed fields:
  - `analysis_id`: stable analysis identifier.
  - `ticker`: ticker symbol under analysis.
  - `as_of_date`: analysis date.
  - `generated_at`: UTC datetime when the package was assembled.
  - `symbolic_verdict_ref`: reference to the final verdict token or verdict record.
  - `evidence_context`: `EvidenceContext`.
  - `freshness`: `FreshnessEnvelope`.
  - `target_context`: optional `FollowUpTarget` when the package is created in response to a follow-up.
  - `recommendation_blocks`: ordered list of `RecommendationBlock` objects.
  - `primary_recommendation`: optional short code or label for the leading advisory posture.
  - `analysis_summary`: short human-readable summary of the overall case.
  - `confidence_label`: optional qualitative label such as `low`, `moderate`, or `high`, if and only if it is explicitly derived from the provided evidence context.
  - `assumption_summary`: optional short summary of explicit assumptions.
- Validation rules:
  - `analysis_id`, `ticker`, `as_of_date`, `generated_at`, `symbolic_verdict_ref`, `evidence_context`, and `freshness` are required.
  - The package must not compute or modify the symbolic verdict.
  - Confidence labels, if used, must be advisory and must not masquerade as deterministic truth.
  - If the package is created from a follow-up, it should preserve the same evidence freshness and verdict reference.
- Boundary notes:
  - This is the parent object for the recommendation family.
  - It should be reusable by later dashboard rendering and by future recommendation/decision packages, but it remains analysis-domain first.

RecommendationBlock
- Purpose: group one advisory recommendation angle, such as an entry view, risk view, invalidation view, or monitoring view.
- Proposed fields:
  - `block_id`: stable identifier for the block.
  - `block_type`: enum with values `entry`, `risk`, `invalidation`, `monitoring`.
  - `headline`: short advisory label.
  - `summary`: concise narrative for the block.
  - `status`: enum with values such as `supportive`, `cautionary`, `blocking`, `watching`.
  - `evidence_context`: `EvidenceContext`.
  - `freshness`: `FreshnessEnvelope`.
  - `entry_plan`: optional `EntryPlan`.
  - `risk_plan`: optional `RiskPlan`.
  - `invalidation_plan`: optional `InvalidationPlan`.
  - `monitoring_plan`: optional `MonitoringPlan`.
  - `supporting_rule_ids`: optional list of rule identifiers.
  - `notes`: optional free text for the advisory summary.
- Validation rules:
  - `block_id`, `block_type`, `headline`, `summary`, `status`, `evidence_context`, and `freshness` are required.
  - A block may include one or more plan sub-objects, but it should not duplicate the same field across multiple sub-objects unless the relationship is explicit.
  - The block is advisory and must not be the sole source of truth for the symbolic verdict.
  - If a block is marked `blocking`, that means the advisory case is blocked; it does not automatically mutate the final verdict.
- Boundary notes:
  - This object is the bridge between the analysis package and the individual plan objects.
  - It should be easy to render in the UI without recomputing any logic.

EntryPlan
- Purpose: capture the planned entry posture in structured form.
- Proposed fields:
  - `entry_bias`: enum or string such as `long`, `short`, `wait`, `no_entry`.
  - `timing_window`: optional text or structured window describing when entry is acceptable.
  - `capital_allocation`: optional numeric or percentage allocation reference.
  - `size_plan`: optional `SizeInfo`-like object or a future equivalent size summary.
  - `entry_conditions`: list of explicit conditions that should be satisfied before entry.
  - `entry_triggers`: list of trigger descriptions that are observable in the evidence context.
  - `entry_rationale`: short explanation of why the entry posture exists.
  - `freshness`: `FreshnessEnvelope`.
  - `evidence_context`: `EvidenceContext`.
- Validation rules:
  - `entry_bias`, `entry_conditions`, `entry_rationale`, `evidence_context`, and `freshness` are required.
  - Entry plans must not embed a final verdict token as if it were a policy rule.
  - If a size reference is included, it must remain advisory and should not exceed the deterministic risk contract later defined by risk engine outputs.
  - Timing and capital allocation references must be explicit, not implied.
- Boundary notes:
  - This object is a planning surface, not an execution instruction.
  - It should align conceptually with `SizeInfo` and the decision pipeline, but it must remain advisory until the decision engine consumes it.

RiskPlan
- Purpose: capture the structured risk posture for the analysis package.
- Proposed fields:
  - `risk_level`: qualitative label such as `low`, `moderate`, `high`, or a future deterministic gate label.
  - `stop_loss`: explicit stop price, stop distance, or stop logic descriptor.
  - `waiting_time`: optional hold-off period before acting or before reassessment.
  - `hold_time`: optional intended holding window.
  - `capital_at_risk`: optional numeric reference.
  - `risk_conditions`: list of conditions that must remain true for the case to stay acceptable.
  - `risk_notes`: short explanation of the risk posture.
  - `freshness`: `FreshnessEnvelope`.
  - `evidence_context`: `EvidenceContext`.
- Validation rules:
  - `risk_level`, `risk_conditions`, `risk_notes`, `evidence_context`, and `freshness` are required.
  - The risk plan must clearly distinguish advisory framing from deterministic risk engine outputs.
  - Stop-loss language must not be conflated with final gate state.
  - If capital-at-risk is present, it must be traceable to the evidence context or an explicit derived assumption.
- Boundary notes:
  - This object is the risk-facing plan, not the definitive risk contract.
  - It should align conceptually with `RiskConfig`, `SizeInfo`, and `RiskMetrics` without copying those objects verbatim.

InvalidationPlan
- Purpose: capture the conditions that break the thesis or force the recommendation to be reconsidered.
- Proposed fields:
  - `invalidation_level`: qualitative label or state for how severe the invalidation is.
  - `invalidation_conditions`: list of explicit break conditions.
  - `invalidation_triggers`: list of observable triggers that would satisfy those conditions.
  - `invalidation_message`: short human-readable summary of the breakage logic.
  - `reassessment_needed`: boolean.
  - `freshness`: `FreshnessEnvelope`.
  - `evidence_context`: `EvidenceContext`.
- Validation rules:
  - `invalidation_conditions`, `invalidation_message`, `reassessment_needed`, `evidence_context`, and `freshness` are required.
  - Invalidation is advisory in this family; it signals breakage, but it does not itself replace the symbolic verdict.
  - Conditions should be observable and evidence-based rather than speculative.
  - If the invalidation is already triggered, that should be explicit in the wording and not hidden.
- Boundary notes:
  - This object should make thesis breakage easy to trace.
  - It will likely feed later monitoring work, but it does not become an alert family in this step.

MonitoringPlan
- Purpose: capture the structured post-entry conditions that should be watched after the case is active.
- Proposed fields:
  - `monitoring_level`: qualitative label such as `light`, `standard`, `intense`.
  - `monitoring_conditions`: list of conditions to watch post-entry.
  - `review_frequency`: optional text or interval descriptor.
  - `alert_thresholds`: optional list of threshold descriptions, if the threshold is explicitly derived from the evidence.
  - `watch_notes`: short explanatory summary of what should be monitored and why.
  - `freshness`: `FreshnessEnvelope`.
  - `evidence_context`: `EvidenceContext`.
- Validation rules:
  - `monitoring_level`, `monitoring_conditions`, `watch_notes`, `evidence_context`, and `freshness` are required.
  - The monitoring plan must remain a planning surface and must not become the alert event stream itself.
  - Alert thresholds, if present, must be explicit and traceable.
  - Monitoring conditions should be aligned to thesis-breakage, risk, and evidence updates rather than generic watchlist commentary.
- Boundary notes:
  - This object is the planning precursor to later monitoring/watchtower payloads.
  - It should be renderable in the UI as a plan, not as an executed alert.

Family relation and duplication rules
- `TickerAnalysisPackage` owns the overall analysis context and the ordered recommendation blocks.
- `RecommendationBlock` owns one advisory posture and can carry one or more of the plan objects.
- `EntryPlan`, `RiskPlan`, `InvalidationPlan`, and `MonitoringPlan` should avoid duplicating the same semantic fact unless the duplication is deliberate and tagged by block type.
- `EvidenceContext` and `FreshnessEnvelope` are reused at every level of the family to avoid a second freshness system.
- The symbolic verdict remains separate; this family describes the case around the verdict, not the verdict itself.

Legacy vocabulary alignment for recommendation planning
- `TickerAnalysisPackage` is conceptually broader than `DecisionInputs` in `backend/schemas/decision_models.py`; it packages the analysis context, not just the engine inputs.
- `RecommendationBlock` is conceptually adjacent to `DecisionItem` and `ExplanationItem`, but it is not a verdict token and must not impersonate one.
- `EntryPlan` and `RiskPlan` align loosely with `SizeInfo`, `RiskMetrics`, and `RiskConfig` from the legacy stack, but they are advisory planning objects rather than engine outputs.
- `InvalidationPlan` and `MonitoringPlan` have no exact legacy analogs in the current backend stack; they are new planning surfaces that later code will need to introduce cleanly.
- The older request/response models in `backend/schemas/models_requests.py` and `backend/schemas/models_responses.py` can serve as naming anchors for request/response structure, but not as direct owners of these richer plan objects.

3.1.3 Options analysis family, concrete design

This family is advisory-first and remains separate from the dashboard transport layer. It can inform later recommendations, but it does not produce a final trade decision by itself.

OptionsProfile
- Purpose: top-level options-analysis container for one ticker and one options context.
- Proposed fields:
  - `profile_id`: stable options-analysis identifier.
  - `ticker`: underlying ticker symbol.
  - `as_of_date`: analysis date.
  - `generated_at`: UTC datetime when the profile was assembled.
  - `symbolic_verdict_ref`: reference to the current symbolic verdict or analysis state.
  - `evidence_context`: `EvidenceContext`.
  - `freshness`: `FreshnessEnvelope`.
  - `contract_snapshots`: ordered list of `OptionContractSnapshot` objects.
  - `profile_summary`: short human-readable summary of the options case.
  - `thesis_fit`: optional advisory label describing whether the structure fits the broader case.
  - `contract_count`: optional integer count of included contracts.
  - `notes`: optional short advisory note.
- Validation rules:
  - `profile_id`, `ticker`, `as_of_date`, `generated_at`, `symbolic_verdict_ref`, `evidence_context`, and `freshness` are required.
  - The profile must not invent an options recommendation or override the symbolic verdict.
  - If `thesis_fit` is present, it must be advisory and not treated as a deterministic gate.
  - Evidence freshness must remain explicit across the whole profile.
- Boundary notes:
  - This is the parent object for options analysis.
  - It should be reusable by later recommendation and dashboard rendering layers, but it remains analysis-domain first.

OptionContractSnapshot
- Purpose: capture one option contract or contract candidate in structured form.
- Proposed fields:
  - `contract_id`: stable contract identifier or symbol.
  - `underlying_ticker`: ticker for the underlying asset.
  - `contract_type`: enum with values `call` and `put`.
  - `expiry`: contract expiry date.
  - `strike`: strike price.
  - `exchange`: optional exchange or venue label.
  - `currency`: optional currency code.
  - `last_price`: optional last traded premium.
  - `bid`: optional best bid.
  - `ask`: optional best ask.
  - `mid_price`: optional midpoint premium.
  - `intrinsic_value`: optional calculated intrinsic value if explicitly provided.
  - `extrinsic_value`: optional calculated extrinsic value if explicitly provided.
  - `open_interest`: optional open-interest count.
  - `volume`: optional volume count.
  - `contract_size`: optional contract size or multiplier.
  - `tradeable`: boolean or optional indicator that the contract is considered usable in analysis.
  - `freshness`: `FreshnessEnvelope`.
  - `evidence_context`: `EvidenceContext`.
- Validation rules:
  - `contract_id`, `underlying_ticker`, `contract_type`, `expiry`, `strike`, `evidence_context`, and `freshness` are required.
  - Contract pricing fields are optional unless explicitly sourced; they must not be invented.
  - Tradeability must be advisory unless a later deterministic gate explicitly consumes it.
  - The snapshot should represent one contract at one analysis time, not a rolling market feed.
- Boundary notes:
  - This object is the contract-level building block for options analysis.
  - It should align conceptually with `QuoteSnapshot` and `PriceBar` in the provider stack, but it is an analysis snapshot rather than a raw market-data transport shape.

GreeksSnapshot
- Purpose: capture the greek and implied-volatility view for one contract or one options profile.
- Proposed fields:
  - `snapshot_id`: stable identifier for the greek snapshot.
  - `contract_id`: reference to the option contract.
  - `underlying_ticker`: underlying ticker symbol.
  - `implied_volatility`: optional numeric IV value.
  - `delta`: optional numeric delta.
  - `gamma`: optional numeric gamma.
  - `theta`: optional numeric theta.
  - `vega`: optional numeric vega.
  - `rho`: optional numeric rho.
  - `iv_rank`: optional qualitative or numeric IV rank.
  - `iv_percentile`: optional qualitative or numeric IV percentile.
  - `directional_bias`: optional advisory label derived from the greeks, if explicitly grounded.
  - `sensitivity_notes`: short human-readable interpretation notes.
  - `freshness`: `FreshnessEnvelope`.
  - `evidence_context`: `EvidenceContext`.
- Validation rules:
  - `snapshot_id`, `contract_id`, `underlying_ticker`, `evidence_context`, and `freshness` are required.
  - Greek values must be optional unless explicitly sourced; the model must not invent them.
  - `directional_bias` is advisory and must not be elevated into a policy rule.
  - If IV rank or percentile is used, the calculation basis should be explained in the evidence context or notes.
- Boundary notes:
  - This object isolates sensitivity analysis from contract selection and liquidity.
  - It should remain compatible with later options-analysis reasoning, but it is not a final gate.

LiquiditySnapshot
- Purpose: capture marketability and tradability signals for an options contract.
- Proposed fields:
  - `snapshot_id`: stable identifier for the liquidity snapshot.
  - `contract_id`: reference to the option contract.
  - `underlying_ticker`: underlying ticker symbol.
  - `bid_size`: optional best-bid size.
  - `ask_size`: optional best-ask size.
  - `spread`: optional absolute bid/ask spread.
  - `spread_pct`: optional spread as a percentage of midpoint or premium.
  - `open_interest`: optional open-interest count.
  - `volume`: optional volume count.
  - `average_daily_volume`: optional rolling average volume if explicitly sourced.
  - `liquidity_label`: optional advisory label such as `thin`, `adequate`, `deep`.
  - `freshness`: `FreshnessEnvelope`.
  - `evidence_context`: `EvidenceContext`.
- Validation rules:
  - `snapshot_id`, `contract_id`, `underlying_ticker`, `evidence_context`, and `freshness` are required.
  - Liquidity labels must be advisory and traceable; they must not be synthesized from UI state.
  - Spread and size fields must be explicit if used and cannot be assumed.
  - A contract may be option-available yet still poorly liquid; that distinction must remain visible.
- Boundary notes:
  - This object is separate from contract pricing and greek sensitivity.
  - It should be reusable by later recommendation logic and monitoring, but it remains an analysis snapshot.

SpreadQualitySnapshot
- Purpose: capture how clean or poor the option spread is for analysis purposes.
- Proposed fields:
  - `snapshot_id`: stable identifier for the spread-quality snapshot.
  - `contract_id`: reference to the option contract.
  - `underlying_ticker`: underlying ticker symbol.
  - `bid`: optional best bid.
  - `ask`: optional best ask.
  - `mid_price`: optional midpoint premium.
  - `spread`: optional absolute spread.
  - `spread_pct`: optional spread as a percentage of midpoint or premium.
  - `slippage_risk`: optional advisory label or short descriptor.
  - `quality_label`: optional label such as `tight`, `acceptable`, `wide`, `unusable`.
  - `quality_notes`: short advisory explanation of the spread quality.
  - `freshness`: `FreshnessEnvelope`.
  - `evidence_context`: `EvidenceContext`.
- Validation rules:
  - `snapshot_id`, `contract_id`, `underlying_ticker`, `evidence_context`, and `freshness` are required.
  - Quality labels must be advisory and based on the explicit spread evidence.
  - A wide spread must remain visible as a cautionary factor rather than being hidden by a positive thesis.
  - Spread quality must not be conflated with liquidity, though the two may overlap.
- Boundary notes:
  - This object is distinct from liquidity and greek sensitivity.
  - It is a structured analysis object, not a transport-only dashboard label.

Family relation and duplication rules
- `OptionsProfile` owns the overall options context and the ordered contract snapshots.
- `OptionContractSnapshot` owns one contract-level analysis record.
- `GreeksSnapshot`, `LiquiditySnapshot`, and `SpreadQualitySnapshot` should describe different dimensions of the same option context without duplicating the exact same field unless the dimension requires it.
- `EvidenceContext` and `FreshnessEnvelope` are reused throughout the family to avoid a second options-specific provenance system.
- The symbolic verdict remains separate; this family describes options structure around the verdict, not the verdict itself.

Legacy vocabulary alignment for options planning
- `OptionsProfile` has no exact legacy analog in the current `backend/schemas/` stack; it is a new analysis container that will need a dedicated schema later.
- `OptionContractSnapshot` is conceptually similar to `QuoteSnapshot` and `PriceBar` in the provider layer because it captures a market snapshot, but it is options-specific rather than equity-price-specific.
- `GreeksSnapshot` has no direct legacy equivalent in the current backend models and should not be forced into `TechnicalIndicatorsItem`.
- `LiquiditySnapshot` and `SpreadQualitySnapshot` are new analysis objects; they are related to existing `SizeInfo` and `RiskMetrics` concepts only in the sense that they inform risk, not because they are already represented there.
- The older request/response classes in `backend/schemas/models_requests.py` and `backend/schemas/models_responses.py` can anchor future request/response wrappers, but they do not supply the right structure for these options-specific analysis objects.

3.1.4 Monitoring / watchtower family, concrete design

This family is advisory-first and post-entry focused. It describes what should be watched after a case is active, but it does not define alert transport or auto-action behavior.

PostEntryContext
- Purpose: capture the active-case context needed to evaluate post-entry monitoring.
- Proposed fields:
  - `context_id`: stable identifier for the post-entry context.
  - `analysis_id`: reference to the originating analysis package or recommendation block.
  - `ticker`: ticker under watch.
  - `symbolic_verdict_ref`: reference to the current symbolic verdict or verdict state.
  - `entry_timestamp`: UTC datetime when the case became active.
  - `entry_price`: optional reference entry price.
  - `position_side`: optional enum or string such as `long`, `short`, or `flat`.
  - `planned_hold_time`: optional holding-window descriptor.
  - `capital_at_risk`: optional numeric reference.
  - `evidence_context`: `EvidenceContext`.
  - `freshness`: `FreshnessEnvelope`.
- Validation rules:
  - `context_id`, `analysis_id`, `ticker`, `symbolic_verdict_ref`, `entry_timestamp`, `evidence_context`, and `freshness` are required.
  - The context must represent an already-active or actively watched case, not a hypothetical pre-entry idea.
  - Entry and risk references should be advisory or explicit derived inputs, not hidden policy.
  - If `position_side` is omitted, the context should still clearly indicate whether monitoring is active or pending.
- Boundary notes:
  - This is the parent object for the monitoring family.
  - It should align conceptually with the recommendation family and later dashboard rendering, but it remains a post-entry analysis context.

MonitoringCondition
- Purpose: define one observable condition that the watchtower should track.
- Proposed fields:
  - `condition_id`: stable identifier for the condition.
  - `condition_type`: enum with values such as `thesis_breakage`, `stop_loss`, `volatility_change`, `macro_shock`, `options_risk_change`, or `other_observable_condition`.
  - `condition_name`: short canonical label.
  - `condition_description`: human-readable explanation of the condition.
  - `trigger_basis`: description of the observable basis for the condition.
  - `threshold`: optional numeric or descriptive threshold.
  - `comparison_operator`: optional descriptor such as `>=`, `<=`, `crosses_above`, `crosses_below`, or `within`.
  - `severity_hint`: optional advisory label such as `light`, `moderate`, `high`.
  - `freshness`: `FreshnessEnvelope`.
  - `evidence_context`: `EvidenceContext`.
- Validation rules:
  - `condition_id`, `condition_type`, `condition_name`, `condition_description`, `trigger_basis`, `evidence_context`, and `freshness` are required.
  - Conditions must be observable and evidence-based; they should not be vague commentary.
  - Conditions may mention alert-like outcomes by name only, but they must not define alert transport.
  - A condition may be advisory or deterministic later, but this family remains advisory until a later gate explicitly consumes it.
- Boundary notes:
  - This object is the atomic monitoring rule for the family.
  - It should be reusable by future monitoring state and later transport surfaces.

MonitoringState
- Purpose: aggregate the current monitoring status for an active case.
- Proposed fields:
  - `state_id`: stable identifier for the state record.
  - `context_id`: link to the `PostEntryContext`.
  - `ticker`: ticker under watch.
  - `symbolic_verdict_ref`: reference to the current symbolic verdict or verdict state.
  - `status`: enum with values such as `watching`, `stable`, `watchlist_warning`, `thesis_at_risk`, `review_needed`.
  - `last_checked_at`: UTC datetime.
  - `active_condition_ids`: list of monitoring condition identifiers currently active.
  - `resolved_condition_ids`: list of condition identifiers that were previously active and are now resolved.
  - `current_conditions`: ordered list of `MonitoringCondition` objects.
  - `state_summary`: short human-readable summary of the monitoring posture.
  - `freshness`: `FreshnessEnvelope`.
  - `evidence_context`: `EvidenceContext`.
- Validation rules:
  - `state_id`, `context_id`, `ticker`, `symbolic_verdict_ref`, `status`, `last_checked_at`, `current_conditions`, `evidence_context`, and `freshness` are required.
  - MonitoringState must not be confused with a transport event stream; it is the backend-owned state of the watchtower.
  - A state can signal caution or review need, but it must not auto-close or mutate the final verdict.
  - If the state depends on delayed or stale evidence, that must remain explicit in the freshness envelope.
- Boundary notes:
  - This object aggregates the monitoring conditions into one current-state view.
  - It is the main analysis object the UI can render later, but it remains separate from transport mechanics.

ThesisBreakageEvent
- Purpose: capture a specific thesis-breakage occurrence observed by the monitoring family.
- Proposed fields:
  - `event_id`: stable identifier for the event.
  - `state_id`: link to the `MonitoringState` that observed the breakage.
  - `context_id`: link to the `PostEntryContext`.
  - `ticker`: ticker under watch.
  - `symbolic_verdict_ref`: reference to the current symbolic verdict or verdict state.
  - `condition_id`: identifier of the monitoring condition that triggered the breakage.
  - `breakage_type`: enum or string aligned to the triggering condition type.
  - `observed_at`: UTC datetime.
  - `evidence_context`: `EvidenceContext`.
  - `freshness`: `FreshnessEnvelope`.
  - `summary`: short human-readable description of the breakage.
  - `requires_reassessment`: boolean.
- Validation rules:
  - `event_id`, `state_id`, `context_id`, `ticker`, `symbolic_verdict_ref`, `condition_id`, `breakage_type`, `observed_at`, `evidence_context`, and `freshness` are required.
  - The event records a thesis breakage observation; it does not itself emit transport or auto-action.
  - `requires_reassessment` should be explicit when breakage is severe enough to require review.
  - The event must remain grounded in observed evidence, not inferred from UI state.
- Boundary notes:
  - This object is the terminal monitoring-domain record for the family.
  - It should be suitable for later consumption by deterministic gating or dashboard transport, but that is outside this planning step.

Family relation and duplication rules
- `PostEntryContext` owns the active-case metadata and links the monitoring family back to the original analysis.
- `MonitoringCondition` owns one observable watch condition.
- `MonitoringState` aggregates the active conditions into a backend-owned current state.
- `ThesisBreakageEvent` records one observed breakage against a state and condition.
- `EvidenceContext` and `FreshnessEnvelope` are reused throughout the family to avoid a second monitoring-specific freshness or provenance system.
- The symbolic verdict remains separate; this family describes what is being watched around the verdict, not the verdict itself.

Legacy vocabulary alignment for monitoring planning
- `PostEntryContext` is conceptually adjacent to `PipelineResponse` and `AuditEntry` in the legacy stack because it anchors an analysis lifecycle, but it is more specific to post-entry monitoring.
- `MonitoringState` has no exact legacy equivalent in the current backend models; it should not be forced into `DecisionItem` or `EventFlagsItem`.
- `MonitoringCondition` is conceptually similar to the condition logic behind `EventFlagsItem` and risk thresholds, but it is a richer watch condition object and should remain distinct.
- `ThesisBreakageEvent` is conceptually adjacent to `ErrorItem` and `AuditEntry` as an observed state change, but it is not an error object and should not be flattened into generic error handling.
- The older request/response models in `backend/schemas/models_requests.py` and `backend/schemas/models_responses.py` can help with eventual wrappers, but they do not supply the needed monitoring shape.

3.1.5 Alert family, concrete design

This family is advisory-to-operational handoff metadata. It is separate from monitoring state and separate from any notification transport or provider-specific delivery mechanism.

AlertEvent
- Purpose: represent one actionable alert record derived from a monitoring or analysis condition.
- Proposed fields:
  - `alert_id`: stable alert identifier.
  - `ticker`: ticker symbol associated with the alert.
  - `symbolic_verdict_ref`: reference to the current symbolic verdict or verdict state.
  - `source_kind`: enum or string indicating where the alert originated, such as `monitoring_state`, `thesis_breakage_event`, `recommendation_block`, or `other_deterministic_source`.
  - `source_id`: identifier of the source record, such as a monitoring state, thesis-breakage event, or recommendation block.
  - `alert_type`: canonical label such as `thesis_breakage`, `stop_loss_breach`, `volatility_change`, `macro_shock`, `options_risk_change`, or `watch_condition_triggered`.
  - `severity`: `AlertSeverity`.
  - `trigger`: `AlertTrigger`.
  - `routing_hint`: optional `AlertRoutingHint`.
  - `summary`: short human-readable alert summary.
  - `observed_at`: UTC datetime.
  - `evidence_context`: `EvidenceContext`.
  - `freshness`: `FreshnessEnvelope`.
  - `requires_review`: boolean.
- Validation rules:
  - `alert_id`, `ticker`, `symbolic_verdict_ref`, `source_kind`, `source_id`, `alert_type`, `severity`, `trigger`, `summary`, `observed_at`, `evidence_context`, and `freshness` are required.
  - The alert is a record of an actionable condition, not a transport delivery artifact.
  - The alert must remain grounded in an explicit source record and observed evidence.
  - `requires_review` should be explicit when the alert is significant enough to merit escalation.
- Boundary notes:
  - This object is the top-level alert domain record.
  - It may later be consumed by transport or routing layers, but those layers are outside this planning step.

AlertSeverity
- Purpose: classify how urgent or important an alert is without implying a provider or transport path.
- Proposed fields:
  - `severity_code`: enum with values such as `info`, `low`, `medium`, `high`, `critical`.
  - `severity_label`: human-readable label.
  - `severity_rank`: optional numeric ordering value if needed for sorting.
  - `escalation_needed`: boolean.
  - `freshness`: `FreshnessEnvelope`.
- Validation rules:
  - `severity_code` and `severity_label` are required.
  - Severity is a classification of urgency, not a delivery instruction.
  - The rank, if present, must remain advisory and stable.
  - Escalation need may be expressed, but it must not encode where or how delivery occurs.
- Boundary notes:
  - This object is reusable by later alert streams and dashboard views, but it remains a severity classification.
  - It does not replace monitoring state or thesis breakage records.

AlertTrigger
- Purpose: describe the specific evidence or condition that caused an alert to be emitted.
- Proposed fields:
  - `trigger_id`: stable trigger identifier.
  - `condition_id`: identifier of the originating monitoring condition or related condition.
  - `trigger_type`: canonical label such as `threshold_breach`, `condition_entered`, `condition_crossed`, `state_changed`, `manual_review_required`, or `other_trigger`.
  - `trigger_basis`: short description of the observed basis.
  - `trigger_value`: optional observed value.
  - `threshold`: optional threshold reference.
  - `comparison_operator`: optional descriptor such as `>=`, `<=`, `crosses_above`, `crosses_below`, or `within`.
  - `evidence_context`: `EvidenceContext`.
  - `freshness`: `FreshnessEnvelope`.
- Validation rules:
  - `trigger_id`, `condition_id`, `trigger_type`, `trigger_basis`, `evidence_context`, and `freshness` are required.
  - Triggers must reference an observed condition or evidence basis rather than a guessed outcome.
  - The trigger should be sufficient to explain why the alert exists, but it must not define transport behavior.
  - If a threshold is used, it must be explicit and traceable.
- Boundary notes:
  - This object is the bridge between monitoring evidence and alert classification.
  - It should remain distinct from the monitoring condition itself, even if the same evidence drives both.

AlertRoutingHint
- Purpose: provide non-provider-specific guidance for how an alert should be treated by later delivery layers.
- Proposed fields:
  - `hint_id`: stable routing-hint identifier.
  - `priority`: optional numeric or ordinal priority.
  - `audience`: optional label such as `operator`, `analyst`, `review_queue`, or `system`.
  - `urgency`: optional label such as `immediate`, `soon`, `deferred`.
  - `dedupe_key`: optional key for grouping repeated alerts.
  - `suppression_hint`: optional note indicating whether the alert should be suppressed, grouped, or deferred.
  - `display_hint`: optional short UI-oriented note.
  - `freshness`: `FreshnessEnvelope`.
- Validation rules:
  - `hint_id` is required.
  - Routing hints are advisory metadata only; they must not encode a notification provider, channel, or transport implementation.
  - If present, priority and urgency must be stable and easy to interpret.
  - Suppression or grouping hints must not hide the alert from the authoritative record.
- Boundary notes:
  - This object is the soft routing layer between alert creation and any later delivery mechanism.
  - It intentionally avoids provider-specific channel semantics.

Family relation and duplication rules
- `AlertEvent` owns the top-level alert record.
- `AlertSeverity` classifies urgency.
- `AlertTrigger` explains the evidence or condition that caused the alert.
- `AlertRoutingHint` guides later delivery layers without defining transport.
- `EvidenceContext` and `FreshnessEnvelope` are reused where they genuinely belong so that evidence and recency remain explicit.
- Alerts may reference monitoring artifacts such as `MonitoringState` or `ThesisBreakageEvent`, but they are not the same object and should not be collapsed into one another.

Legacy vocabulary alignment for alert planning
- `AlertEvent` is conceptually adjacent to `ErrorItem` and `AuditEntry` in the legacy stack because it records an important state change, but it is not an error object and should not be flattened into error handling.
- `AlertSeverity` has no exact legacy analog in the current backend stack and should remain its own classification object.
- `AlertTrigger` is conceptually similar to condition and threshold logic in `EventFlagsItem` and `MonitoringCondition`, but it is specifically the alert-side trigger record.
- `AlertRoutingHint` has no direct legacy equivalent and should not be forced into `ResponseStatus`, `RequestMeta`, or any generic request wrapper.
- The older request/response models in `backend/schemas/models_requests.py` and `backend/schemas/models_responses.py` can help with eventual envelopes, but they do not provide the right alert shape.

3.1 Planned contract map

Core domain contracts: backend-owned, deterministic, and authoritative
- Follow-up interaction domain: `FollowUpQuestion`, `FollowUpAnswer`, `FollowUpTarget`, `EvidenceContext`, `FreshnessEnvelope`.
- Structured analysis and recommendation domain: `TickerAnalysisPackage`, `RecommendationBlock`, `EntryPlan`, `RiskPlan`, `InvalidationPlan`, `MonitoringPlan`.
- Options analysis domain: `OptionsProfile`, `OptionContractSnapshot`, `GreeksSnapshot`, `LiquiditySnapshot`, `SpreadQualitySnapshot`.
- Monitoring domain: `MonitoringState`, `MonitoringCondition`, `PostEntryContext`, `ThesisBreakageEvent`.
- Alert domain: `AlertEvent`, `AlertSeverity`, `AlertTrigger`, `AlertRoutingHint`.

UI/dashboard transport and view contracts: render-only projections of the core domain
- Follow-up view: `FollowUpThreadView`, `FollowUpAnswerCard`, `FollowUpContextDrawer`.
- Structured analysis view: `AnalysisSummaryCard`, `VerdictRationalePanel`, `RecommendationBlockView`.
- Options view: `OptionsPanelView`, `OptionsComparisonRow`, `GreeksMiniTable`.
- Monitoring view: `MonitoringPanelView`, `AlertTimelineItem`, `WatchStatusBadge`.
- Alert view: `AlertBannerView`, `AlertDrawerItem`, `AlertStreamEvent`.

Boundary rule
- Core domain contracts are the source of truth and must preserve the symbolic verdict, explicit timestamps, and freshness labels.
- UI/dashboard transport contracts are derived views only; they may present, sort, filter, or group data, but they must not compute verdicts, risk gates, or policy.

Freshness and timestamp requirements
- Every future payload family should carry explicit evidence timestamps and provenance timestamps where available.
- Freshness labels must be explicit and stable across the stack: `real_time`, `delayed`, `stale`, and `snapshot`.
- A UI surface may be live while the underlying evidence remains delayed or stale; transport liveness must not be confused with evidence freshness.

Legacy-stack alignment note
- If the older `backend/schemas/` stack remains active during migration, align these planned families to the existing `RequestMeta`, `ResponseStatus`, `ErrorItem`, `DecisionInputs`, and `DecisionItem` patterns instead of inventing a second parallel vocabulary.

4. Shared types (JSON-like)

- TickerMetadata:
  { "ticker": str, "exchange": str, "sector": str, "market_cap": number, "lot_size": int, "tradable": bool }

- PriceBar:
  { "date": "YYYY-MM-DD", "open": number, "high": number, "low": number, "close": number, "volume": int }

- SizeInfo:
  { "allowed_qty": int, "notional": number, "risk_amount": number, "sizing_model_used": str, "stop_distance": number|null }

- RiskMetrics:
  { "portfolio_var": number, "portfolio_variance": number, "volatility": number }

- DecisionToken: enum ["BUY_CANDIDATE","SELL_EXIT_CANDIDATE","HOLD","NO_TRADE"]

5. Error codes (canonical)
- INSUFFICIENT_HISTORY: price history too short for indicators
- UNIVERSE_EMPTY: no tradable tickers after filters
- MISSING_DATA: required fundamental data missing
- RISK_ERROR: general risk computation failure
- MARGIN_EXCEEDED: computed margin / leverage > allowed
- POLICY_VIOLATION: policy-config disallows action
- INTERNAL_ERROR: unexpected server error

Each error object: { "code": str, "message": str, "details": object|null }

6. Decision payload schema (must enforce token restriction)
Decision response per ticker:
{
  "ticker": "AAPL",
  "decision": "BUY_CANDIDATE",  // MUST be one of DecisionToken
  "size_info": SizeInfo|null,
  "reason_codes": ["MA_CROSS","FUND_PASS","RISK_OK"],
  "applied_rules": ["R0004","R0006"]
}

Rules:
- `decision` must be exactly one of the four tokens.
- If `size_info` is null, `decision` must not be `BUY_CANDIDATE` (fail-safe).
- Missing inputs must produce `NO_TRADE`.

7. Audit log schema
Each decision run produces an audit event:
{
  "run_id":"UUID",
  "request_id":"UUID",
  "timestamp":"ISO",
  "as_of_date":"YYYY-MM-DD",
  "engine_versions": {"universe":"v1","technical":"v1","risk":"v1","decision":"v1"},
  "inputs": { /* summarized inputs, avoid sensitive raw data */ },
  "decisions": { "AAPL": { /* decision payload */ } },
  "errors": [],
  "duration_ms": 1234
}

Audit entries must be append-only and immutable.

8. Source-link schema for explanations
- source_link = { "rule_id": "R0006", "file": "docs/varsity-extraction/module-09-risk-management-trading-psychology.md", "line_range": null }
- `line_range` is optional; when exact line mapping not available, set to null and include a `note` field: {"note":"line-level traceability not available"}.

9. Contract invariants (safety)
 - All decision outputs must be in DecisionToken set.
 - Any missing or invalid input causes a safe failure: decision = `NO_TRADE` and an error code emitted.
 - `BUY_CANDIDATE` requires non-null `size_info.allowed_qty > 0`.
 - Engines must propagate `errors` array; an error in a required upstream engine forces `NO_TRADE`.
 - Risk engine must never return `allowed_qty` that violates `max_position_size_pct` or `max_leverage`; if computation would, return `allowed_qty=0` and error `MARGIN_EXCEEDED`.
 - Explanation outputs must attempt to include at least one `source_link` per applied rule; if unavailable, emit a placeholder `source_link` with `line_range=null` and a note indicating line-level traceability is not available.
 - Follow-up answers must not alter the symbolic verdict; they may only summarize, cite, or rephrase the approved verdict and evidence context.
 - Freshness labels must be explicit anywhere evidence or market-state recency is surfaced.

Planned schema surfaces likely to change later
- Core follow-up payload families and their evidence envelopes.
- Structured recommendation payloads for entry, risk, invalidation, and monitoring.
- Options profile payloads and their greeks/liquidity substructures.
- Monitoring state and alert payloads for post-entry surveillance.
- Dashboard transport/view models that render the above without recomputing verdicts.
- Shared freshness/timestamp helpers that standardize explicit labeling across payload families.

Likely future code files that will need changes later
- `trading_os_v1/trading_os_v1/providers/schemas.py`
- `trading_os_v1/trading_os_v1/providers/dashboard_contracts.py`
- `trading_os_v1/trading_os_v1/app.py`
- `backend/schemas/shared.py`
- `backend/schemas/decision_models.py`
- `backend/schemas/models_requests.py`
- `backend/schemas/models_responses.py`

10. Gherkin acceptance criteria for contract validation
- Scenario: Decision service rejects missing price history
  Given `technical_signals` for AAPL computed with less than required history
  When Decision engine receives request referencing that signal
  Then response for AAPL has `decision` == "NO_TRADE" and errors contains `INSUFFICIENT_HISTORY`

- Scenario: Decision service enforces token constraints
  Given inputs that would otherwise produce an unknown token
  When Decision engine responds
  Then `decision` value is one of ["BUY_CANDIDATE","SELL_EXIT_CANDIDATE","HOLD","NO_TRADE"]

- Scenario: Buy requires size_info
  Given Decision engine outputs `BUY_CANDIDATE` for AAPL
  Then `size_info` is present and `allowed_qty` > 0

- Scenario: Risk over-limit forces NO_TRADE
  Given computed margin exceeds `max_leverage`
  When Risk engine responds
  Then Decision response `decision` == "NO_TRADE" and error `MARGIN_EXCEEDED` is present

- Scenario: Explanations are source-linked
  Given a decision applying rule R0006
  When Explanation engine responds
  Then `explanations.AAPL.source_links` contains an entry with `rule_id` == "R0006" and `file` set to a path under `docs/varsity-extraction/`

End of contracts.
