import importlib
from datetime import datetime, timezone

from fastapi.testclient import TestClient
import pytest
from trading_os_v1.app import app
from trading_os_v1.providers.schemas import ProviderMeta, QuoteSnapshot


app_module = importlib.import_module("trading_os_v1.app")


class FakeLiveQuoteAdapter:
    async def stream_quote_watch(self, symbols):
        symbol = list(symbols)[0]
        yield app_module.QuoteWatchFrame(
            symbol=symbol,
            feed_status="reconnecting",
            quote=None,
            last_successful_update_at=None,
            last_error="socket dropped",
            reconnect_attempts=1,
            reconnect_backoff_seconds=0.5,
        )
        yield app_module.QuoteWatchFrame(
            symbol=symbol,
            feed_status="live",
            quote=QuoteSnapshot(
                symbol=symbol,
                as_of=datetime(2024, 1, 15, 15, 31, tzinfo=timezone.utc),
                last=100.75,
                currency="USD",
                exchange="NASDAQ",
                meta=ProviderMeta(provider_name="twelvedata", source_id=symbol, received_at=datetime(2024, 1, 15, 15, 31, tzinfo=timezone.utc)),
            ),
            last_successful_update_at=datetime(2024, 1, 15, 15, 31, tzinfo=timezone.utc),
            reconnect_attempts=0,
            reconnect_backoff_seconds=None,
        )

    async def close(self):
        return None

@pytest.mark.asyncio
async def test_analyze_symbol_valid():
    client = TestClient(app)
    response = client.post("/analyze-symbol", json={"symbol": "AAPL"})
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "AAPL"
    assert "price" in data
    assert "decision" in data

@pytest.mark.asyncio
async def test_analyze_symbol_invalid_format():
    client = TestClient(app)
    response = client.post("/analyze-symbol", json={"symbol": "aapl"})
    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == "Invalid symbol format. Must be 3 uppercase letters."

@pytest.mark.asyncio
async def test_analyze_symbol_invalid_characters():
    client = TestClient(app)
    response = client.post("/analyze-symbol", json={"symbol": "AAPL!"})
    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == "Symbol contains invalid characters"

@pytest.mark.asyncio
async def test_analyze_symbol_server_error():
    client = TestClient(app)
    response = client.post("/analyze-symbol", json={"symbol": "ERROR"})
    assert response.status_code == 500
    data = response.json()
    assert data["detail"].startswith("Internal server error")


@pytest.mark.asyncio
async def test_dashboard_stream_emits_dashboard_snapshots():
    original_factory = app_module._build_quote_stream_adapter
    app_module._build_quote_stream_adapter = lambda: FakeLiveQuoteAdapter()
    client = TestClient(app)
    try:
        with client.stream("GET", "/dashboard/stream", headers={"Origin": "null"}) as response:
            assert response.status_code == 200
            assert response.headers["access-control-allow-origin"] == "*"
            body = "".join(chunk for chunk in response.iter_text())
    finally:
        app_module._build_quote_stream_adapter = original_factory

    assert "event: HealthSnapshot" in body
    assert "event: EvidenceTimelineSnapshot" in body
    assert "event: CompositionFallbackSnapshot" in body
    assert "event: CompositionOutcome" in body
    assert "event: QuoteWatchSnapshot" in body
    assert "event: DiagnosticsSnapshot" in body
    assert '"feed_status":"live"' in body
    assert '"feed_status":"reconnecting"' in body
    assert '"last_error":"socket dropped"' in body
    assert "provider_status_rows" in body
    assert "evidence_timeline_items" in body
    assert "composition_fallback_panel" in body
    assert "composition_outcome_detail_panel" in body
    assert "quote_watch_panel" in body
    assert "watchlist_items" in body
    assert "diagnostics_drawer" in body
    assert "Overview" in body
    assert '"operator_status":"Waiting for first live tick"' in body
    assert '"operator_status":"Live but stale"' in body
    assert '"recovery_copy":"Stream is warming up.' in body
    assert '"symbol":"MSFT"' in body
    assert '"symbol":"NVDA"' in body
    assert '"row_severity":"warning"' in body
    assert '"row_severity":"neutral"' in body
    assert '"transition_note":"' in body
    assert '"recovery_detail":"last success' in body