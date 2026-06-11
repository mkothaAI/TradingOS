# trading_os_v1 — V1 Implementation Plan

This document specifies a deterministic, test-first implementation sequence to build `trading_os_v1` using only local models and the approved specs and extracted Varsity sources. It references only:
- `docs/specs/v1-rules-spec.md`
- `docs/specs/v1-backend-contracts.md`
- `docs/engine-mapping/varsity-to-trading-os-v1.md`
- `docs/varsity-extraction/*.md`

1. Purpose
- This is the implementation sequence and developer guidance for `trading_os_v1`. It prescribes a minimal, safe build order that enforces fail-safe behavior (`NO_TRADE`), modular engines, and repeatable tests for a beginner using Cline.

2. Build principles
- Deterministic first: core logic must produce identical outputs for identical inputs.
- Test business logic before UI: unit and contract tests exist prior to UI or wrapper code.
- One engine at a time: fully implement, test, and freeze each engine before relying on it.
- Fail-safe to `NO_TRADE`: missing/invalid upstream input or engine error forces downstream `NO_TRADE`.
- No broker integration and no execution in V1.
- Local-model friendly: use local deterministic code and local artifacts; AI limited to explanation drafting and test-data generation (human-reviewed).
- Symbolic/verdict authority remains final; agents are advisory and must not become policy by prose.

3. Recommended project structure
- `backend/` — engine implementations, library code, and local runners.
- `frontend/` — minimal read-only UI prototypes (Phase 10 only).
- `tests/` — unit, contract, and integration tests organized by engine.
- `docs/` — specs, contracts, extracted Varsity sources, and design notes.
- `config/` — example configuration files (no secrets), canonical JSON contract examples.
- `scripts/` — helper scripts for data generation, exports, and local runs.

Folder guidance: place engine code in `backend/engines/<engine_name>/`, keep schema/contract models in `backend/schemas/` so they are reusable by implementations and tests, and store authoritative examples in `tests/fixtures/`.

4. Build phases (ordered, goals & outputs)
Phase 0: Repo setup and guardrails
- Goal: create repo baseline, virtual environment, formatting, and test runner.
- Outputs: `README`, `requirements.txt` or `pyproject.toml`, `.gitignore`, `tests/` layout, minimal CI/CI-placeholder files.
- Tests: `pytest` runs an initial smoke test.
- Do NOT: implement engine logic.

Phase 1: Shared types and contract artifacts
- Goal: implement reusable schema/contract models that will be used by engines and tests.
- Outputs: `backend/schemas/` with JSON Schemas and/or Pydantic models (designed for reuse by implementations, not throwaway test-only artifacts), canonical example request/response fixtures in `tests/fixtures/contracts/`.
- Tests: contract validation tests that assert example requests/responses in `v1-backend-contracts.md` validate and invalid cases fail.
- Do NOT: wire engines to schemas yet.

Phase 2: Risk engine (foundation)
- Goal: implement numeric building blocks from `module-09`: daily returns, variance/covariance, portfolio variance, annualization (config-flagged), empirical VaR (configurable), ATR helper, and sizing-model scaffolding.
- Outputs: `backend/engines/risk/` with pure functions and a deterministic API.
- Dependencies: prefer pure Python for v1; only add `numpy`/`pandas` if clearly necessary and after approval.
- Tests: unit tests that reproduce hand-calculated examples from `docs/varsity-extraction/module-09-*` and contract tests for risk request/response shapes.
- Do NOT: enable Kelly as default, add solver/optimizer, or connect to Decision engine until tests pass.

Phase 3: Technical engine
- Goal: EOD indicators: ATR(14), simple MAs, MA-cross detection (explicitly marked v1 design interpretation), candle classification, returns series.
- Outputs: `backend/engines/technical/` functions returning indicators and structured signals.
- Tests: unit tests with synthetic price bars verifying ATR, MA, and MA-cross detection; contract tests.
- Do NOT: implement visual heuristics or ML pattern recognition.

Phase 4: Decision engine (core pipeline)
- Goal: deterministic pipeline consuming Technical + optional Fundamental + Risk + Event flags and emitting `BUY_CANDIDATE` / `SELL_EXIT_CANDIDATE` / `HOLD` / `NO_TRADE` plus `size_info`.
- Outputs: `backend/engines/decision/` implementing Decision matrix from `v1-rules-spec.md`.
- Tests: golden-path unit tests, contract-level tests ensuring token constraints, and failure tests that missing inputs yield `NO_TRADE`.
- Do NOT: implement ranking beyond specified deterministic rules.

Phase 5: Explanation engine
- Goal: deterministic, source-linked explanation assembler that uses applied rules and data snapshot to produce `explanation_text` and `source_links`.
- Outputs: `backend/engines/explanation/` and tests verifying source-link fallback behavior.
- Do NOT: deploy AI-generated explanations to production without human review.

Phase 6: Universe engine
- Goal: deterministic universe filters and sector-cap mechanics per contracts.
- Outputs: `backend/engines/universe/` and tests verifying sector caps and truncation.
- Do NOT: auto-curate or include subjective filters.

Phase 7: Fundamental engine
- Goal: simple pass/fail fundamental checks using configured thresholds only (no defaults unless explicitly confirmed).
- Outputs: `backend/engines/fundamental/` and tests covering missing data flows.
- Do NOT: embed Varsity numeric defaults unless confirmed.

Phase 8: Event engine
- Goal: deterministic scheduled-event ingestion and advisory flagging with earnings-only blackout behavior.
- Inputs: authoritative `ticker_list`, structured `scheduled_events`, and `event_config` with partial blackout sides treated as 0 days.
- Outputs: `backend/engines/event/` plus tests for full ticker coverage, blackout windows, and deterministic ordering.
- Do NOT: treat example blackout numbers as production defaults or let non-earnings events trigger blackout.
- Response contract: `EventResponse` exposes `event_flags` once at the response level; `event_config` remains request-only.

Phase 9: Local orchestration runner (developer-only)
- Goal: add a thin local orchestration runner (CLI or script) that wires engines for local testing; no network API.
- Outputs: `scripts/local_run.py` or `backend/cli/` runner for end-to-end local tests.
- Tests: end-to-end integration tests using deterministic synthetic data verifying Decision + Explanation + Audit log creation.
- Do NOT: implement network APIs or broker integration in this phase.
- Runtime boundary note: partial live runtime feeds may be introduced only behind compatibility fallbacks. Claim "fully live" only when the raw orchestration input bundle is fully owned by genuine runtime sources for every required field on the recommendation path.

Phase 10: Minimal UI (read-only)
- Goal: simple read-only frontend that displays audit logs, decisions, and explanations from local-run outputs.
- Outputs: `frontend/` static pages and assets.
- Tests: manual acceptance and lightweight smoke tests.
- Do NOT: enable execution/order placement.

Future planning addenda (not v1 implementation)
- Interactive multi-agent follow-up shell: allow users to ask a specific agent or the synthesized verdict a traced question about a ticker analysis.
- Options analysis surface: render structured options vocabulary, greeks, liquidity, and spread quality as a first-class advisory view.
- Monitoring/watchtower surface: render post-entry thesis breakage, stop-loss, volatility, macro, and options-risk alerts.
- These addenda must preserve the final symbolic verdict and may not introduce broker/execution behavior.

5. Per-phase checklist (example pattern)
For each phase implement:
- Purpose (what this phase delivers)
- Files to create (clear list of paths)
- Dependencies (runtime/test deps)
- Tests required before moving on (unit + contract specifics)
- What NOT to do in that phase

6. Testing strategy
- Unit tests first: pure-function tests with deterministic inputs.
- Contract tests second: validate request/response shapes against `v1-backend-contracts.md` schemas.
- Integration tests later: local-run end-to-end scenarios using synthetic fixtures.
- Always use synthetic data before live data; create deterministic fixtures based on Varsity examples in `tests/fixtures/`.
- Blocking failures:
  - Any failing contract test blocks downstream integration.
  - Any decision test producing tokens outside the four allowed tokens blocks progress.
  - Risk calculations that cannot reproduce documented formula outputs block moving forward.

7. Prompting strategy for Cline
- Ask for one phase at a time. Example prompt: "Phase 2 — Risk engine: show test names and synthetic input arrays for returns/variance/covariance, then provide pure-function signatures; do not write files yet."
- Request a draft before writing files: require tests and function signatures to be shown and approved.
- Avoid architecture drift: require explicit approval to change folder layout, contract schemas, or Decision tokens; link changes to `v1-backend-contracts.md`.
- Use small incremental commits for each approved phase.
- For future planning work, keep follow-up, options, and monitoring vocabulary aligned with the canonical terms in `v1-rules-spec.md`.

8. Stop conditions
- Stop and ask for review when:
  - Implemented unit tests do not match the numerical examples in `docs/varsity-extraction/`.
  - A proposed change modifies `v1-rules-spec.md` or `v1-backend-contracts.md` without explicit approval.
  - Any change modifies Decision tokens or contract shapes.
- Changes requiring explicit approval:
  - Adopting example-derived numeric defaults (per-trade risk, VaR confidence, blackout days, annualization factor).
  - Introducing broker/execution integration or remote APIs.
  - Enabling Kelly as a default sizing strategy.

9. Exit criteria for v1
- All engines implemented with unit tests:
  - Risk: numeric building blocks + sizing models.
  - Technical: ATR, MA, MA-cross tests passing.
  - Decision: deterministic decision matrix tests passing.
  - Explanation: source-linked output tests passing.
  - Universe/Fundamental/Event: basic filters and flags with contract tests.
- All contract validation tests pass.
- Integration smoke tests: local-run end-to-end scenarios with synthetic data produce decisions and audit logs; decisions are one of the four tokens.
- Documentation: `v1-rules-spec.md`, `v1-backend-contracts.md`, `v1-implementation-plan.md` present in `docs/`.
- Audit: append-only audit log produced by local runs.
- No broker/execution artifacts present.

Notes for beginners
- Start with Phase 0 and Phase 1 to establish guardrails and reusable schemas. Then implement Phase 2 (Risk) and Phase 3 (Technical) before Decision.
- Keep each change small and test-first; map each numerical example from `docs/varsity-extraction/` to a unit test fixture.

End of plan.
