from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
for path in (PACKAGE_ROOT, WORKSPACE_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from trading_os_v1.providers.adapters.portfolio_state import FilePortfolioStateConfig, FilePortfolioStateProvider, validate_portfolio_state_payload


def test_validate_portfolio_state_payload_accepts_required_fields() -> None:
    payload = {
        "total_equity": 150000,
        "cash": 40000,
        "positions": [{"symbol": "AAPL", "qty": 12}],
    }

    result = validate_portfolio_state_payload(payload)

    assert result["total_equity"] == 150000.0
    assert result["cash"] == 40000.0
    assert result["positions"][0]["symbol"] == "AAPL"


def test_validate_portfolio_state_payload_rejects_missing_required_field() -> None:
    with pytest.raises(ValueError, match="portfolio_state.cash is required"):
        validate_portfolio_state_payload({"total_equity": 10, "positions": []})


@pytest.mark.asyncio
async def test_file_portfolio_state_provider_reads_runtime_snapshot(tmp_path: Path) -> None:
    snapshot = {
        "total_equity": 210000.0,
        "cash": 50000.0,
        "positions": [{"symbol": "MSFT", "qty": 8}],
    }
    snapshot_path = tmp_path / "portfolio_state.json"
    snapshot_path.write_text(json.dumps(snapshot), encoding="utf-8")

    provider = FilePortfolioStateProvider(FilePortfolioStateConfig(snapshot_path=snapshot_path))
    result = await provider.get_portfolio_state()

    assert result["total_equity"] == 210000.0
    assert result["positions"][0]["symbol"] == "MSFT"
