from __future__ import annotations

from datetime import datetime
import sys
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
for path in (PACKAGE_ROOT, WORKSPACE_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from trading_os_v1.providers.adapters.fmp import FMPAdapter, FMPFundamentalDataProvider, resolve_fmp_api_key


def test_fmp_requires_api_key() -> None:
    with pytest.raises(ValueError):
        FMPAdapter(api_key="")


def test_fmp_maps_fundamentals_payload_to_company_fundamentals() -> None:
    adapter = FMPAdapter(api_key="test-key", base_url="https://example.invalid", config={"timeout_seconds": 2})
    payload = {
        "symbol": "AAPL",
        "as_of": "2024-01-15T15:30:00",
        "company_name": "Apple Inc.",
        "exchange": "NASDAQ",
        "currency": "USD",
        "sector": "Technology",
        "industry": "Consumer Electronics",
        "market_cap": 3000000000000,
        "shares_outstanding": 15000000000,
        "float_shares": 14900000000,
        "beta": 1.2,
        "pe_ttm": 30.5,
        "pb": 45.1,
        "ps": 7.8,
        "ev_ebitda": 24.0,
        "revenue_ttm": 400000000000,
        "net_income_ttm": 100000000000,
        "gross_margin_ttm": 0.45,
        "operating_margin_ttm": 0.3,
        "debt_to_equity": 1.5,
        "current_ratio": 1.1,
        "dividend_yield": 0.005,
        "fiscal_year_end": "09-30",
    }

    fundamentals = adapter.map_fundamentals_payload_to_company_fundamentals(payload)

    assert fundamentals.symbol == "AAPL"
    assert fundamentals.company_name == "Apple Inc."
    assert fundamentals.market_cap == 3000000000000
    assert fundamentals.meta.provider_name == "fmp"
    assert fundamentals.as_of == datetime(2024, 1, 15, 15, 30)


def test_fmp_rejects_missing_date() -> None:
    adapter = FMPAdapter(api_key="test-key")
    with pytest.raises(ValueError):
        adapter.map_fundamentals_payload_to_company_fundamentals({"symbol": "AAPL"})


def test_resolve_fmp_api_key_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FMP_API_KEY", "env-key")
    assert resolve_fmp_api_key() == "env-key"


@pytest.mark.asyncio
async def test_fmp_runtime_provider_uses_stable_endpoint_and_header(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, dict[str, str], dict[str, str]]] = []

    class _FakeResponse:
        status_code = 200

        def __init__(self, payload: object) -> None:
            self._payload = payload

        def raise_for_status(self) -> None:
            return None

        def json(self) -> object:
            return self._payload

    class _FakeAsyncClient:
        def __init__(self, timeout: float) -> None:
            self.timeout = timeout

        async def __aenter__(self) -> "_FakeAsyncClient":
            return self

        async def __aexit__(self, exc_type, exc, tb) -> None:
            return None

        async def get(self, url: str, params: dict[str, str], headers: dict[str, str]) -> _FakeResponse:
            calls.append((url, params, headers))
            if url.endswith("ratios-ttm"):
                return _FakeResponse([{"returnOnEquityTTM": 0.27, "netProfitMarginTTM": 0.19}])
            if url.endswith("key-metrics-ttm"):
                return _FakeResponse([{"netDebtToEBITDA": 0.82}])
            raise AssertionError(f"unexpected url: {url}")

    monkeypatch.setattr("trading_os_v1.providers.adapters.fmp.httpx.AsyncClient", _FakeAsyncClient)

    provider = FMPFundamentalDataProvider(api_key="test-key")
    result = await provider.get_fundamental_data("AAPL")

    assert result == {"roe": 0.27, "net_margin": 0.19, "debt_ebitda": 0.82}
    assert calls[0][0] == "https://financialmodelingprep.com/stable/ratios-ttm"
    assert calls[0][1] == {"symbol": "AAPL"}
    assert calls[0][2] == {"apikey": "test-key"}
    assert calls[1][0] == "https://financialmodelingprep.com/stable/key-metrics-ttm"


@pytest.mark.asyncio
async def test_fmp_runtime_provider_translates_403(monkeypatch: pytest.MonkeyPatch) -> None:
    class _FakeResponse:
        status_code = 403

        def raise_for_status(self) -> None:
            request = SimpleNamespace(method="GET", url="https://financialmodelingprep.com/stable/ratios-ttm")
            response = SimpleNamespace(status_code=403)
            raise httpx.HTTPStatusError("forbidden", request=request, response=response)

        def json(self) -> object:
            return []

    class _FakeAsyncClient:
        def __init__(self, timeout: float) -> None:
            self.timeout = timeout

        async def __aenter__(self) -> "_FakeAsyncClient":
            return self

        async def __aexit__(self, exc_type, exc, tb) -> None:
            return None

        async def get(self, url: str, params: dict[str, str], headers: dict[str, str]) -> _FakeResponse:
            return _FakeResponse()

    monkeypatch.setattr("trading_os_v1.providers.adapters.fmp.httpx.AsyncClient", _FakeAsyncClient)

    provider = FMPFundamentalDataProvider(api_key="test-key")

    with pytest.raises(PermissionError, match="stable endpoint is enabled"):
        await provider.get_fundamental_data("AAPL")


@pytest.mark.asyncio
async def test_fmp_runtime_provider_maps_required_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = FMPFundamentalDataProvider(api_key="test-key", base_url="https://example.invalid")

    async def _fake_fetch(endpoint: str, symbol: str):
        assert symbol == "AAPL"
        if endpoint == "ratios-ttm":
            return {
                "returnOnEquityTTM": 0.27,
                "netProfitMarginTTM": 0.19,
            }
        if endpoint == "key-metrics-ttm":
            return {
                "netDebtToEBITDA": 0.82,
            }
        raise AssertionError("unexpected endpoint")

    monkeypatch.setattr(provider, "_fetch_first_record", _fake_fetch)

    result = await provider.get_fundamental_data("AAPL")
    assert result["roe"] == 0.27
    assert result["net_margin"] == 0.19
    assert result["debt_ebitda"] == 0.82