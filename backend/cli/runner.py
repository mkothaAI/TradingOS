"""Deterministic CLI runner for Phase 10.

Small runner that constructs a deterministic request (or loads JSON) and
invokes the orchestration pipeline, printing the final response as pretty JSON.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from typing import Any, Dict

from backend.schemas.shared import RequestMeta, UniverseStats, SizeInfo, RiskMetrics
from backend.schemas.models_responses import (
    UniverseResponse,
    RiskResponse,
    DecisionResponse,
)
from backend.schemas.decision_models import DecisionItem
from backend.engines.orchestration.assembler import compute_pipeline, build_pipeline_response


def _make_sample_payload() -> Dict[str, Any]:
    meta = RequestMeta(request_id="SAMPLE-REQ-000", as_of_date=date(2024, 1, 15))
    ticker_list = ["AAPL", "MSFT"]

    stats = UniverseStats(count=len(ticker_list), total_market_cap=1000.0, sector_exposures={})
    universe = UniverseResponse(meta=meta, status="OK", universe_list=[], universe_stats=stats, errors=[])

    metrics = RiskMetrics()
    size_info = {t: SizeInfo(allowed_qty=0) for t in ticker_list}
    risk = RiskResponse(meta=meta, status="OK", risk_metrics=metrics, size_info=size_info, errors=[])

    decisions = {t: DecisionItem(ticker=t, decision="NO_TRADE", size_info=None, reason_codes=[], applied_rules=[]) for t in ticker_list}
    decision = DecisionResponse(meta=meta, status="OK", decisions=decisions, errors=[])

    payloads = {"universe": universe, "fundamental": None, "event": None, "risk": risk, "decision": decision}
    return {"meta": meta, "ticker_list": ticker_list, "payloads": payloads, "pipeline_config": {}}


def _serialize_pipeline_result(pipeline_result: Dict[str, Any]) -> Dict[str, Any]:
    """Convert Pydantic models inside pipeline_result into primitives for JSON."""
    def _conv(obj: Any):
        # pydantic models expose `model_dump()` in v2
        if hasattr(obj, "model_dump"):
            return _conv(obj.model_dump())
        if isinstance(obj, dict):
            return {k: _conv(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_conv(v) for v in obj]
        if isinstance(obj, (str, int, float, bool)) or obj is None:
            return obj
        # dates
        if hasattr(obj, "isoformat"):
            try:
                return obj.isoformat()
            except Exception:
                pass
        return str(obj)

    return _conv(pipeline_result)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run deterministic orchestration pipeline")
    parser.add_argument("--input", "-i", help="Path to JSON request file", default=None)
    args = parser.parse_args(argv)

    try:
        if args.input:
            with open(args.input, "r") as fh:
                data = json.load(fh)
            # minimal supported: ignore contents and use sample meta if malformed shape
            meta = RequestMeta(**data.get("meta", {})) if data.get("meta") else None
            if meta is None:
                # fallback to sample but warn
                print("Warning: input missing meta; using sample request", file=sys.stderr)
                request = _make_sample_payload()
            else:
                # Build a very small pipeline by reusing sample payloads but with provided meta
                request = _make_sample_payload()
                request["meta"] = meta
        else:
            request = _make_sample_payload()

        pipeline_result = compute_pipeline(request["meta"], request["ticker_list"], request["payloads"], request.get("pipeline_config", {}))
        # convert pydantic models into primitives and print
        out = _serialize_pipeline_result(pipeline_result)
        print(json.dumps(out, indent=2, sort_keys=True))
        return 0
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}", file=sys.stderr)
        return 3
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
