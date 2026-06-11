from __future__ import annotations

import os
from datetime import date, datetime
from typing import Any, Mapping

import httpx

from trading_os_v1.providers.base import FundamentalsProvider
from trading_os_v1.providers.schemas import CompanyFundamentals, ProviderCapability, ProviderMeta


_FMP_ENV_KEYS = ("FMP_API_KEY", "FINANCIALMODELINGPREP_API_KEY", "FMP_KEY")


def resolve_fmp_api_key(api_key: str | None = None) -> str:
    candidate = (api_key or "").strip()
    if candidate:
        return candidate

    for env_key in _FMP_ENV_KEYS:
        env_value = os.getenv(env_key, "").strip()
        if env_value:
            return env_value

    raise ValueError("FMP api_key is required")


class FMPAdapter(FundamentalsProvider):
    provider_name = "fmp"
    provider_capability = ProviderCapability.FUNDAMENTALS

    def __init__(
        self,
        api_key: str,
        base_url: str | None = None,
        config: Mapping[str, Any] | None = None,
    ) -> None:
        if not api_key or not api_key.strip():
            raise ValueError("api_key is required")
        self.api_key = api_key
        self.base_url = base_url or "https://financialmodelingprep.com/stable"
        self.config = dict(config or {})

    @staticmethod
    def map_fundamentals_payload_to_company_fundamentals(
        payload: Mapping[str, Any],
        provider_name: str = "fmp",
    ) -> CompanyFundamentals:
        as_of = payload.get("as_of") or payload.get("date") or payload.get("reported_at")
        if isinstance(as_of, str):
            as_of = datetime.fromisoformat(as_of)
        if not isinstance(as_of, datetime):
            raise ValueError("fundamentals payload must include as_of/date/reported_at")

        meta = ProviderMeta(
            provider_name=provider_name,
            provider_version=payload.get("provider_version"),
            source_id=payload.get("symbol") or payload.get("source_id"),
            raw_hash=payload.get("raw_hash"),
            received_at=payload.get("received_at") or as_of,
            is_delayed=bool(payload.get("is_delayed", False)),
        )
        return CompanyFundamentals(
            symbol=str(payload.get("symbol") or ""),
            as_of=as_of,
            company_name=payload.get("company_name"),
            exchange=payload.get("exchange"),
            currency=payload.get("currency"),
            sector=payload.get("sector"),
            industry=payload.get("industry"),
            market_cap=payload.get("market_cap"),
            shares_outstanding=payload.get("shares_outstanding"),
            float_shares=payload.get("float_shares"),
            beta=payload.get("beta"),
            pe_ttm=payload.get("pe_ttm"),
            pb=payload.get("pb"),
            ps=payload.get("ps"),
            ev_ebitda=payload.get("ev_ebitda"),
            revenue_ttm=payload.get("revenue_ttm"),
            net_income_ttm=payload.get("net_income_ttm"),
            gross_margin_ttm=payload.get("gross_margin_ttm"),
            operating_margin_ttm=payload.get("operating_margin_ttm"),
            debt_to_equity=payload.get("debt_to_equity"),
            current_ratio=payload.get("current_ratio"),
            dividend_yield=payload.get("dividend_yield"),
            fiscal_year_end=payload.get("fiscal_year_end"),
            meta=meta,
        )

    async def get_company_fundamentals(self, symbol: str, as_of: datetime | None = None) -> CompanyFundamentals:
        raise NotImplementedError("FMPAdapter Phase 12 is mapping-only; live requests are not implemented")


class FMPFundamentalDataProvider:
    """Runtime owner for raw `fundamental_data` sourced from FMP live endpoints."""

    provider_name = "fmp_fundamental_data"

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout_seconds: float = 20.0,
    ) -> None:
        self.api_key = resolve_fmp_api_key(api_key)
        self.base_url = (base_url or "https://financialmodelingprep.com/stable").rstrip("/")
        self.timeout_seconds = float(timeout_seconds)

    async def _fetch_first_record(self, endpoint: str, symbol: str) -> dict[str, Any]:
        url = f"{self.base_url}/{endpoint}"
        params = {"symbol": symbol}
        headers = {"apikey": self.api_key}
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            try:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                if exc.response is not None and exc.response.status_code == 403:
                    raise PermissionError(
                        f"FMP returned 403 for {endpoint} on {symbol}; check API plan, key validity, and whether the stable endpoint is enabled"
                    ) from exc
                raise
            payload = response.json()

        if isinstance(payload, list):
            if not payload:
                raise ValueError(f"FMP {endpoint} returned no records for {symbol}")
            first = payload[0]
        elif isinstance(payload, dict):
            first = payload
        else:
            raise ValueError(f"Unexpected FMP payload shape for {endpoint}")

        if not isinstance(first, dict):
            raise ValueError(f"Unexpected FMP {endpoint} record type for {symbol}")
        return first

    @staticmethod
    def _coerce_numeric(value: Any, field_name: str) -> float:
        try:
            return float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"FMP field {field_name} is missing or non-numeric") from exc

    async def get_fundamental_data(self, symbol: str, as_of_date: date | None = None) -> dict[str, Any]:
        del as_of_date
        ratios = await self._fetch_first_record("ratios-ttm", symbol)
        metrics = await self._fetch_first_record("key-metrics-ttm", symbol)

        roe = metrics.get("returnOnEquityTTM") or ratios.get("returnOnEquityTTM")
        net_margin = ratios.get("netProfitMarginTTM")
        debt_ebitda = (
            metrics.get("netDebtToEBITDATTM")
            or metrics.get("netDebtToEBITDA")
            or metrics.get("netDebtToEbitdaTTM")
            or metrics.get("netDebtToEbitda")
            or metrics.get("debtToEbitdaTTM")
            or metrics.get("debtToEbitda")
            or ratios.get("debtToEBITDATTM")
            or ratios.get("debtToEBITDA")
            or ratios.get("debtToEbitdaTTM")
            or ratios.get("debtToEbitda")
        )

        return {
            "roe": self._coerce_numeric(roe, "returnOnEquityTTM"),
            "net_margin": self._coerce_numeric(net_margin, "netProfitMarginTTM"),
            "debt_ebitda": self._coerce_numeric(debt_ebitda, "netDebtToEBITDA"),
        }