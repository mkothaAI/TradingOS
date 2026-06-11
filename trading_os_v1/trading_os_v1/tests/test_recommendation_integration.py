from __future__ import annotations

import importlib
import sys
from datetime import date
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_os_v1.app import _build_dashboard_source_model
from backend.schemas.decision_models import DecisionItem
from backend.schemas.models_responses import DecisionResponse
from backend.schemas.shared import RequestMeta, SizeInfo


@pytest.mark.asyncio
async def test_recommendation_projection_present_in_shell_snapshot() -> None:
    snapshot = await _build_dashboard_source_model()
    bundle = snapshot.get("projection_bundle") or {}
    assert bundle.get("recommendation_blocks")
    assert bundle.get("recommendation_blocks")[0]["block_id"] == "rec-aapl-entry"


@pytest.mark.asyncio
async def test_recommendation_projection_prefers_real_decision_response(monkeypatch) -> None:
    def _real_decision_response(*args, **kwargs) -> DecisionResponse:
        return DecisionResponse(
            meta=RequestMeta(request_id="req-live-1", as_of_date=date(2026, 5, 25)),
            status="OK",
            decisions={
                "AAPL": DecisionItem(
                    ticker="AAPL",
                    decision="HOLD",
                    size_info=SizeInfo(allowed_qty=10),
                    reason_codes=["NO_SIGNAL"],
                    applied_rules=[],
                )
            },
            errors=[],
        )

    app_module = importlib.import_module("trading_os_v1.app")
    monkeypatch.setattr(app_module, "build_runtime_decision_response", _real_decision_response)

    snapshot = await _build_dashboard_source_model()
    bundle = snapshot.get("projection_bundle") or {}

    assert bundle.get("recommendation_blocks")
    assert bundle.get("recommendation_blocks")[0]["block_type"] == "monitoring"
