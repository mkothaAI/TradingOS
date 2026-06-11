# Twelve Data 20B WebSocket Plan

Scope: realtime quote/tick normalization only. No OHLC bar aggregation, no REST changes, no broker/execution work.

## Proposed adapter surface

- `TwelveDataRealtimeConfig`
- `TwelveDataRealtimeAdapter`

Recommended config shape:

- `api_key: str`
- `websocket_url: str = "wss://ws.twelvedata.com/v1/quotes/price?apikey=<KEY>"`
- `timeout_seconds: int = 30`
- `heartbeat_seconds: int = 15`
- `reconnect_initial_backoff_seconds: float = 0.25`
- `reconnect_max_backoff_seconds: float = 4.0`
- `reconnect_max_attempts: int | None = None`

Reuse existing repo contracts:

- realtime capability: `ProviderCapability.REALTIME_STREAM`
- normalized object: `QuoteSnapshot`
- health: `ProviderHealthManager`
- evidence: `EvidenceStore` / `LocalEvidenceStore`

## Lifecycle

- Open one shared websocket connection per adapter instance.
- Maintain a subscription set in memory so reconnect can replay active symbols.
- On initial connect, send subscribe actions for the requested symbols.
- On disconnect, reconnect with small capped exponential backoff and replay subscription state.
- Close cleanly by stopping the read loop, sending unsubscribe/reset if needed, and closing the socket.

## Control semantics

- `subscribe`: add symbols to the active set and send a subscribe control frame.
- `unsubscribe`: remove symbols from the active set and send an unsubscribe control frame.
- `reset`: clear or resync the active set and re-send the current subscription state after reconnect or stream reset.
- `heartbeat`: send a heartbeat frame on the configured interval while the stream is open.

## Normalization

- Normalize Twelve Data price messages into `QuoteSnapshot`.
- Treat bid/ask as optional; do not assume both fields are present.
- Preserve missing values as `None` when the websocket payload omits them.
- Do not synthesize OHLC bars in 20B.

## Evidence strategy

- Persist each inbound websocket frame as raw evidence for 20B.
- Persist one normalized record for each delivered `QuoteSnapshot`.
- Subscription status, reset, heartbeat, and malformed frames should also be captured as raw evidence when available.
- If write volume becomes problematic later, introduce short window batching behind the same contract; do not change the contract for 20B.

## Health strategy

- `record_success` when a quote frame is delivered successfully.
- `record_degraded` for malformed frames, reconnectable disconnects, heartbeat misses, or partial payloads.
- `record_failure` for terminal auth/entitlement failures and exhausted reconnect attempts.

## Error classification

- Terminal: auth failure, entitlement failure, unsupported websocket access, explicit deny/forbidden close codes.
- Reconnectable: network drop, timeout, temporary server disconnect, rate-limited stream.
- Degraded but continuing: malformed control frame, malformed price frame, missing optional fields.

## Live-test gating

- Require `TWELVEDATA_API_KEY`.
- Require an explicit websocket opt-in env var such as `TWELVEDATA_WEBSOCKET_LIVE=1`.
- Skip live tests unless both are set.
- Allow an optional websocket URL override only for local/manual verification.

## Non-goals for 20B

- No websocket OHLC aggregation.
- No REST bar changes.
- No new schema family.
- No symbol ranking or portfolio logic.
- No broker/execution integration.
- No assumption that bid/ask is always present.
