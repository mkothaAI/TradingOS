from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def resolve_portfolio_state_snapshot_path() -> Path:
    """Resolve the configured portfolio-state snapshot path from environment."""
    configured = (os.getenv("PORTFOLIO_STATE_JSON_PATH") or "").strip()
    if not configured:
        raise ValueError("PORTFOLIO_STATE_JSON_PATH is required for runtime portfolio-state sourcing")
    return Path(configured).expanduser().resolve()


def _validated_float(value: Any, field_name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"portfolio_state.{field_name} must be numeric") from exc
    if number < 0:
        raise ValueError(f"portfolio_state.{field_name} must be non-negative")
    return number


def _validate_position_item(position: Any) -> dict[str, Any]:
    if not isinstance(position, dict):
        raise ValueError("portfolio_state.positions items must be objects")
    if not position.get("symbol"):
        raise ValueError("portfolio_state.positions items must include symbol")
    if "qty" in position and not isinstance(position.get("qty"), (int, float)):
        raise ValueError("portfolio_state.positions.qty must be numeric when provided")
    return dict(position)


def validate_portfolio_state_payload(payload: Any) -> dict[str, Any]:
    """Validate and normalize runtime portfolio_state payload."""
    if not isinstance(payload, dict):
        raise ValueError("portfolio_state snapshot must be a JSON object")

    if "total_equity" not in payload:
        raise ValueError("portfolio_state.total_equity is required")
    if "cash" not in payload:
        raise ValueError("portfolio_state.cash is required")
    if "positions" not in payload:
        raise ValueError("portfolio_state.positions is required")

    positions = payload.get("positions")
    if not isinstance(positions, list):
        raise ValueError("portfolio_state.positions must be an array")

    return {
        "total_equity": _validated_float(payload.get("total_equity"), "total_equity"),
        "cash": _validated_float(payload.get("cash"), "cash"),
        "positions": [_validate_position_item(item) for item in positions],
    }


@dataclass(frozen=True)
class FilePortfolioStateConfig:
    snapshot_path: Path


class FilePortfolioStateProvider:
    """Runtime portfolio-state owner backed by an external JSON snapshot."""

    provider_name = "portfolio_state_file"

    def __init__(self, config: FilePortfolioStateConfig) -> None:
        self._config = config

    @classmethod
    def from_environment(cls) -> "FilePortfolioStateProvider":
        return cls(FilePortfolioStateConfig(snapshot_path=resolve_portfolio_state_snapshot_path()))

    async def get_portfolio_state(self, as_of_date: Any = None) -> dict[str, Any]:
        del as_of_date
        path = self._config.snapshot_path
        if not path.exists():
            raise FileNotFoundError(f"portfolio_state snapshot not found: {path}")

        payload = json.loads(path.read_text(encoding="utf-8"))
        return validate_portfolio_state_payload(payload)
