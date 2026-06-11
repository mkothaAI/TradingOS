from __future__ import annotations
from typing import List, Optional, Dict
from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime, date
from .shared import SizeInfo, SourceLink, ErrorItem, EvidenceContext, FreshnessEnvelope, _ensure_utc_datetime


class TechnicalIndicatorsItem(BaseModel):
    atr: Optional[float] = None
    ma: Optional[Dict[int, float]] = None
    returns: Optional[List[float]] = None
    volatility: Optional[float] = None


class TechnicalSignalsItem(BaseModel):
    ma_cross: Optional[int] = None
    candle_classification: Optional[str] = None
    atr_spike: Optional[bool] = None
    momentum_pass: Optional[bool] = None


class ScheduledEventItem(BaseModel):
    ticker: str
    event_type: str
    event_date: date
    source: Optional[str] = None


class EventFlagsItem(BaseModel):
    earnings_upcoming: bool = False
    blackout: bool = False
    events: Optional[List[ScheduledEventItem]] = None


class FundamentalResultItem(BaseModel):
    fundamental_pass: bool
    reasons: List[str]


class DecisionInputs(BaseModel):
    technical_signals: Dict[str, TechnicalSignalsItem]
    technical_indicators: Optional[Dict[str, TechnicalIndicatorsItem]] = None
    fundamental_results: Dict[str, FundamentalResultItem]
    risk_assessment: Dict[str, SizeInfo]
    event_flags: Dict[str, EventFlagsItem]


class FollowUpTargetKind(str, Enum):
    ADVISORY_AGENT = "advisory_agent"
    SYNTHESIZED_VERDICT = "synthesized_verdict"


class FollowUpAnswerType(str, Enum):
    ADVISORY = "advisory"
    REFUSAL = "refusal"
    NEEDS_REVIEW = "needs_review"


class FollowUpTarget(BaseModel):
    target_kind: FollowUpTargetKind
    target_name: str = Field(min_length=1)
    display_name: Optional[str] = None
    is_authoritative: bool = False
    topic_tags: List[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_authority(self) -> "FollowUpTarget":
        if self.is_authoritative:
            raise ValueError("follow-up targets must remain advisory-only")
        return self


class FollowUpQuestion(BaseModel):
    question_id: str = Field(min_length=1)
    thread_id: Optional[str] = None
    ticker: str = Field(min_length=1)
    target: FollowUpTarget
    question_text: str = Field(min_length=1)
    asked_at: datetime
    as_of_date: date
    requested_by: Optional[str] = None
    evidence_context: EvidenceContext
    follow_up_mode: Optional[str] = None

    @field_validator("asked_at")
    @classmethod
    def _validate_asked_at(cls, value: datetime) -> datetime:
        return _ensure_utc_datetime(value, "asked_at")


class FollowUpAnswer(BaseModel):
    answer_id: str = Field(min_length=1)
    question_id: str = Field(min_length=1)
    ticker: str = Field(min_length=1)
    target: FollowUpTarget
    answer_text: str = Field(min_length=1)
    answer_type: FollowUpAnswerType
    generated_at: datetime
    as_of_date: date
    evidence_context: EvidenceContext
    freshness: FreshnessEnvelope
    supporting_rule_ids: List[str] = Field(default_factory=list)
    follow_up_summary: Optional[str] = None

    @field_validator("generated_at")
    @classmethod
    def _validate_generated_at(cls, value: datetime) -> datetime:
        return _ensure_utc_datetime(value, "generated_at")


class RecommendationBlockType(str, Enum):
    ENTRY = "entry"
    RISK = "risk"
    INVALIDATION = "invalidation"
    MONITORING = "monitoring"


class RecommendationStatus(str, Enum):
    SUPPORTIVE = "supportive"
    CAUTIONARY = "cautionary"
    BLOCKING = "blocking"
    WATCHING = "watching"


class EntryBias(str, Enum):
    LONG = "long"
    SHORT = "short"
    WAIT = "wait"
    NO_ENTRY = "no_entry"


class EntryPlan(BaseModel):
    entry_bias: EntryBias
    timing_window: Optional[str] = None
    capital_allocation: Optional[float] = Field(default=None, ge=0)
    size_plan: Optional[SizeInfo] = None
    entry_conditions: List[str] = Field(default_factory=list)
    entry_triggers: List[str] = Field(default_factory=list)
    entry_rationale: str = Field(min_length=1)
    freshness: FreshnessEnvelope
    evidence_context: EvidenceContext

    @model_validator(mode="after")
    def _validate_entry_conditions(self) -> "EntryPlan":
        if not self.entry_conditions:
            raise ValueError("entry_conditions must be provided")
        return self


class RiskPlan(BaseModel):
    risk_level: str = Field(min_length=1)
    stop_loss: Optional[str] = None
    waiting_time: Optional[str] = None
    hold_time: Optional[str] = None
    capital_at_risk: Optional[float] = Field(default=None, ge=0)
    risk_conditions: List[str] = Field(default_factory=list)
    risk_notes: str = Field(min_length=1)
    freshness: FreshnessEnvelope
    evidence_context: EvidenceContext

    @model_validator(mode="after")
    def _validate_risk_conditions(self) -> "RiskPlan":
        if not self.risk_conditions:
            raise ValueError("risk_conditions must be provided")
        return self


class InvalidationPlan(BaseModel):
    invalidation_level: Optional[str] = None
    invalidation_conditions: List[str] = Field(default_factory=list)
    invalidation_triggers: List[str] = Field(default_factory=list)
    invalidation_message: str = Field(min_length=1)
    reassessment_needed: bool
    freshness: FreshnessEnvelope
    evidence_context: EvidenceContext

    @model_validator(mode="after")
    def _validate_invalidation_conditions(self) -> "InvalidationPlan":
        if not self.invalidation_conditions:
            raise ValueError("invalidation_conditions must be provided")
        return self


class MonitoringPlan(BaseModel):
    monitoring_level: str = Field(min_length=1)
    monitoring_conditions: List[str] = Field(default_factory=list)
    review_frequency: Optional[str] = None
    alert_thresholds: List[str] = Field(default_factory=list)
    watch_notes: str = Field(min_length=1)
    freshness: FreshnessEnvelope
    evidence_context: EvidenceContext

    @model_validator(mode="after")
    def _validate_monitoring_conditions(self) -> "MonitoringPlan":
        if not self.monitoring_conditions:
            raise ValueError("monitoring_conditions must be provided")
        return self


class RecommendationBlock(BaseModel):
    block_id: str = Field(min_length=1)
    block_type: RecommendationBlockType
    headline: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    status: RecommendationStatus
    evidence_context: EvidenceContext
    freshness: FreshnessEnvelope
    entry_plan: Optional[EntryPlan] = None
    risk_plan: Optional[RiskPlan] = None
    invalidation_plan: Optional[InvalidationPlan] = None
    monitoring_plan: Optional[MonitoringPlan] = None
    supporting_rule_ids: List[str] = Field(default_factory=list)
    notes: Optional[str] = None

    @model_validator(mode="after")
    def _validate_plan_presence(self) -> "RecommendationBlock":
        if not any(
            [
                self.entry_plan,
                self.risk_plan,
                self.invalidation_plan,
                self.monitoring_plan,
            ]
        ):
            raise ValueError("at least one plan sub-object must be provided")
        return self


class TickerAnalysisPackage(BaseModel):
    analysis_id: str = Field(min_length=1)
    ticker: str = Field(min_length=1)
    as_of_date: date
    generated_at: datetime
    symbolic_verdict_ref: str = Field(min_length=1)
    evidence_context: EvidenceContext
    freshness: FreshnessEnvelope
    recommendation_blocks: List[RecommendationBlock] = Field(default_factory=list)
    target_context: Optional[FollowUpTarget] = None
    primary_recommendation: Optional[str] = None
    analysis_summary: Optional[str] = None
    confidence_label: Optional[str] = None
    assumption_summary: Optional[str] = None

    @field_validator("generated_at")
    @classmethod
    def _validate_generated_at(cls, value: datetime) -> datetime:
        return _ensure_utc_datetime(value, "generated_at")

    @model_validator(mode="after")
    def _validate_recommendation_blocks(self) -> "TickerAnalysisPackage":
        if not self.recommendation_blocks:
            raise ValueError("recommendation_blocks must be provided")
        return self


class OptionContractType(str, Enum):
    CALL = "call"
    PUT = "put"


class LiquidityLabel(str, Enum):
    THIN = "thin"
    ADEQUATE = "adequate"
    DEEP = "deep"


class SpreadQualityLabel(str, Enum):
    TIGHT = "tight"
    ACCEPTABLE = "acceptable"
    WIDE = "wide"
    UNUSABLE = "unusable"


class OptionContractSnapshot(BaseModel):
    contract_id: str = Field(min_length=1)
    underlying_ticker: str = Field(min_length=1)
    contract_type: OptionContractType
    expiry: date
    strike: float = Field(gt=0)
    exchange: Optional[str] = None
    currency: Optional[str] = None
    last_price: Optional[float] = Field(default=None, ge=0)
    bid: Optional[float] = Field(default=None, ge=0)
    ask: Optional[float] = Field(default=None, ge=0)
    mid_price: Optional[float] = Field(default=None, ge=0)
    intrinsic_value: Optional[float] = Field(default=None, ge=0)
    extrinsic_value: Optional[float] = Field(default=None, ge=0)
    open_interest: Optional[int] = Field(default=None, ge=0)
    volume: Optional[int] = Field(default=None, ge=0)
    contract_size: Optional[int] = Field(default=None, ge=0)
    tradeable: bool = True
    freshness: FreshnessEnvelope
    evidence_context: EvidenceContext

    @model_validator(mode="after")
    def _validate_price_bounds(self) -> "OptionContractSnapshot":
        if self.bid is not None and self.ask is not None and self.bid > self.ask:
            raise ValueError("bid must not exceed ask")
        if self.mid_price is not None and self.bid is not None and self.ask is not None:
            if not (self.bid <= self.mid_price <= self.ask):
                raise ValueError("mid_price must sit between bid and ask when both are present")
        return self


class GreeksSnapshot(BaseModel):
    snapshot_id: str = Field(min_length=1)
    contract_id: str = Field(min_length=1)
    underlying_ticker: str = Field(min_length=1)
    implied_volatility: Optional[float] = Field(default=None, ge=0)
    delta: Optional[float] = Field(default=None, ge=-1, le=1)
    gamma: Optional[float] = Field(default=None, ge=0)
    theta: Optional[float] = None
    vega: Optional[float] = Field(default=None, ge=0)
    rho: Optional[float] = None
    iv_rank: Optional[float] = Field(default=None, ge=0)
    iv_percentile: Optional[float] = Field(default=None, ge=0, le=100)
    directional_bias: Optional[str] = None
    sensitivity_notes: Optional[str] = None
    freshness: FreshnessEnvelope
    evidence_context: EvidenceContext

    @model_validator(mode="after")
    def _validate_metrics_present(self) -> "GreeksSnapshot":
        if not any(
            [
                self.implied_volatility is not None,
                self.delta is not None,
                self.gamma is not None,
                self.theta is not None,
                self.vega is not None,
                self.rho is not None,
                self.iv_rank is not None,
                self.iv_percentile is not None,
            ]
        ):
            raise ValueError("at least one greek or volatility metric must be provided")
        return self


class LiquiditySnapshot(BaseModel):
    snapshot_id: str = Field(min_length=1)
    contract_id: str = Field(min_length=1)
    underlying_ticker: str = Field(min_length=1)
    bid_size: Optional[float] = Field(default=None, ge=0)
    ask_size: Optional[float] = Field(default=None, ge=0)
    spread: Optional[float] = Field(default=None, ge=0)
    spread_pct: Optional[float] = Field(default=None, ge=0)
    open_interest: Optional[int] = Field(default=None, ge=0)
    volume: Optional[int] = Field(default=None, ge=0)
    average_daily_volume: Optional[float] = Field(default=None, ge=0)
    liquidity_label: Optional[LiquidityLabel] = None
    freshness: FreshnessEnvelope
    evidence_context: EvidenceContext

    @model_validator(mode="after")
    def _validate_liquidity_presence(self) -> "LiquiditySnapshot":
        if not any(
            [
                self.bid_size is not None,
                self.ask_size is not None,
                self.spread is not None,
                self.spread_pct is not None,
                self.open_interest is not None,
                self.volume is not None,
                self.average_daily_volume is not None,
                self.liquidity_label is not None,
            ]
        ):
            raise ValueError("at least one liquidity metric must be provided")
        return self


class SpreadQualitySnapshot(BaseModel):
    snapshot_id: str = Field(min_length=1)
    contract_id: str = Field(min_length=1)
    underlying_ticker: str = Field(min_length=1)
    bid: Optional[float] = Field(default=None, ge=0)
    ask: Optional[float] = Field(default=None, ge=0)
    mid_price: Optional[float] = Field(default=None, ge=0)
    spread: Optional[float] = Field(default=None, ge=0)
    spread_pct: Optional[float] = Field(default=None, ge=0)
    slippage_risk: Optional[str] = None
    quality_label: Optional[SpreadQualityLabel] = None
    quality_notes: Optional[str] = None
    freshness: FreshnessEnvelope
    evidence_context: EvidenceContext

    @model_validator(mode="after")
    def _validate_quality_presence(self) -> "SpreadQualitySnapshot":
        if self.bid is not None and self.ask is not None and self.bid > self.ask:
            raise ValueError("bid must not exceed ask")
        if not any(
            [
                self.bid is not None,
                self.ask is not None,
                self.mid_price is not None,
                self.spread is not None,
                self.spread_pct is not None,
                self.quality_label is not None,
            ]
        ):
            raise ValueError("at least one spread-quality field must be provided")
        return self


class OptionsProfile(BaseModel):
    profile_id: str = Field(min_length=1)
    ticker: str = Field(min_length=1)
    as_of_date: date
    generated_at: datetime
    symbolic_verdict_ref: str = Field(min_length=1)
    evidence_context: EvidenceContext
    freshness: FreshnessEnvelope
    contract_snapshots: List[OptionContractSnapshot] = Field(default_factory=list)
    greeks_snapshots: List[GreeksSnapshot] = Field(default_factory=list)
    liquidity_snapshots: List[LiquiditySnapshot] = Field(default_factory=list)
    spread_quality_snapshots: List[SpreadQualitySnapshot] = Field(default_factory=list)
    profile_summary: Optional[str] = None
    thesis_fit: Optional[str] = None
    contract_count: Optional[int] = Field(default=None, ge=0)
    notes: Optional[str] = None

    @field_validator("generated_at")
    @classmethod
    def _validate_generated_at(cls, value: datetime) -> datetime:
        return _ensure_utc_datetime(value, "generated_at")

    @model_validator(mode="after")
    def _validate_option_family(self) -> "OptionsProfile":
        if not self.contract_snapshots:
            raise ValueError("contract_snapshots must be provided")
        contract_ids = {snapshot.contract_id for snapshot in self.contract_snapshots}
        for snapshot in self.greeks_snapshots:
            if snapshot.contract_id not in contract_ids:
                raise ValueError("greeks_snapshots must reference a contract snapshot")
        for snapshot in self.liquidity_snapshots:
            if snapshot.contract_id not in contract_ids:
                raise ValueError("liquidity_snapshots must reference a contract snapshot")
        for snapshot in self.spread_quality_snapshots:
            if snapshot.contract_id not in contract_ids:
                raise ValueError("spread_quality_snapshots must reference a contract snapshot")
        if self.contract_count is not None and self.contract_count != len(self.contract_snapshots):
            raise ValueError("contract_count must match the number of contract_snapshots")
        return self


class PositionSide(str, Enum):
    LONG = "long"
    SHORT = "short"
    FLAT = "flat"


class MonitoringConditionType(str, Enum):
    THESIS_BREAKAGE = "thesis_breakage"
    STOP_LOSS = "stop_loss"
    VOLATILITY_CHANGE = "volatility_change"
    MACRO_SHOCK = "macro_shock"
    OPTIONS_RISK_CHANGE = "options_risk_change"
    OTHER_OBSERVABLE_CONDITION = "other_observable_condition"


class MonitoringStateStatus(str, Enum):
    WATCHING = "watching"
    STABLE = "stable"
    WATCHLIST_WARNING = "watchlist_warning"
    THESIS_AT_RISK = "thesis_at_risk"
    REVIEW_NEEDED = "review_needed"


class ThesisBreakageType(str, Enum):
    THESIS_BREAKAGE = "thesis_breakage"
    STOP_LOSS = "stop_loss"
    VOLATILITY_CHANGE = "volatility_change"
    MACRO_SHOCK = "macro_shock"
    OPTIONS_RISK_CHANGE = "options_risk_change"
    OTHER_OBSERVABLE_CONDITION = "other_observable_condition"


class PostEntryContext(BaseModel):
    context_id: str = Field(min_length=1)
    analysis_id: str = Field(min_length=1)
    ticker: str = Field(min_length=1)
    symbolic_verdict_ref: str = Field(min_length=1)
    entry_timestamp: datetime
    entry_price: Optional[float] = Field(default=None, ge=0)
    position_side: Optional[PositionSide] = None
    planned_hold_time: Optional[str] = None
    capital_at_risk: Optional[float] = Field(default=None, ge=0)
    evidence_context: EvidenceContext
    freshness: FreshnessEnvelope

    @field_validator("entry_timestamp")
    @classmethod
    def _validate_entry_timestamp(cls, value: datetime) -> datetime:
        return _ensure_utc_datetime(value, "entry_timestamp")


class MonitoringCondition(BaseModel):
    condition_id: str = Field(min_length=1)
    condition_type: MonitoringConditionType
    condition_name: str = Field(min_length=1)
    condition_description: str = Field(min_length=1)
    trigger_basis: str = Field(min_length=1)
    threshold: Optional[str] = None
    comparison_operator: Optional[str] = None
    severity_hint: Optional[str] = None
    freshness: FreshnessEnvelope
    evidence_context: EvidenceContext


class MonitoringState(BaseModel):
    state_id: str = Field(min_length=1)
    context_id: str = Field(min_length=1)
    ticker: str = Field(min_length=1)
    symbolic_verdict_ref: str = Field(min_length=1)
    status: MonitoringStateStatus
    last_checked_at: datetime
    active_condition_ids: List[str] = Field(default_factory=list)
    resolved_condition_ids: List[str] = Field(default_factory=list)
    current_conditions: List[MonitoringCondition] = Field(default_factory=list)
    state_summary: Optional[str] = None
    freshness: FreshnessEnvelope
    evidence_context: EvidenceContext

    @field_validator("last_checked_at")
    @classmethod
    def _validate_last_checked_at(cls, value: datetime) -> datetime:
        return _ensure_utc_datetime(value, "last_checked_at")

    @model_validator(mode="after")
    def _validate_condition_alignment(self) -> "MonitoringState":
        if not self.current_conditions:
            raise ValueError("current_conditions must be provided")
        condition_ids = {condition.condition_id for condition in self.current_conditions}
        if len(condition_ids) != len(self.current_conditions):
            raise ValueError("current_conditions must contain unique condition_id values")
        for active_condition_id in self.active_condition_ids:
            if active_condition_id not in condition_ids:
                raise ValueError("active_condition_ids must reference current_conditions")
        if set(self.active_condition_ids).intersection(self.resolved_condition_ids):
            raise ValueError("active_condition_ids and resolved_condition_ids must not overlap")
        return self


class ThesisBreakageEvent(BaseModel):
    event_id: str = Field(min_length=1)
    state_id: str = Field(min_length=1)
    context_id: str = Field(min_length=1)
    ticker: str = Field(min_length=1)
    symbolic_verdict_ref: str = Field(min_length=1)
    condition_id: str = Field(min_length=1)
    breakage_type: ThesisBreakageType
    observed_at: datetime
    evidence_context: EvidenceContext
    freshness: FreshnessEnvelope
    summary: Optional[str] = None
    requires_reassessment: bool

    @field_validator("observed_at")
    @classmethod
    def _validate_observed_at(cls, value: datetime) -> datetime:
        return _ensure_utc_datetime(value, "observed_at")


class AlertSourceKind(str, Enum):
    MONITORING_STATE = "monitoring_state"
    THESIS_BREAKAGE_EVENT = "thesis_breakage_event"
    RECOMMENDATION_BLOCK = "recommendation_block"
    OTHER_DETERMINISTIC_SOURCE = "other_deterministic_source"


class AlertSeverityCode(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertTriggerType(str, Enum):
    THRESHOLD_BREACH = "threshold_breach"
    CONDITION_ENTERED = "condition_entered"
    CONDITION_CROSSED = "condition_crossed"
    STATE_CHANGED = "state_changed"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"
    OTHER_TRIGGER = "other_trigger"


class AlertSeverity(BaseModel):
    severity_code: AlertSeverityCode
    severity_label: str = Field(min_length=1)
    severity_rank: Optional[int] = Field(default=None, ge=0)
    escalation_needed: bool = False
    freshness: FreshnessEnvelope


class AlertTrigger(BaseModel):
    trigger_id: str = Field(min_length=1)
    condition_id: str = Field(min_length=1)
    trigger_type: AlertTriggerType
    trigger_basis: str = Field(min_length=1)
    trigger_value: Optional[str] = None
    threshold: Optional[str] = None
    comparison_operator: Optional[str] = None
    evidence_context: EvidenceContext
    freshness: FreshnessEnvelope


class AlertRoutingHint(BaseModel):
    hint_id: str = Field(min_length=1)
    priority: Optional[int] = Field(default=None, ge=0)
    audience: Optional[str] = None
    urgency: Optional[str] = None
    dedupe_key: Optional[str] = None
    suppression_hint: Optional[str] = None
    display_hint: Optional[str] = None
    freshness: Optional[FreshnessEnvelope] = None


class AlertEvent(BaseModel):
    alert_id: str = Field(min_length=1)
    ticker: str = Field(min_length=1)
    symbolic_verdict_ref: str = Field(min_length=1)
    source_kind: AlertSourceKind
    source_id: str = Field(min_length=1)
    alert_type: str = Field(min_length=1)
    severity: AlertSeverity
    trigger: AlertTrigger
    routing_hint: Optional[AlertRoutingHint] = None
    summary: str = Field(min_length=1)
    observed_at: datetime
    evidence_context: EvidenceContext
    freshness: FreshnessEnvelope
    requires_review: bool

    @field_validator("observed_at")
    @classmethod
    def _validate_observed_at(cls, value: datetime) -> datetime:
        return _ensure_utc_datetime(value, "observed_at")


class DecisionItem(BaseModel):
    ticker: str
    decision: str
    size_info: Optional[SizeInfo] = None
    reason_codes: List[str]
    applied_rules: List[str]


class ExplanationItem(BaseModel):
    explanation_text: str
    source_links: List[SourceLink]


class AuditEntry(BaseModel):
    run_id: str
    request_id: str
    timestamp: datetime
    as_of_date: date
    engine_versions: Dict[str, str]
    inputs: Optional[Dict] = None
    decisions: Dict[str, DecisionItem]
    errors: List[ErrorItem]
    duration_ms: int
