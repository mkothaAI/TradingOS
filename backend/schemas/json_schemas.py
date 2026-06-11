"""Simple JSON Schema generator from Pydantic models for Phase 1.

Writes JSON schema files into backend/schemas/json/ when run.
"""
from pathlib import Path
import json
from .shared import RequestMeta, TickerMetadata, PriceBar, FreshnessEnvelope, EvidenceContext
from .models_requests import UniverseRequest, TechnicalRequest
from .decision_models import (
    FollowUpTarget,
    FollowUpQuestion,
    FollowUpAnswer,
    RecommendationBlock,
    TickerAnalysisPackage,
    OptionContractSnapshot,
    GreeksSnapshot,
    LiquiditySnapshot,
    SpreadQualitySnapshot,
    OptionsProfile,
    PostEntryContext,
    MonitoringCondition,
    MonitoringState,
    ThesisBreakageEvent,
    AlertSeverity,
    AlertTrigger,
    AlertRoutingHint,
    AlertEvent,
)


OUT_DIR = Path(__file__).resolve().parent / 'json'
OUT_DIR.mkdir(exist_ok=True)


def dump_schema(model, name: str):
    schema = model.model_json_schema()
    p = OUT_DIR / f"{name}.json"
    p.write_text(json.dumps(schema, indent=2))
    return p


def generate_all():
    paths = []
    paths.append(dump_schema(UniverseRequest, 'universe_request'))
    paths.append(dump_schema(TechnicalRequest, 'technical_request'))
    paths.append(dump_schema(RequestMeta, 'request_meta'))
    paths.append(dump_schema(TickerMetadata, 'ticker_metadata'))
    paths.append(dump_schema(PriceBar, 'price_bar'))
    paths.append(dump_schema(FreshnessEnvelope, 'freshness_envelope'))
    paths.append(dump_schema(EvidenceContext, 'evidence_context'))
    paths.append(dump_schema(FollowUpTarget, 'follow_up_target'))
    paths.append(dump_schema(FollowUpQuestion, 'follow_up_question'))
    paths.append(dump_schema(FollowUpAnswer, 'follow_up_answer'))
    paths.append(dump_schema(RecommendationBlock, 'recommendation_block'))
    paths.append(dump_schema(TickerAnalysisPackage, 'ticker_analysis_package'))
    paths.append(dump_schema(OptionContractSnapshot, 'option_contract_snapshot'))
    paths.append(dump_schema(GreeksSnapshot, 'greeks_snapshot'))
    paths.append(dump_schema(LiquiditySnapshot, 'liquidity_snapshot'))
    paths.append(dump_schema(SpreadQualitySnapshot, 'spread_quality_snapshot'))
    paths.append(dump_schema(OptionsProfile, 'options_profile'))
    paths.append(dump_schema(PostEntryContext, 'post_entry_context'))
    paths.append(dump_schema(MonitoringCondition, 'monitoring_condition'))
    paths.append(dump_schema(MonitoringState, 'monitoring_state'))
    paths.append(dump_schema(ThesisBreakageEvent, 'thesis_breakage_event'))
    paths.append(dump_schema(AlertSeverity, 'alert_severity'))
    paths.append(dump_schema(AlertTrigger, 'alert_trigger'))
    paths.append(dump_schema(AlertRoutingHint, 'alert_routing_hint'))
    paths.append(dump_schema(AlertEvent, 'alert_event'))
    return paths


if __name__ == '__main__':
    for p in generate_all():
        print('Wrote', p)
