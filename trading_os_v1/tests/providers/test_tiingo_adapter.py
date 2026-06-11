import os
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

# Top-level import of the adapter under test. This will fail if the adapter
# hasn't been implemented yet — the test run will surface that clearly.
from trading_os_v1.providers.adapters.tiingo import TiingoHistoricalAdapter, TiingoConfig

try:
    from trading_os_v1.providers.errors import AuthenticationError, RemoteServiceError
except Exception:
    # TODO: replace these fallbacks with the repo's specific error types
    AuthenticationError = Exception
    RemoteServiceError = Exception


SAMPLE_TiINGO_DAILY = [
    {
        "date": "2020-01-02",
        "open": 75.0875,
        "high": 75.15,
        "low": 73.7975,
        "close": 75.0875,
        "volume": 135480400,
        "adjClose": 75.0875,
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
async def test_successful_mapping_of_daily_bars_and_evidence_and_health(monkeypatch):
    mock_http = AsyncMock()
    mock_http.get = AsyncMock(return_value=DummyResponse(200, SAMPLE_TiINGO_DAILY))

    mock_evidence = MagicMock()
    mock_evidence.put_raw = MagicMock(return_value="raw_1")
    mock_evidence.put_normalized = MagicMock(return_value="normalized_1")

    mock_health = MagicMock()
    config = TiingoConfig(api_key="test-key", base_url="https://api.tiingo.com", timeout_seconds=10)
    adapter = TiingoHistoricalAdapter(config=config, evidence_store=mock_evidence, health_manager=mock_health, http_client=mock_http)

    bars = await adapter.fetch_price_bars("AAPL", start="2020-01-01", end="2020-01-03")

    # mapping assertions
    assert len(bars) == 1
    pb = bars[0]
    assert pb.open == 75.0875
    assert pb.high == 75.15
    assert pb.low == 73.7975
    assert pb.close == 75.0875
    assert pb.volume == 135480400
    assert pb.provider == "tiingo"
    assert getattr(pb, "evidence_id", None) is not None
    assert getattr(pb, "provenance_chain_id", None) is not None
    assert getattr(pb, "raw_artifact_sha256", None) is not None
    assert getattr(pb, "normalized_artifact_sha256", None) is not None

    # evidence assertions
    mock_evidence.put_raw.assert_called_once()
    mock_evidence.put_normalized.assert_called_once()
    # ensure normalized referenced raw id
    normalized_kwargs = mock_evidence.put_normalized.call_args.kwargs
    assert normalized_kwargs["raw_evidence_id"] == "raw_1"
    assert normalized_kwargs["provider_name"] == "tiingo"

    # health assertion
    mock_health.record_success.assert_called_once()


@pytest.mark.asyncio
async def test_401_auth_failure_behavior_records_failure(monkeypatch):
    mock_http = AsyncMock()
    mock_http.get = AsyncMock(return_value=DummyResponse(401, {"error": "Unauthorized"}))

    mock_evidence = MagicMock()
    mock_evidence.put_raw = MagicMock(return_value="raw_err")

    mock_health = MagicMock()
    config = TiingoConfig(api_key="bad-key", base_url="https://api.tiingo.com", timeout_seconds=5)
    adapter = TiingoHistoricalAdapter(config=config, evidence_store=mock_evidence, health_manager=mock_health, http_client=mock_http)

    with pytest.raises(AuthenticationError):
        await adapter.fetch_price_bars("AAPL", start="2020-01-01", end="2020-01-03")

    mock_evidence.put_raw.assert_called_once()
    mock_health.record_failure.assert_called_once()


@pytest.mark.asyncio
async def test_429_rate_limit_degraded_then_success(monkeypatch):
    # first response 429, second response 200
    resp_429 = DummyResponse(429, {"error": "rate limit"})
    resp_200 = DummyResponse(200, SAMPLE_TiINGO_DAILY)

    mock_http = AsyncMock()
    mock_http.get = AsyncMock(side_effect=[resp_429, resp_200])

    mock_evidence = MagicMock()
    mock_evidence.put_raw = MagicMock(return_value="raw_retry")
    mock_evidence.put_normalized = MagicMock()

    mock_health = MagicMock()
    config = TiingoConfig(api_key="test-key", base_url="https://api.tiingo.com", timeout_seconds=5)
    adapter = TiingoHistoricalAdapter(config=config, evidence_store=mock_evidence, health_manager=mock_health, http_client=mock_http)

    bars = await adapter.fetch_price_bars("AAPL", start="2020-01-01", end="2020-01-03")

    # should succeed after retry
    assert len(bars) == 1
    # evidence persisted at least once
    assert mock_evidence.put_raw.call_count >= 1
    # degraded recorded due to 429 then success recorded
    mock_health.record_degraded.assert_called()
    mock_health.record_success.assert_called()


@pytest.mark.asyncio
async def test_5xx_retry_then_failure_records_failure(monkeypatch):
    resp_500 = DummyResponse(500, {"error": "server"})
    resp_500b = DummyResponse(500, {"error": "server2"})

    mock_http = AsyncMock()
    # exhaust retries
    mock_http.get = AsyncMock(side_effect=[resp_500, resp_500b])

    mock_evidence = MagicMock()
    mock_evidence.put_raw = MagicMock()

    mock_health = MagicMock()
    config = TiingoConfig(api_key="test-key", base_url="https://api.tiingo.com", timeout_seconds=2)
    adapter = TiingoHistoricalAdapter(config=config, evidence_store=mock_evidence, health_manager=mock_health, http_client=mock_http)

    with pytest.raises(RemoteServiceError):
        await adapter.fetch_price_bars("AAPL", start="2020-01-01", end="2020-01-03")

    # raw persisted for error
    assert mock_evidence.put_raw.called
    mock_health.record_failure.assert_called_once()


@pytest.mark.asyncio
async def test_partial_malformed_row_parse_records_degraded(monkeypatch):
    malformed = [
        {"date": "2020-01-02", "open": 75.0, "high": 76.0, "low": 74.0, "close": 75.0, "volume": 100000},
        {"date": "2020-01-03", "open": None, "high": None, "low": None, "close": None, "volume": None},
    ]

    mock_http = AsyncMock()
    mock_http.get = AsyncMock(return_value=DummyResponse(200, malformed))

    mock_evidence = MagicMock()
    mock_evidence.put_raw = MagicMock(return_value="raw_partial")
    mock_evidence.put_normalized = MagicMock()

    mock_health = MagicMock()
    config = TiingoConfig(api_key="test-key", base_url="https://api.tiingo.com", timeout_seconds=5)
    adapter = TiingoHistoricalAdapter(config=config, evidence_store=mock_evidence, health_manager=mock_health, http_client=mock_http)

    bars = await adapter.fetch_price_bars("AAPL", start="2020-01-01", end="2020-01-04")

    assert len(bars) == 1
    mock_evidence.put_raw.assert_called_once()
    mock_evidence.put_normalized.assert_called_once()
    mock_health.record_degraded.assert_called_once()


@pytest.mark.asyncio
async def test_get_provider_meta_returns_expected():
    mock_http = AsyncMock()
    mock_http.get = AsyncMock(return_value=DummyResponse(200, SAMPLE_TiINGO_DAILY))

    mock_evidence = MagicMock()
    mock_health = MagicMock()
    config = TiingoConfig(api_key="k", base_url="https://api.tiingo.com", timeout_seconds=5)
    adapter = TiingoHistoricalAdapter(config=config, evidence_store=mock_evidence, health_manager=mock_health, http_client=mock_http)

    meta = await adapter.get_provider_meta()
    assert meta.provider == "tiingo"
    assert "tiingo" in meta.base_url
