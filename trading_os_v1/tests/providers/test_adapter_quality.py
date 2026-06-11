from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from trading_os_v1.providers.adapters.tiingo import TiingoConfig, TiingoHistoricalAdapter
from trading_os_v1.providers.adapters.twelvedata import TwelveDataConfig, TwelveDataIntradayAdapter
from trading_os_v1.providers.config import classify_provider_error, normalize_provider_config
from trading_os_v1.providers.evidence_summaries import summarize_evidence_eligibility_view, summarize_local_evidence
from trading_os_v1.providers.health import ProviderHealthManager
from trading_os_v1.providers.health_summaries import summarize_health
from trading_os_v1.providers.local_evidence_store import LocalEvidenceStore
from trading_os_v1.providers.registry import ProviderBinding, ProviderRegistry
from trading_os_v1.providers.schemas import ProviderCapability


class DummyResponse:
    def __init__(self, status_code: int, json_body):
        self.status_code = status_code
        self._json = json_body

    async def json(self):
        return self._json


def test_config_normalization(monkeypatch) -> None:
    monkeypatch.setenv("TWELVEDATA_API_KEY", "env-twelve-key")
    normalized = normalize_provider_config(
        explicit={"api_key": "", "timeout_seconds": None},
        env_map={"api_key": "TWELVEDATA_API_KEY"},
        defaults={"timeout_seconds": 30, "max_retries": 2},
        required=("api_key",),
    )
    assert normalized["api_key"] == "env-twelve-key"
    assert normalized["timeout_seconds"] == 30
    assert normalized["max_retries"] == 2

    monkeypatch.setenv("TIINGO_API_KEY", "env-tiingo-key")
    tiingo = TiingoConfig(api_key="", timeout_seconds=12)
    assert tiingo.api_key == "env-tiingo-key"
    assert tiingo.timeout_seconds == 12

    twelve = TwelveDataConfig(api_key="explicit-key", timeout_seconds=8)
    assert twelve.api_key == "explicit-key"
    assert twelve.timeout_seconds == 8


def test_error_classification() -> None:
    retryable = classify_provider_error(http_status=429, payload={"message": "rate limit"})
    terminal = classify_provider_error(http_status=401, payload={"message": "unauthorized"})
    provider_error = classify_provider_error(http_status=422, payload={"message": "bad symbol"})
    timeout_error = classify_provider_error(error=TimeoutError("timed out"))

    assert retryable.disposition == "retryable"
    assert retryable.retryable is True
    assert terminal.disposition == "terminal_auth"
    assert terminal.terminal is True
    assert provider_error.disposition == "provider_error"
    assert provider_error.retryable is False
    assert timeout_error.disposition == "retryable"


@pytest.mark.asyncio
async def test_adapter_quality_round_trip(tmp_path) -> None:
    store = LocalEvidenceStore(tmp_path)
    manager = ProviderHealthManager()
    registry = ProviderRegistry(manager)
    registry.register(
        ProviderBinding(
            capability=ProviderCapability.MARKET_DATA,
            provider_name="tiingo",
            factory=lambda: object(),
            priority=0,
        )
    )
    registry.register(
        ProviderBinding(
            capability=ProviderCapability.MARKET_DATA,
            provider_name="twelvedata",
            factory=lambda: object(),
            priority=1,
        )
    )

    tiingo_http = AsyncMock()
    tiingo_http.get = AsyncMock(
        return_value=DummyResponse(
            200,
            [
                {
                    "date": "2020-01-02",
                    "open": 75.0,
                    "high": 76.0,
                    "low": 74.0,
                    "close": 75.5,
                    "volume": 1000,
                    "adjClose": 75.5,
                }
            ],
        )
    )
    twelve_http = AsyncMock()
    twelve_http.get = AsyncMock(
        return_value=DummyResponse(
            200,
            {
                "values": [
                    {
                        "datetime": "2024-01-02 09:31:00",
                        "open": "150.0",
                        "high": "151.0",
                        "low": "149.5",
                        "close": "150.5",
                        "volume": "1000",
                    }
                ]
            },
        )
    )

    tiingo = TiingoHistoricalAdapter(
        config=TiingoConfig(api_key="tiingo-key"),
        evidence_store=store,
        health_manager=manager,
        http_client=tiingo_http,
    )
    twelve = TwelveDataIntradayAdapter(
        config=TwelveDataConfig(api_key="twelve-key"),
        evidence_store=store,
        health_manager=manager,
        http_client=twelve_http,
    )

    tiingo_bars = await tiingo.fetch_price_bars("AAPL", start="2020-01-01", end="2020-01-03")
    twelve_bars = await twelve.fetch_price_bars("AAPL", start="2024-01-02", end="2024-01-02", timeframe="1min")

    assert len(tiingo_bars) == 1
    assert len(twelve_bars) == 1

    health_summary = summarize_health(registry, capabilities=[ProviderCapability.MARKET_DATA])
    evidence_summary = summarize_local_evidence(store)
    eligibility = summarize_evidence_eligibility_view(health_summary, evidence_summary=evidence_summary)

    assert "tiingo" in evidence_summary
    assert "twelvedata" in evidence_summary
    assert eligibility["tiingo"][ProviderCapability.MARKET_DATA.value].classification_code == "HEALTHY_ELIGIBLE"
    assert eligibility["twelvedata"][ProviderCapability.MARKET_DATA.value].classification_code == "HEALTHY_ELIGIBLE"