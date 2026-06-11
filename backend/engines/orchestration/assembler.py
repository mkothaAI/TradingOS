"""Thin assembler for Phase 9 orchestration.

Wraps `run_pipeline` and formats PipelineResponse model.
"""
from typing import Dict, Any
from backend.engines.orchestration.calc import run_pipeline
from backend.schemas.models_responses import PipelineResponse


def compute_pipeline(meta, ticker_list, payloads: Dict[str, Any], pipeline_config: Dict[str, Any]):
    return run_pipeline(meta, ticker_list, payloads, pipeline_config)


def build_pipeline_response(pipeline_result: Dict[str, Any]):
    # Convert dict into PipelineResponse Pydantic model
    return PipelineResponse(
        meta=pipeline_result["meta"],
        run_id=pipeline_result["run_id"],
        status=pipeline_result["status"],
        decisions=pipeline_result.get("decisions"),
        event_flags=pipeline_result.get("event_flags"),
        errors=pipeline_result.get("errors", []),
        audit=pipeline_result.get("audit", []),
        timing=pipeline_result.get("timing"),
    )
