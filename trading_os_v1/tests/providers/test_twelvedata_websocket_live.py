from __future__ import annotations

import os

import pytest


def _resolve_live_websocket_config() -> tuple[str, str]:
    api_key = (os.getenv("TWELVEDATA_API_KEY") or "").strip()
    websocket_live = (os.getenv("TWELVEDATA_WEBSOCKET_LIVE") or "").strip()
    if not api_key:
        pytest.skip("TWELVEDATA_API_KEY is not set")
    if websocket_live != "1":
        pytest.skip("TWELVEDATA_WEBSOCKET_LIVE=1 is required for live websocket tests")
    return api_key, websocket_live


@pytest.mark.asyncio
async def test_twelvedata_live_websocket_quote_round_trip(tmp_path) -> None:
    _resolve_live_websocket_config()

    from trading_os_v1.providers.adapters.twelvedata import TwelveDataRealtimeAdapter, TwelveDataRealtimeConfig
    from trading_os_v1.providers.local_evidence_store import LocalEvidenceStore
    from trading_os_v1.providers.health import ProviderHealthManager

    config = TwelveDataRealtimeConfig(api_key=os.environ["TWELVEDATA_API_KEY"])
    evidence_store = LocalEvidenceStore(tmp_path)
    health_manager = ProviderHealthManager()

    adapter = TwelveDataRealtimeAdapter(config=config, evidence_store=evidence_store, health_manager=health_manager)

    stream = adapter.stream_quotes(["AAPL"])
    quote = await stream.__anext__()

    assert quote.symbol == "AAPL"
    assert quote.meta.provider_name == "twelvedata"
