import os
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

# Adapter import will exist once implementation is added; tests will fail clearly if missing
from trading_os_v1.providers.adapters.twelvedata import TwelveDataIntradayAdapter, TwelveDataConfig

try:
    from trading_os_v1.providers.errors import AuthenticationError, RemoteServiceError
except Exception:
    AuthenticationError = Exception
    RemoteServiceError = Exception


SAMPLE_TWELVEDATA_INTRADAY = [
    {
        "datetime": "2024-01-02 09:31:00",
        "open": "150.00",
        "high": "150.50",
        "low": "149.80",
        "close": "150.30",
        "volume": "1200",
    }
]


class DummyResponse:
    def __init__(self, status_code: int, json_body):
        self.status_code = status_code
        self._json = json_body

    async def json(self):
        return self._json

    @property
    def text(self):
        try:
            import json

            return json.dumps(self._json)
        except Exception:
            return str(self._json)


@pytest.mark.asyncio
async def test_successful_mapping_of_intraday_bars_and_evidence_and_health(monkeypatch):
    mock_http = AsyncMock()
    mock_http.get = AsyncMock(return_value=DummyResponse(200, {"values": SAMPLE_TWELVEDATA_INTRADAY}))

    mock_evidence = MagicMock()
    mock_evidence.put_raw = MagicMock(return_value="raw_1")
    mock_evidence.put_normalized = MagicMock()

    mock_health = MagicMock()
    config = TwelveDataConfig(api_key="test-key", base_url="https://api.twelvedata.com", timeout_seconds=10)
    adapter = TwelveDataIntradayAdapter(config=config, evidence_store=mock_evidence, health_manager=mock_health, http_client=mock_http)

    bars = await adapter.get_bars("AAPL", start="2024-01-02", end="2024-01-02", timeframe="1min")

    assert len(bars) == 1
    pb = bars[0]
    assert float(pb.open) == 150.00
    assert float(pb.high) == 150.50
    assert float(pb.low) == 149.80
    assert float(pb.close) == 150.30
    assert int(pb.volume) == 1200
    assert pb.provider == "twelvedata"
    assert getattr(pb, "evidence_id", None) is not None

    mock_evidence.put_raw.assert_called_once()
    mock_evidence.put_normalized.assert_called_once()
    normalized_kwargs = mock_evidence.put_normalized.call_args.kwargs
    assert normalized_kwargs["raw_evidence_id"] == "raw_1"
    assert normalized_kwargs["provider_name"] == "twelvedata"

    mock_health.record_success.assert_called_once()


@pytest.mark.asyncio
async def test_401_auth_failure_behavior_records_failure(monkeypatch):
    mock_http = AsyncMock()
    mock_http.get = AsyncMock(return_value=DummyResponse(401, {"code": 401, "message": "Invalid API key"}))

    mock_evidence = MagicMock()
    mock_evidence.put_raw = MagicMock(return_value="raw_err")

    mock_health = MagicMock()
    config = TwelveDataConfig(api_key="bad-key", base_url="https://api.twelvedata.com", timeout_seconds=5)
    adapter = TwelveDataIntradayAdapter(config=config, evidence_store=mock_evidence, health_manager=mock_health, http_client=mock_http)

    with pytest.raises(AuthenticationError):
        await adapter.get_bars("AAPL", start="2024-01-02", end="2024-01-02", timeframe="1min")

    mock_evidence.put_raw.assert_called_once()
    mock_health.record_failure.assert_called_once()


@pytest.mark.asyncio
async def test_429_rate_limit_degraded_then_success(monkeypatch):
    resp_429 = DummyResponse(429, {"code": 429, "message": "Rate limit"})
    resp_200 = DummyResponse(200, {"values": SAMPLE_TWELVEDATA_INTRADAY})

    mock_http = AsyncMock()
    mock_http.get = AsyncMock(side_effect=[resp_429, resp_200])

    mock_evidence = MagicMock()
    mock_evidence.put_raw = MagicMock(return_value="raw_retry")
    mock_evidence.put_normalized = MagicMock()

    mock_health = MagicMock()
    config = TwelveDataConfig(api_key="test-key", base_url="https://api.twelvedata.com", timeout_seconds=5)
    adapter = TwelveDataIntradayAdapter(config=config, evidence_store=mock_evidence, health_manager=mock_health, http_client=mock_http)

    bars = await adapter.get_bars("AAPL", start="2024-01-02", end="2024-01-02", timeframe="1min")

    assert len(bars) == 1
    assert mock_evidence.put_raw.call_count >= 1
    mock_health.record_degraded.assert_called()
    mock_health.record_success.assert_called()


@pytest.mark.asyncio
async def test_5xx_retry_then_failure_records_failure(monkeypatch):
    resp_500 = DummyResponse(500, {"code": 500, "message": "Server error"})
    resp_500b = DummyResponse(500, {"code": 500, "message": "Server2"})

    mock_http = AsyncMock()
    mock_http.get = AsyncMock(side_effect=[resp_500, resp_500b])

    mock_evidence = MagicMock()
    mock_evidence.put_raw = MagicMock()

    mock_health = MagicMock()
    config = TwelveDataConfig(api_key="test-key", base_url="https://api.twelvedata.com", timeout_seconds=2)
    adapter = TwelveDataIntradayAdapter(config=config, evidence_store=mock_evidence, health_manager=mock_health, http_client=mock_http)

    with pytest.raises(RemoteServiceError):
        await adapter.get_bars("AAPL", start="2024-01-02", end="2024-01-02", timeframe="1min")

    assert mock_evidence.put_raw.called
    mock_health.record_failure.assert_called_once()


@pytest.mark.asyncio
async def test_partial_malformed_row_parse_records_degraded(monkeypatch):
    malformed = [
        {"datetime": "2024-01-02 09:31:00", "open": "150.0", "high": "151.0", "low": "149.5", "close": "150.5", "volume": "1000"},
        {"datetime": "2024-01-02 09:32:00", "open": None, "high": None, "low": None, "close": None, "volume": None},
    ]

    mock_http = AsyncMock()
    mock_http.get = AsyncMock(return_value=DummyResponse(200, {"values": malformed}))

    mock_evidence = MagicMock()
    mock_evidence.put_raw = MagicMock(return_value="raw_partial")
    mock_evidence.put_normalized = MagicMock()

    mock_health = MagicMock()
    config = TwelveDataConfig(api_key="test-key", base_url="https://api.twelvedata.com", timeout_seconds=5)
    adapter = TwelveDataIntradayAdapter(config=config, evidence_store=mock_evidence, health_manager=mock_health, http_client=mock_http)

    bars = await adapter.get_bars("AAPL", start="2024-01-02", end="2024-01-02", timeframe="1min")

    assert len(bars) == 1
    mock_evidence.put_raw.assert_called_once()
    mock_evidence.put_normalized.assert_called_once()
    mock_health.record_degraded.assert_called_once()


@pytest.mark.asyncio
async def test_get_provider_meta_returns_expected():
    mock_http = AsyncMock()
    mock_http.get = AsyncMock(return_value=DummyResponse(200, {"values": SAMPLE_TWELVEDATA_INTRADAY}))

    mock_evidence = MagicMock()
    mock_health = MagicMock()
    config = TwelveDataConfig(api_key="k", base_url="https://api.twelvedata.com", timeout_seconds=5)
    adapter = TwelveDataIntradayAdapter(config=config, evidence_store=mock_evidence, health_manager=mock_health, http_client=mock_http)

    meta = await adapter.get_provider_meta()
    assert meta.provider == "twelvedata"
    assert "twelvedata" in meta.base_url
