import asyncio
import json
import os
from trading_os_v1.app import _build_dashboard_source_model
from trading_os_v1.providers.adapters.fmp import FMPFundamentalDataProvider
from trading_os_v1.providers.adapters.portfolio_state import FilePortfolioStateProvider


async def main():
    out = {"env": {}, "fmp": None, "portfolio_state": None, "dashboard": None}
    for key in ["FMP_API_KEY", "PORTFOLIO_STATE_JSON_PATH", "TWELVEDATA_API_KEY", "FINNHUB_API_KEY"]:
        out["env"][key] = bool(os.getenv(key))
    try:
        fmp = FMPFundamentalDataProvider(api_key=os.environ["FMP_API_KEY"])
        data = await fmp.get_fundamental_data("AAPL")
        out["fmp"] = {"ok": True, "keys": sorted(list(data))[:20]}
    except Exception as exc:
        out["fmp"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    try:
        portfolio_provider = FilePortfolioStateProvider.from_environment()
        state = await portfolio_provider.get_portfolio_state()
        out["portfolio_state"] = {"ok": True, "type": type(state).__name__}
    except Exception as exc:
        out["portfolio_state"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    try:
        shell = await _build_dashboard_source_model()
        out["dashboard"] = {
            "projection_keys": sorted(shell.get("projection_bundle", {}).keys()),
            "health_rows": len(shell.get("health_rows", [])),
            "blocks": len(shell.get("projection_bundle", {}).get("recommendation_blocks", [])),
        }
    except Exception as exc:
        out["dashboard"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    print(json.dumps(out, default=str, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
