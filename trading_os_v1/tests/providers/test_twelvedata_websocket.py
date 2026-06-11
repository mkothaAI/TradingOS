from __future__ import annotations

import asyncio
import importlib
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from trading_os_v1.providers.schemas import ProviderCapability, ProviderMeta, QuoteSnapshot


MODULE_PATH = "trading_os_v1.providers.adapters.twelvedata"


def _load_realtime_module():
    return importlib.import_module(MODULE_PATH)


def _load_realtime_symbols():
    module = _load_realtime_module()
    adapter_cls = getattr(module, "TwelveDataRealtimeAdapter")
    config_cls = getattr(module, "TwelveDataRealtimeConfig")
    return module, adapter_cls, config_cls


class FakeWebSocket:
    def __init__(self, inbound_messages: list[str]):
        self.inbound_messages = list(inbound_messages)
        self.sent_messages: list[str] = []
        self.closed = False

    async def send(self, message: str) -> None:
        self.sent_messages.append(message)

    async def recv(self) -> str:
        if not self.inbound_messages:
            raise asyncio.TimeoutError
        return self.inbound_messages.pop(0)

    async def close(self) -> None:
        self.closed = True

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()


class DisconnectingWebSocket(FakeWebSocket):
    async def __aenter__(self):
        raise ConnectionError("socket dropped")


@pytest.mark.asyncio
async def test_twelvedata_realtime_adapter_surface_exists() -> None:
    module = _load_realtime_module()
    assert hasattr(module, "TwelveDataRealtimeAdapter"), "expected TwelveDataRealtimeAdapter in trading_os_v1.providers.adapters.twelvedata"
    assert hasattr(module, "TwelveDataRealtimeConfig"), "expected TwelveDataRealtimeConfig in trading_os_v1.providers.adapters.twelvedata"


@pytest.mark.asyncio
async def test_twelvedata_realtime_maps_price_message_to_quote_snapshot(monkeypatch) -> None:
    module, adapter_cls, config_cls = _load_realtime_symbols()
    config = SimpleNamespace(
        api_key="test-key",
        websocket_url="wss://ws.twelvedata.com/v1/quotes/price?apikey=test-key",
        timeout_seconds=5,
        heartbeat_seconds=15,
        reconnect_initial_backoff_seconds=0.25,
        reconnect_max_backoff_seconds=4.0,
    )
    evidence_store = MagicMock()
    evidence_store.put_raw = AsyncMock(return_value="raw-1")
    evidence_store.put_normalized = AsyncMock(return_value="normalized-1")
    health_manager = MagicMock()

    fake_socket = FakeWebSocket(
        [
            '{"type":"subscribe","status":"ok","symbol":"AAPL"}',
            '{"event":"price","symbol":"AAPL","price":150.30,"timestamp":"2024-01-02T09:31:00Z"}',
        ]
    )
    monkeypatch.setattr(module, "websockets", SimpleNamespace(connect=AsyncMock(return_value=fake_socket)))

    adapter = adapter_cls(config=config, evidence_store=evidence_store, health_manager=health_manager)
    stream = adapter.stream_quotes(["AAPL"])

    quote = await stream.__anext__()

    assert isinstance(quote, QuoteSnapshot)
    assert quote.symbol == "AAPL"
    assert quote.last == 150.30
    assert quote.meta.provider_name in {"twelvedata", getattr(adapter, "provider_name", "twelvedata")}


@pytest.mark.asyncio
async def test_twelvedata_realtime_persists_raw_and_normalized_evidence(monkeypatch) -> None:
    module, adapter_cls, _ = _load_realtime_symbols()
    config = SimpleNamespace(api_key="test-key", websocket_url="wss://ws.twelvedata.com/v1/quotes/price?apikey=test-key")
    evidence_store = MagicMock()
    evidence_store.put_raw = AsyncMock(return_value="raw-1")
    evidence_store.put_normalized = AsyncMock(return_value="normalized-1")
    health_manager = MagicMock()

    fake_socket = FakeWebSocket(['{"event":"price","symbol":"AAPL","price":150.30,"timestamp":"2024-01-02T09:31:00Z"}'])
    monkeypatch.setattr(module, "websockets", SimpleNamespace(connect=AsyncMock(return_value=fake_socket)))

    adapter = adapter_cls(config=config, evidence_store=evidence_store, health_manager=health_manager)
    stream = adapter.stream_quotes(["AAPL"])
    quote = await stream.__anext__()

    assert quote.symbol == "AAPL"
    evidence_store.put_raw.assert_called_once()
    evidence_store.put_normalized.assert_called_once()


@pytest.mark.asyncio
async def test_twelvedata_realtime_handles_control_messages_and_heartbeat(monkeypatch) -> None:
    module, adapter_cls, _ = _load_realtime_symbols()
    config = SimpleNamespace(api_key="test-key", websocket_url="wss://ws.twelvedata.com/v1/quotes/price?apikey=test-key", heartbeat_seconds=1)
    evidence_store = MagicMock()
    evidence_store.put_raw = AsyncMock(return_value="raw-1")
    evidence_store.put_normalized = AsyncMock(return_value="normalized-1")
    health_manager = MagicMock()

    fake_socket = FakeWebSocket(
        [
            '{"type":"subscribe","status":"ok","symbol":"AAPL"}',
            '{"type":"heartbeat","status":"ok"}',
            '{"event":"price","symbol":"AAPL","price":150.30,"timestamp":"2024-01-02T09:31:00Z"}',
        ]
    )
    monkeypatch.setattr(module, "websockets", SimpleNamespace(connect=AsyncMock(return_value=fake_socket)))

    adapter = adapter_cls(config=config, evidence_store=evidence_store, health_manager=health_manager)
    stream = adapter.stream_quotes(["AAPL"])
    quote = await stream.__anext__()

    assert quote.symbol == "AAPL"
    assert fake_socket.sent_messages


@pytest.mark.asyncio
async def test_twelvedata_realtime_reconnects_with_capped_backoff_and_replays_symbols(monkeypatch) -> None:
    module, adapter_cls, _ = _load_realtime_symbols()
    config = SimpleNamespace(
        api_key="test-key",
        websocket_url="wss://ws.twelvedata.com/v1/quotes/price?apikey=test-key",
        timeout_seconds=0.01,
        reconnect_initial_backoff_seconds=0.25,
        reconnect_max_backoff_seconds=4.0,
    )
    evidence_store = MagicMock()
    evidence_store.put_raw = AsyncMock(return_value="raw-1")
    evidence_store.put_normalized = AsyncMock(return_value="normalized-1")
    health_manager = MagicMock()

    first_socket = DisconnectingWebSocket([])
    second_socket = FakeWebSocket(
        [
            '{"type":"subscribe-status","status":"ok","symbol":"AAPL"}',
            '{"type":"subscribe-status","status":"ok","symbol":"MSFT"}',
            '{"event":"price","symbol":"AAPL","price":150.30,"timestamp":"2024-01-02T09:31:00Z"}',
        ]
    )
    connect_mock = AsyncMock(side_effect=[first_socket, second_socket])
    monkeypatch.setattr(module, "websockets", SimpleNamespace(connect=connect_mock))
    sleep_mock = AsyncMock()
    monkeypatch.setattr(module.asyncio, "sleep", sleep_mock)

    adapter = adapter_cls(config=config, evidence_store=evidence_store, health_manager=health_manager)
    stream = adapter.stream_quotes(["AAPL", "MSFT"])

    quote = await stream.__anext__()

    assert isinstance(quote, QuoteSnapshot)
    assert quote.symbol == "AAPL"
    assert quote.last == 150.30
    assert connect_mock.await_count >= 2
    assert sleep_mock.await_count >= 1
    assert len(second_socket.sent_messages) >= 1
    subscribe_payload = second_socket.sent_messages[0]
    assert '"action": "subscribe"' in subscribe_payload
    assert '"symbols": "AAPL,MSFT"' in subscribe_payload


@pytest.mark.asyncio
async def test_twelvedata_quote_watch_stream_surfaces_reconnecting_then_live(monkeypatch) -> None:
    module, adapter_cls, _ = _load_realtime_symbols()
    config = SimpleNamespace(
        api_key="test-key",
        websocket_url="wss://ws.twelvedata.com/v1/quotes/price?apikey=test-key",
        timeout_seconds=0.01,
        reconnect_initial_backoff_seconds=0.25,
        reconnect_max_backoff_seconds=4.0,
    )
    evidence_store = MagicMock()
    evidence_store.put_raw = AsyncMock(return_value="raw-1")
    evidence_store.put_normalized = AsyncMock(return_value="normalized-1")
    health_manager = MagicMock()

    first_socket = DisconnectingWebSocket([])
    second_socket = FakeWebSocket([
        '{"type":"subscribe-status","status":"ok","symbol":"AAPL"}',
        '{"event":"price","symbol":"AAPL","price":150.30,"timestamp":"2024-01-02T09:31:00Z"}',
    ])
    connect_mock = AsyncMock(side_effect=[first_socket, second_socket])
    monkeypatch.setattr(module, "websockets", SimpleNamespace(connect=connect_mock))
    sleep_mock = AsyncMock()
    monkeypatch.setattr(module.asyncio, "sleep", sleep_mock)

    adapter = adapter_cls(config=config, evidence_store=evidence_store, health_manager=health_manager)
    stream = adapter.stream_quote_watch(["AAPL"])

    reconnecting = await stream.__anext__()
    live = await stream.__anext__()

    assert reconnecting.feed_status == "reconnecting"
    assert reconnecting.reconnect_attempts == 1
    assert reconnecting.reconnect_backoff_seconds == 0.25
    assert reconnecting.last_error == "socket dropped"
    assert live.feed_status == "live"
    assert live.quote is not None
    assert live.quote.symbol == "AAPL"
    assert live.last_successful_update_at is not None


@pytest.mark.asyncio
async def test_twelvedata_realtime_auth_failure_is_terminal(monkeypatch) -> None:
    module, adapter_cls, _ = _load_realtime_symbols()
    config = SimpleNamespace(api_key="bad-key", websocket_url="wss://ws.twelvedata.com/v1/quotes/price?apikey=bad-key")
    evidence_store = MagicMock()
    evidence_store.put_raw = AsyncMock(return_value="raw-1")
    evidence_store.put_normalized = AsyncMock(return_value="normalized-1")
    health_manager = MagicMock()

    fake_socket = FakeWebSocket(['{"type":"error","code":401,"message":"unauthorized"}'])
    monkeypatch.setattr(module, "websockets", SimpleNamespace(connect=AsyncMock(return_value=fake_socket)))

    adapter = adapter_cls(config=config, evidence_store=evidence_store, health_manager=health_manager)

    with pytest.raises(Exception):
        stream = adapter.stream_quotes(["AAPL"])
        await stream.__anext__()


@pytest.mark.asyncio
async def test_twelvedata_realtime_malformed_message_is_degraded_but_continues(monkeypatch) -> None:
    module, adapter_cls, _ = _load_realtime_symbols()
    config = SimpleNamespace(api_key="test-key", websocket_url="wss://ws.twelvedata.com/v1/quotes/price?apikey=test-key")
    evidence_store = MagicMock()
    evidence_store.put_raw = AsyncMock(return_value="raw-1")
    evidence_store.put_normalized = AsyncMock(return_value="normalized-1")
    health_manager = MagicMock()

    fake_socket = FakeWebSocket(
        [
            '{"event":"price","symbol":"AAPL","timestamp":"2024-01-02T09:31:00Z"}',
            '{"event":"price","symbol":"AAPL","price":150.30,"timestamp":"2024-01-02T09:31:01Z"}',
        ]
    )
    monkeypatch.setattr(module, "websockets", SimpleNamespace(connect=AsyncMock(return_value=fake_socket)))

    adapter = adapter_cls(config=config, evidence_store=evidence_store, health_manager=health_manager)
    stream = adapter.stream_quotes(["AAPL"])
    quote = await stream.__anext__()

    assert quote.symbol == "AAPL"
    assert health_manager.record_degraded.called
