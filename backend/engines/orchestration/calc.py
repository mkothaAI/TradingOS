"""Pure orchestration functions for Phase 9.

Consumes typed engine responses only and composes a PipelineResponse summary.
"""
from typing import Dict, Any, List
from datetime import datetime
import uuid
import json

from backend.schemas.shared import RequestMeta, ErrorItem, StepAuditItem
from backend.schemas.models_responses import (
    UniverseResponse,
    FundamentalResponse,
    EventResponse,
    RiskResponse,
    DecisionResponse,
)

KNOWN_PIPELINE_CONFIG_KEYS = {"fail_on_missing_upstream"}


def validate_pipeline_config_keys(config: Dict[str, Any]) -> None:
    if not config:
        return
    unknown = set(config.keys()) - KNOWN_PIPELINE_CONFIG_KEYS
    if unknown:
        raise ValueError(f"Unknown pipeline_config keys: {unknown}")


def _step_summary(name: str, payload: Any, ticker_list: List[str]) -> StepAuditItem:
    """Create a minimal StepAuditItem for a step given its payload (or None)."""
    if payload is None:
        return StepAuditItem(step_name=name, status="SKIPPED", duration_ms=0, error_codes=[], summary={"tickers": len(ticker_list)})

    # payload has `errors` attribute by contract
    errs = getattr(payload, "errors", []) or []
    error_codes = [e.code for e in errs]
    status = "OK" if len(error_codes) == 0 else "ERROR"
    summary = {"tickers": len(ticker_list), "errors": len(error_codes)}
    return StepAuditItem(step_name=name, status=status, duration_ms=0, error_codes=error_codes, summary=summary)


def compute_run_id(meta: RequestMeta, ticker_list: List[str], pipeline_config: Dict[str, Any]) -> str:
    # deterministic UUIDv5 over canonical string
    canonical = json.dumps(pipeline_config or {}, sort_keys=True)
    name = f"{meta.request_id}|{meta.as_of_date.isoformat()}|{','.join(ticker_list)}|{canonical}"
    return str(uuid.uuid5(uuid.NAMESPACE_URL, name))


def run_pipeline(meta: RequestMeta, ticker_list: List[str], payloads: Dict[str, Any], pipeline_config: Dict[str, Any]) -> Dict[str, Any]:
    """Run a narrow orchestration that consumes typed engine responses only.

    Returns a dict matching PipelineResponse fields (not a Pydantic model).
    """
    validate_pipeline_config_keys(pipeline_config)

    # required payloads in v1
    required = {"universe", "risk", "decision"}

    errors: List[ErrorItem] = []
    audit: List[StepAuditItem] = []

    # fixed deterministic order
    steps = ["universe", "fundamental", "event", "risk", "decision"]

    # check required presence
    # If a required key is present but its value is explicitly None, treat as assembler/engine failure
    explicit_none = [s for s in required if s in payloads and payloads.get(s) is None]
    if explicit_none:
        raise Exception(f"Upstream payloads present but None for steps: {explicit_none}")

    missing_required = [s for s in required if s not in payloads]
    if missing_required and pipeline_config.get("fail_on_missing_upstream", True):
        for m in missing_required:
            errors.append(ErrorItem(code=f"{m.upper()}_MISSING", message=f"Missing required upstream payload: {m}"))

    # Build audit entries in fixed order
    for step in steps:
        payload = payloads.get(step)
        audit_item = _step_summary(step.capitalize(), payload, ticker_list)
        audit.append(audit_item)
        # propagate engine errors
        if payload is not None:
            errs = getattr(payload, "errors", []) or []
            for e in errs:
                errors.append(e)

    run_id = compute_run_id(meta, ticker_list, pipeline_config)

    status = "OK"
    if errors:
        status = "ERROR"

    result: Dict[str, Any] = {
        "meta": meta,
        "run_id": run_id,
        "status": status,
        "decisions": None,
        "event_flags": None,
        "errors": errors,
        "audit": audit,
        "timing": {"total_ms": 0},
    }

    # forward Decisions and Event flags if present
    if payloads.get("decision") is not None:
        result["decisions"] = getattr(payloads.get("decision"), "decisions", None)
    if payloads.get("event") is not None:
        result["event_flags"] = getattr(payloads.get("event"), "event_flags", None)

    return result
