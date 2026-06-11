from __future__ import annotations

import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_os_v1.app import _build_dashboard_source_model


@pytest.mark.asyncio
async def test_options_projection_present_in_shell_snapshot() -> None:
    snapshot = await _build_dashboard_source_model()
    bundle = snapshot.get("projection_bundle") or {}
    assert bundle.get("options_profiles")
    assert bundle.get("options_profiles")[0]["profile_id"] == "options-runtime-1"
