from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Sequence

from backend.schemas import (
    AlertEvent,
    AlertRoutingHint,
    AlertSeverity,
    AlertTrigger,
    FollowUpAnswer,
    FollowUpQuestion,
    MonitoringState,
    OptionsProfile,
    RecommendationBlock,
)


def _freshness_label_text(freshness: Any) -> str:
    label = getattr(freshness, "freshness_label", None)
    return str(getattr(label, "value", label) or "unknown")


def _evidence_summary_text(evidence_context: Any) -> str:
    provenance_summary = getattr(evidence_context, "provenance_summary", None)
    evidence_ids = getattr(evidence_context, "evidence_ids", None) or ()
    if provenance_summary:
        return str(provenance_summary)
    if evidence_ids:
        return f"{len(tuple(evidence_ids))} evidence reference(s)"
    return "evidence available"


@dataclass(frozen=True)
class DashboardSummaryCard:
    label: str
    value: str
    detail: str | None = None
    status: str | None = None
    updated_at: str | None = None


@dataclass(frozen=True)
class DashboardFollowUpQuestionProjection:
    question_id: str
    ticker: str
    target_name: str
    question_text: str
    asked_at: str
    as_of_date: str
    freshness_label: str
    evidence_summary: str
    follow_up_mode: str | None = None


@dataclass(frozen=True)
class DashboardFollowUpAnswerProjection:
    answer_id: str
    question_id: str
    ticker: str
    target_name: str
    answer_type: str
    answer_text: str
    generated_at: str
    as_of_date: str
    freshness_label: str
    evidence_summary: str
    supporting_rule_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class DashboardRecommendationBlockProjection:
    block_id: str
    ticker: str
    block_type: str
    headline: str
    summary: str
    status: str
    freshness_label: str
    evidence_summary: str
    plan_kinds: tuple[str, ...] = ()


@dataclass(frozen=True)
class DashboardOptionsProfileProjection:
    profile_id: str
    ticker: str
    as_of_date: str
    generated_at: str
    symbolic_verdict_ref: str
    contract_count: int
    freshness_label: str
    evidence_summary: str
    has_greeks: bool
    has_liquidity: bool
    has_spread_quality: bool


@dataclass(frozen=True)
class DashboardMonitoringStateProjection:
    state_id: str
    context_id: str
    ticker: str
    symbolic_verdict_ref: str
    status: str
    last_checked_at: str
    current_condition_ids: tuple[str, ...]
    active_condition_ids: tuple[str, ...]
    resolved_condition_ids: tuple[str, ...]
    state_summary: str | None
    freshness_label: str
    evidence_summary: str


@dataclass(frozen=True)
class DashboardAlertEventProjection:
    alert_id: str
    ticker: str
    symbolic_verdict_ref: str
    source_kind: str
    source_id: str
    alert_type: str
    severity_code: str
    severity_label: str
    trigger_type: str
    trigger_basis: str
    observed_at: str
    summary: str
    requires_review: bool
    freshness_label: str
    evidence_summary: str
    routing_priority: int | None = None
    routing_audience: str | None = None


@dataclass(frozen=True)
class DashboardProjectionBundle:
    follow_up_questions: tuple[DashboardFollowUpQuestionProjection, ...] = ()
    follow_up_answers: tuple[DashboardFollowUpAnswerProjection, ...] = ()
    recommendation_blocks: tuple[DashboardRecommendationBlockProjection, ...] = ()
    options_profiles: tuple[DashboardOptionsProfileProjection, ...] = ()
    monitoring_states: tuple[DashboardMonitoringStateProjection, ...] = ()
    alert_events: tuple[DashboardAlertEventProjection, ...] = ()


def project_follow_up_question(question: FollowUpQuestion) -> DashboardFollowUpQuestionProjection:
    return DashboardFollowUpQuestionProjection(
        question_id=question.question_id,
        ticker=question.ticker,
        target_name=question.target.target_name,
        question_text=question.question_text,
        asked_at=question.asked_at.isoformat(),
        as_of_date=question.as_of_date.isoformat(),
        freshness_label=_freshness_label_text(question.evidence_context.freshness),
        evidence_summary=_evidence_summary_text(question.evidence_context),
        follow_up_mode=question.follow_up_mode,
    )


def project_follow_up_answer(answer: FollowUpAnswer) -> DashboardFollowUpAnswerProjection:
    return DashboardFollowUpAnswerProjection(
        answer_id=answer.answer_id,
        question_id=answer.question_id,
        ticker=answer.ticker,
        target_name=answer.target.target_name,
        answer_type=str(answer.answer_type.value),
        answer_text=answer.answer_text,
        generated_at=answer.generated_at.isoformat(),
        as_of_date=answer.as_of_date.isoformat(),
        freshness_label=_freshness_label_text(answer.freshness),
        evidence_summary=_evidence_summary_text(answer.evidence_context),
        supporting_rule_ids=tuple(answer.supporting_rule_ids),
    )


def project_recommendation_block(block: RecommendationBlock) -> DashboardRecommendationBlockProjection:
    plan_kinds = tuple(
        plan_kind
        for plan_kind, plan in (
            ("entry", block.entry_plan),
            ("risk", block.risk_plan),
            ("invalidation", block.invalidation_plan),
            ("monitoring", block.monitoring_plan),
        )
        if plan is not None
    )
    return DashboardRecommendationBlockProjection(
        block_id=block.block_id,
        ticker=block.evidence_context.ticker,
        block_type=str(block.block_type.value),
        headline=block.headline,
        summary=block.summary,
        status=str(block.status.value),
        freshness_label=_freshness_label_text(block.freshness),
        evidence_summary=_evidence_summary_text(block.evidence_context),
        plan_kinds=plan_kinds,
    )


def project_options_profile(profile: OptionsProfile) -> DashboardOptionsProfileProjection:
    return DashboardOptionsProfileProjection(
        profile_id=profile.profile_id,
        ticker=profile.ticker,
        as_of_date=profile.as_of_date.isoformat(),
        generated_at=profile.generated_at.isoformat(),
        symbolic_verdict_ref=profile.symbolic_verdict_ref,
        contract_count=int(profile.contract_count or len(profile.contract_snapshots)),
        freshness_label=_freshness_label_text(profile.freshness),
        evidence_summary=_evidence_summary_text(profile.evidence_context),
        has_greeks=bool(profile.greeks_snapshots),
        has_liquidity=bool(profile.liquidity_snapshots),
        has_spread_quality=bool(profile.spread_quality_snapshots),
    )


def project_monitoring_state(state: MonitoringState) -> DashboardMonitoringStateProjection:
    return DashboardMonitoringStateProjection(
        state_id=state.state_id,
        context_id=state.context_id,
        ticker=state.ticker,
        symbolic_verdict_ref=state.symbolic_verdict_ref,
        status=str(state.status.value),
        last_checked_at=state.last_checked_at.isoformat(),
        current_condition_ids=tuple(condition.condition_id for condition in state.current_conditions),
        active_condition_ids=tuple(state.active_condition_ids),
        resolved_condition_ids=tuple(state.resolved_condition_ids),
        state_summary=state.state_summary,
        freshness_label=_freshness_label_text(state.freshness),
        evidence_summary=_evidence_summary_text(state.evidence_context),
    )


def project_alert_event(alert_event: AlertEvent) -> DashboardAlertEventProjection:
    routing_hint: AlertRoutingHint | None = alert_event.routing_hint
    severity: AlertSeverity = alert_event.severity
    trigger: AlertTrigger = alert_event.trigger
    return DashboardAlertEventProjection(
        alert_id=alert_event.alert_id,
        ticker=alert_event.ticker,
        symbolic_verdict_ref=alert_event.symbolic_verdict_ref,
        source_kind=str(alert_event.source_kind.value),
        source_id=alert_event.source_id,
        alert_type=alert_event.alert_type,
        severity_code=str(severity.severity_code.value),
        severity_label=severity.severity_label,
        trigger_type=str(trigger.trigger_type.value),
        trigger_basis=trigger.trigger_basis,
        observed_at=alert_event.observed_at.isoformat(),
        summary=alert_event.summary,
        requires_review=alert_event.requires_review,
        freshness_label=_freshness_label_text(alert_event.freshness),
        evidence_summary=_evidence_summary_text(alert_event.evidence_context),
        routing_priority=getattr(routing_hint, "priority", None),
        routing_audience=getattr(routing_hint, "audience", None),
    )


def build_dashboard_projection_bundle(
    *,
    follow_up_questions: Sequence[FollowUpQuestion] | None = None,
    follow_up_answers: Sequence[FollowUpAnswer] | None = None,
    recommendation_blocks: Sequence[RecommendationBlock] | None = None,
    options_profiles: Sequence[OptionsProfile] | None = None,
    monitoring_states: Sequence[MonitoringState] | None = None,
    alert_events: Sequence[AlertEvent] | None = None,
) -> DashboardProjectionBundle:
    return DashboardProjectionBundle(
        follow_up_questions=tuple(project_follow_up_question(item) for item in follow_up_questions or ()),
        follow_up_answers=tuple(project_follow_up_answer(item) for item in follow_up_answers or ()),
        recommendation_blocks=tuple(project_recommendation_block(item) for item in recommendation_blocks or ()),
        options_profiles=tuple(project_options_profile(item) for item in options_profiles or ()),
        monitoring_states=tuple(project_monitoring_state(item) for item in monitoring_states or ()),
        alert_events=tuple(project_alert_event(item) for item in alert_events or ()),
    )


@dataclass(frozen=True)
class ProviderStatusRow:
    provider_name: str
    capability: str
    health_status: str | None
    eligibility_code: str
    eligibility_state: str
    raw_count: int
    normalized_count: int
    total_count: int
    last_error_code: str | None
    updated_at: str | None
    row_severity: str
    operator_summary: str
    evidence_recency: str


@dataclass(frozen=True)
class EvidenceTimelineItem:
    provider_name: str
    capability: str
    raw_count: int
    normalized_count: int
    total_count: int
    oldest_fetched_at: str | None
    newest_fetched_at: str | None
    symbols: tuple[str, ...]
    stages: tuple[tuple[str, str, str], ...]


@dataclass(frozen=True)
class QuoteWatchSignal:
    label: str
    value: str
    detail: str | None = None
    status: str | None = None


@dataclass(frozen=True)
class QuoteWatchItem:
    symbol: str
    last_price: float | None
    provider_name: str
    source_name: str
    last_update_at: str
    last_successful_update_at: str | None
    stream_status: str
    feed_status: str
    operator_status: str
    recovery_copy: str
    recovery_detail: str
    transition_note: str
    freshness_label: str
    row_severity: str
    row_priority: int
    watch_status: str
    stale: bool
    last_error: str | None
    reconnect_attempts: int
    reconnect_backoff_seconds: float | None
    display_order: int
    is_primary: bool


@dataclass(frozen=True)
class QuoteWatchPanel:
    watched_symbol: str
    provider_name: str
    source_name: str
    last_price: float | None
    last_update_at: str
    last_successful_update_at: str | None
    stream_status: str
    feed_status: str
    operator_status: str
    recovery_copy: str
    watch_status: str
    stale: bool
    bid_available: bool
    ask_available: bool
    last_error: str | None
    reconnect_attempts: int
    reconnect_backoff_seconds: float | None
    note: str
    signals: tuple[QuoteWatchSignal, ...]
    watchlist_items: tuple[QuoteWatchItem, ...] = ()


@dataclass(frozen=True)
class CompositionResultPanel:
    provider_name: str
    capability: str
    status: str
    selected_provider: str | None
    fallback_group: str | None
    error_type: str | None
    error_message: str | None
    priority: int | None = None


@dataclass(frozen=True)
class CompositionFallbackItem:
    provider_name: str
    capability: str
    status: str
    selected_provider: str | None
    fallback_group: str | None
    priority: int | None
    error_type: str | None
    error_message: str | None


@dataclass(frozen=True)
class CompositionFallbackPanel:
    overall_status: str
    fallback_policy: str
    attempted_provider_names: tuple[str, ...]
    selected_provider_names: tuple[str, ...]
    failed_provider_names: tuple[str, ...]
    skipped_provider_names: tuple[str, ...]
    items: tuple[CompositionFallbackItem, ...]


@dataclass(frozen=True)
class CompositionOutcomeDetailItem:
    label: str
    value: str
    detail: str | None = None
    status: str | None = None


@dataclass(frozen=True)
class CompositionOutcomeDetailSection:
    title: str
    items: tuple[CompositionOutcomeDetailItem, ...]


@dataclass(frozen=True)
class CompositionOutcomeDetailPanel:
    overall_status: str
    fallback_policy: str
    selection_reason: str
    selected_provider_names: tuple[str, ...]
    attempted_provider_names: tuple[str, ...]
    failed_provider_names: tuple[str, ...]
    skipped_provider_names: tuple[str, ...]
    sections: tuple[CompositionOutcomeDetailSection, ...]


@dataclass(frozen=True)
class DiagnosticsDrawerItem:
    label: str
    value: str
    detail: str | None = None
    status: str | None = None


@dataclass(frozen=True)
class DiagnosticsDrawerSection:
    title: str
    items: tuple[DiagnosticsDrawerItem, ...]


def _sorted_provider_capabilities(
    health_summary: dict[str, dict[str, Any]],
    evidence_summary: dict[str, dict[str, Any]],
    eligibility_view: dict[str, dict[str, Any]],
) -> list[tuple[str, str]]:
    provider_names = set(evidence_summary.keys()) | set(eligibility_view.keys())
    for capability_bucket in health_summary.values():
        provider_names.update(capability_bucket.get("providers", {}).keys())

    provider_capabilities: set[tuple[str, str]] = set()
    for provider_name in provider_names:
        capability_names = set(evidence_summary.get(provider_name, {}).keys()) | set(eligibility_view.get(provider_name, {}).keys())
        for capability, capability_bucket in health_summary.items():
            if provider_name in capability_bucket.get("providers", {}):
                capability_names.add(capability)
        for capability in capability_names:
            provider_capabilities.add((provider_name, capability))

    return sorted(provider_capabilities, key=lambda item: (item[0], item[1]))


def build_provider_status_rows(
    health_summary: dict[str, dict[str, Any]],
    evidence_summary: dict[str, dict[str, Any]],
    eligibility_view: dict[str, dict[str, Any]],
) -> list[ProviderStatusRow]:
    rows: list[ProviderStatusRow] = []
    for provider_name, capability in _sorted_provider_capabilities(health_summary, evidence_summary, eligibility_view):
        health_bucket = health_summary.get(capability, {}).get("providers", {}).get(provider_name)
        evidence_bucket = evidence_summary.get(provider_name, {}).get(capability)
        verdict = eligibility_view.get(provider_name, {}).get(capability)
        health_status = str(health_bucket.get("status") or "unknown") if health_bucket else "unknown"
        eligibility_state = str(getattr(verdict, "eligibility", "unknown"))
        raw_count = int(evidence_bucket.get("raw_count") or 0) if evidence_bucket else 0
        normalized_count = int(evidence_bucket.get("normalized_count") or 0) if evidence_bucket else 0
        newest_fetched_at = str(evidence_bucket.get("newest_fetched_at") or "") if evidence_bucket else ""
        last_error_code = health_bucket.get("last_error_code") if health_bucket else None
        if health_status.lower() in {"down", "disabled", "terminal"}:
            row_severity = "critical"
        elif health_status.lower() == "degraded" or eligibility_state == "not_eligible" or raw_count == 0 or normalized_count == 0 or last_error_code:
            row_severity = "warning"
        else:
            row_severity = "healthy"

        if row_severity == "critical":
            operator_summary = f"{health_status} · {eligibility_state} · review immediately"
        elif row_severity == "warning":
            operator_summary = f"{health_status} · {eligibility_state} · check evidence"
        else:
            operator_summary = f"{health_status} · {eligibility_state} · evidence current"

        evidence_recency = f"latest evidence {newest_fetched_at}" if newest_fetched_at else "no evidence yet"
        rows.append(
            ProviderStatusRow(
                provider_name=provider_name,
                capability=capability,
                health_status=health_bucket.get("status") if health_bucket else None,
                eligibility_code=getattr(verdict, "classification_code", "UNCLASSIFIED"),
                eligibility_state=getattr(verdict, "eligibility", "unknown"),
                raw_count=raw_count,
                normalized_count=normalized_count,
                total_count=int(evidence_bucket.get("total_count") or 0) if evidence_bucket else 0,
                last_error_code=last_error_code,
                updated_at=health_bucket.get("updated_at") if health_bucket else None,
                row_severity=row_severity,
                operator_summary=operator_summary,
                evidence_recency=evidence_recency,
            )
        )
    return rows


def build_evidence_timeline_items(evidence_summary: dict[str, dict[str, Any]]) -> list[EvidenceTimelineItem]:
    items: list[EvidenceTimelineItem] = []
    for provider_name in sorted(evidence_summary.keys()):
        for capability in sorted(evidence_summary[provider_name].keys()):
            bucket = evidence_summary[provider_name][capability]
            raw_count = int(bucket.get("raw_count") or 0)
            normalized_count = int(bucket.get("normalized_count") or 0)
            total_count = int(bucket.get("total_count") or 0)
            provenance_ready = raw_count > 0 and normalized_count > 0
            items.append(
                EvidenceTimelineItem(
                    provider_name=provider_name,
                    capability=capability,
                    raw_count=raw_count,
                    normalized_count=normalized_count,
                    total_count=total_count,
                    oldest_fetched_at=bucket.get("oldest_fetched_at"),
                    newest_fetched_at=bucket.get("newest_fetched_at"),
                    symbols=tuple(bucket.get("symbols") or ()),
                    stages=(
                        (
                            "raw_evidence_written",
                            "complete" if raw_count > 0 else "empty",
                            f"{raw_count} raw record(s)",
                        ),
                        (
                            "normalized_evidence_linked",
                            "complete" if normalized_count > 0 else "pending",
                            f"{normalized_count} normalized record(s)",
                        ),
                        (
                            "artifact_created_and_verified",
                            "complete" if provenance_ready else "pending",
                            "backend artifact available" if provenance_ready else "awaiting raw and normalized evidence",
                        ),
                        (
                            "provenance_chain_available",
                            "complete" if provenance_ready else "pending",
                            "linked raw/normalized chain" if provenance_ready else "chain not yet available",
                        ),
                    ),
                )
            )
    return items


def _quote_value(quote_snapshot: Any, field_name: str, default: Any = None) -> Any:
    if quote_snapshot is None:
        return default
    if isinstance(quote_snapshot, dict):
        return quote_snapshot.get(field_name, default)
    return getattr(quote_snapshot, field_name, default)


def _build_quote_watch_item(
    quote_snapshot: Any | None,
    *,
    symbol: str | None = None,
    stream_status: str = "snapshot_ready",
    feed_status: str | None = None,
    watch_status: str = "placeholder",
    stale: bool = False,
    last_successful_update_at: Any | None = None,
    last_error: str | None = None,
    reconnect_attempts: int = 0,
    reconnect_backoff_seconds: float | None = None,
    display_order: int = 0,
    is_primary: bool = False,
) -> QuoteWatchItem:
    meta = _quote_value(quote_snapshot, "meta")
    symbol_value = str(symbol or _quote_value(quote_snapshot, "symbol") or "")
    provider_name = str(_quote_value(meta, "provider_name") or "twelvedata")
    source_name = str(_quote_value(meta, "source_id") or symbol_value or provider_name)
    as_of = _quote_value(quote_snapshot, "as_of")
    last_price = _quote_value(quote_snapshot, "last")

    raw_last_update_at = as_of.isoformat() if hasattr(as_of, "isoformat") else str(as_of or "")
    last_successful_update_at_value = last_successful_update_at
    if hasattr(last_successful_update_at_value, "isoformat"):
        last_successful_update_at_value = last_successful_update_at_value.isoformat()
    elif last_successful_update_at_value is not None:
        last_successful_update_at_value = str(last_successful_update_at_value)
    live_stream = str(stream_status).lower() in {"live", "streaming", "connected"} or str(watch_status).lower() in {"live", "watching"}
    feed_status_value = str(feed_status or ("stale" if stale else ("live" if live_stream else stream_status or "snapshot_ready")))
    display_last_update_at = raw_last_update_at
    if feed_status_value in {"reconnecting", "disconnected", "warming_up"}:
        display_last_update_at = last_successful_update_at_value or "n/a"
    elif stale and last_successful_update_at_value:
        display_last_update_at = last_successful_update_at_value

    if last_successful_update_at_value is None and feed_status_value in {"reconnecting", "disconnected", "warming_up"}:
        panel_last_successful_update_at = None
    else:
        panel_last_successful_update_at = last_successful_update_at_value or raw_last_update_at or None

    operator_status, recovery_copy = _format_quote_watch_status(
        feed_status=feed_status_value,
        stale=bool(stale),
        last_successful_update_at=last_successful_update_at_value,
        last_error=last_error,
        reconnect_attempts=int(reconnect_attempts or 0),
        reconnect_backoff_seconds=reconnect_backoff_seconds,
    )
    transition_note, recovery_detail = _quote_watch_recovery_detail(
        feed_status=feed_status_value,
        stale=bool(stale),
        last_successful_update_at=last_successful_update_at_value,
        last_error=last_error,
        reconnect_attempts=int(reconnect_attempts or 0),
        reconnect_backoff_seconds=reconnect_backoff_seconds,
    )
    freshness_label, row_severity, row_priority = _quote_watch_row_profile(
        feed_status=feed_status_value,
        stale=bool(stale),
        last_successful_update_at=last_successful_update_at_value,
        reconnect_attempts=int(reconnect_attempts or 0),
        is_primary=bool(is_primary),
    )

    return QuoteWatchItem(
        symbol=symbol_value or "n/a",
        last_price=last_price if isinstance(last_price, (int, float)) else None,
        provider_name=provider_name,
        source_name=source_name,
        last_update_at=display_last_update_at or "n/a",
        last_successful_update_at=panel_last_successful_update_at,
        stream_status=stream_status,
        feed_status=feed_status_value,
        operator_status=operator_status,
        recovery_copy=recovery_copy,
        recovery_detail=recovery_detail,
        transition_note=transition_note,
        freshness_label=freshness_label,
        row_severity=row_severity,
        row_priority=row_priority,
        watch_status=watch_status,
        stale=bool(stale),
        last_error=last_error,
        reconnect_attempts=int(reconnect_attempts or 0),
        reconnect_backoff_seconds=reconnect_backoff_seconds,
        display_order=int(display_order),
        is_primary=bool(is_primary),
    )


def build_quote_watch_item(
    quote_snapshot: Any | None,
    *,
    symbol: str | None = None,
    stream_status: str = "snapshot_ready",
    feed_status: str | None = None,
    watch_status: str = "placeholder",
    stale: bool = False,
    last_successful_update_at: Any | None = None,
    last_error: str | None = None,
    reconnect_attempts: int = 0,
    reconnect_backoff_seconds: float | None = None,
    display_order: int = 0,
    is_primary: bool = False,
) -> QuoteWatchItem:
    return _build_quote_watch_item(
        quote_snapshot,
        symbol=symbol,
        stream_status=stream_status,
        feed_status=feed_status,
        watch_status=watch_status,
        stale=stale,
        last_successful_update_at=last_successful_update_at,
        last_error=last_error,
        reconnect_attempts=reconnect_attempts,
        reconnect_backoff_seconds=reconnect_backoff_seconds,
        display_order=display_order,
        is_primary=is_primary,
    )


def _quote_watch_row_profile(
    *,
    feed_status: str,
    stale: bool,
    last_successful_update_at: str | None,
    reconnect_attempts: int,
    is_primary: bool,
) -> tuple[str, str, int]:
    normalized_feed_status = str(feed_status or "snapshot_ready").lower()
    if normalized_feed_status == "live":
        if stale:
            return "stale", "warning", (0 if is_primary else 100) + 30
        if reconnect_attempts > 0:
            return "recovering", "warning", (0 if is_primary else 100) + 20
        return "fresh", "healthy", (0 if is_primary else 100) + 40

    if normalized_feed_status == "reconnecting":
        if last_successful_update_at is None:
            return "warming up", "critical", (0 if is_primary else 100) + 0
        return "recovering", "warning", (0 if is_primary else 100) + 15

    if normalized_feed_status == "disconnected":
        if last_successful_update_at is None:
            return "disconnected", "critical", (0 if is_primary else 100) + 5
        return "disconnected", "critical", (0 if is_primary else 100) + 10

    if stale:
        return "stale", "warning", (0 if is_primary else 100) + 25

    if normalized_feed_status == "snapshot_ready":
        return "snapshot", "neutral", (0 if is_primary else 100) + 50

    return normalized_feed_status.replace("_", " "), "neutral", (0 if is_primary else 100) + 60


def _quote_watch_recovery_detail(
    *,
    feed_status: str,
    stale: bool,
    last_successful_update_at: str | None,
    last_error: str | None,
    reconnect_attempts: int,
    reconnect_backoff_seconds: float | None,
) -> tuple[str, str]:
    normalized_feed_status = str(feed_status or "snapshot_ready").lower()
    success_at = last_successful_update_at or "n/a"
    retry_text = f"retry in {reconnect_backoff_seconds:g}s" if reconnect_backoff_seconds is not None else "retrying"
    error_text = f"last error: {last_error}" if last_error else "no recent error"

    if normalized_feed_status == "live":
        if stale:
            return "recently stale", f"last success {success_at}; {error_text}"
        if reconnect_attempts > 0:
            return f"recovered after {reconnect_attempts} retry(s)", f"last success {success_at}; {retry_text}"
        return "fresh", f"last success {success_at}; {error_text}"

    if normalized_feed_status == "reconnecting":
        if last_successful_update_at is None:
            return "waiting for first live tick", error_text
        return "recovering", f"last success {success_at}; {retry_text}"

    if normalized_feed_status == "disconnected":
        if last_successful_update_at is None:
            return "disconnected", error_text
        return "disconnected", f"last success {success_at}; {error_text}"

    if stale:
        return "recently stale", f"last success {success_at}; {error_text}"

    if normalized_feed_status == "warming_up":
        return "waiting for first live tick", error_text

    return normalized_feed_status.replace("_", " "), f"last success {success_at}; {error_text}"


def _format_quote_watch_status(
    *,
    feed_status: str,
    stale: bool,
    last_successful_update_at: str | None,
    last_error: str | None,
    reconnect_attempts: int,
    reconnect_backoff_seconds: float | None,
) -> tuple[str, str]:
    normalized_feed_status = str(feed_status or "snapshot_ready").lower()
    success_at = last_successful_update_at or "n/a"
    backoff_text = f"Retry in {reconnect_backoff_seconds:g}s." if reconnect_backoff_seconds is not None else "Retrying soon."
    error_text = f" Last error: {last_error}." if last_error else ""

    if normalized_feed_status == "live":
        if stale:
            return (
                "Live but stale",
                f"Last live update at {success_at}. Awaiting a fresher tick.{error_text}",
            )
        if reconnect_attempts > 0:
            return (
                "Recovered",
                f"Recovered after {reconnect_attempts} retry(s). Last live update at {success_at}.{error_text}",
            )
        return ("Live", f"Feed is current. Last live update at {success_at}.{error_text}")

    if normalized_feed_status == "reconnecting":
        if last_successful_update_at is None:
            return (
                "Waiting for first live tick",
                f"Stream is warming up. {backoff_text}{error_text}",
            )
        return (
            "Recovering",
            f"Last live update at {success_at}. {backoff_text}{error_text}",
        )

    if normalized_feed_status == "disconnected":
        if last_successful_update_at is None:
            return (
                "Disconnected before first tick",
                f"No live quote arrived yet. {error_text or 'Waiting for stream recovery.'}",
            )
        return (
            "Disconnected",
            f"Feed disconnected after the last live update at {success_at}.{error_text}",
        )

    if stale:
        return (
            "Stale",
            f"Last live update at {success_at}. Awaiting a fresh tick.{error_text}",
        )

    if normalized_feed_status == "warming_up":
        return (
            "Waiting for first live tick",
            f"Stream is warming up. {backoff_text}{error_text}",
        )

    return (
        normalized_feed_status.replace("_", " ").title(),
        f"Feed status: {normalized_feed_status}.{error_text}",
    )


def build_quote_watch_panel(
    quote_snapshot: Any,
    *,
    stream_status: str = "snapshot_ready",
    feed_status: str | None = None,
    watch_status: str = "placeholder",
    stale: bool = False,
    last_successful_update_at: Any | None = None,
    last_error: str | None = None,
    reconnect_attempts: int = 0,
    reconnect_backoff_seconds: float | None = None,
    watchlist_items: tuple[QuoteWatchItem, ...] | None = None,
) -> QuoteWatchPanel:
    meta = _quote_value(quote_snapshot, "meta")
    symbol = str(_quote_value(quote_snapshot, "symbol") or "")
    provider_name = str(_quote_value(meta, "provider_name") or "unknown")
    source_name = str(_quote_value(meta, "source_id") or provider_name)
    as_of = _quote_value(quote_snapshot, "as_of")
    last_price = _quote_value(quote_snapshot, "last")
    bid = _quote_value(quote_snapshot, "bid")
    ask = _quote_value(quote_snapshot, "ask")
    currency = _quote_value(quote_snapshot, "currency")
    exchange = _quote_value(quote_snapshot, "exchange")
    live_stream = str(stream_status).lower() in {"live", "streaming", "connected"} or str(watch_status).lower() in {"live", "watching"}

    primary_item = _build_quote_watch_item(
        quote_snapshot,
        symbol=symbol,
        stream_status=stream_status,
        feed_status=feed_status,
        watch_status=watch_status,
        stale=stale,
        last_successful_update_at=last_successful_update_at,
        last_error=last_error,
        reconnect_attempts=reconnect_attempts,
        reconnect_backoff_seconds=reconnect_backoff_seconds,
        display_order=0,
        is_primary=True,
    )
    feed_status_value = primary_item.feed_status
    display_last_update_at = primary_item.last_update_at
    last_successful_update_at_value = primary_item.last_successful_update_at
    panel_last_successful_update_at = last_successful_update_at_value
    operator_status = primary_item.operator_status
    recovery_copy = primary_item.recovery_copy
    if live_stream:
        note = "backend-owned live quote stream; bid/ask remain backend-owned for later slices"
    else:
        note = "backend-owned quote placeholder; bid/ask are intentionally omitted until the live market stream slice"

    signals = (
        QuoteWatchSignal(
            label="symbol",
            value=symbol or "n/a",
            detail="watched symbol from backend quote snapshot",
            status="neutral",
        ),
        QuoteWatchSignal(
            label="last_price",
            value=str(last_price if last_price is not None else "n/a"),
            detail="last traded or snapshot price",
            status="healthy" if last_price is not None else "degraded",
        ),
        QuoteWatchSignal(
            label="provider",
            value=provider_name,
            detail=f"source={source_name}",
            status="neutral",
        ),
        QuoteWatchSignal(
            label="last_update",
            value=display_last_update_at or "n/a",
            detail="backend snapshot timestamp",
            status="neutral",
        ),
        QuoteWatchSignal(
            label="stream_status",
            value=stream_status,
            detail="dashboard transport status for the quote placeholder",
            status=stream_status,
        ),
        QuoteWatchSignal(
            label="watch_status",
            value=watch_status,
            detail="panel state for the current watch placeholder",
            status=watch_status,
        ),
        QuoteWatchSignal(
            label="bid_available",
            value="yes" if bid is not None else "no",
            detail="future market fields remain backend-owned",
            status="healthy" if bid is not None else "pending",
        ),
        QuoteWatchSignal(
            label="ask_available",
            value="yes" if ask is not None else "no",
            detail="future market fields remain backend-owned",
            status="healthy" if ask is not None else "pending",
        ),
    )

    if currency or exchange:
        note = f"{note} · {currency or 'currency n/a'} · {exchange or 'exchange n/a'}"

    return QuoteWatchPanel(
        watched_symbol=symbol or "n/a",
        provider_name=provider_name,
        source_name=source_name,
        last_price=last_price if isinstance(last_price, (int, float)) else None,
        last_update_at=display_last_update_at or "n/a",
        last_successful_update_at=panel_last_successful_update_at,
        stream_status=stream_status,
        feed_status=feed_status_value,
        operator_status=operator_status,
        recovery_copy=recovery_copy,
        watch_status=watch_status,
        stale=bool(stale),
        bid_available=bid is not None,
        ask_available=ask is not None,
        last_error=last_error,
        reconnect_attempts=int(reconnect_attempts or 0),
        reconnect_backoff_seconds=reconnect_backoff_seconds,
        note=note,
        signals=signals,
        watchlist_items=(
            tuple(sorted(watchlist_items, key=lambda item: (item.row_priority, item.display_order, item.symbol)))
            if watchlist_items is not None
            else (primary_item,)
        ),
    )


def build_composition_result_panel(outcome: dict[str, Any]) -> CompositionResultPanel:
    error = outcome.get("error") or {}
    selected_provider = outcome.get("fallback_selected_provider") or outcome.get("provider_name")
    return CompositionResultPanel(
        provider_name=str(outcome.get("provider_name") or ""),
        capability=str(outcome.get("capability") or ""),
        status=str(outcome.get("status") or ""),
        selected_provider=str(selected_provider) if selected_provider is not None else None,
        fallback_group=outcome.get("fallback_group"),
        error_type=error.get("error_type"),
        error_message=error.get("error_message"),
        priority=int(outcome["priority"]) if outcome.get("priority") is not None else None,
    )


def build_composition_fallback_panel(composition_result: dict[str, Any]) -> CompositionFallbackPanel:
    outcomes = list(composition_result.get("outcomes") or [])
    items = tuple(
        CompositionFallbackItem(
            provider_name=str(outcome.get("provider_name") or ""),
            capability=str(outcome.get("capability") or ""),
            status=str(outcome.get("status") or ""),
            selected_provider=(
                str(outcome.get("fallback_selected_provider") or outcome.get("provider_name") or "")
                if str(outcome.get("status") or "") in {"ok", "skipped_fallback"}
                else None
            ),
            fallback_group=outcome.get("fallback_group"),
            priority=int(outcome["priority"]) if outcome.get("priority") is not None else None,
            error_type=(outcome.get("error") or {}).get("error_type"),
            error_message=(outcome.get("error") or {}).get("error_message"),
        )
        for outcome in outcomes
    )

    attempted_provider_names = tuple(dict.fromkeys(item.provider_name for item in items))
    failed_provider_names = tuple(item.provider_name for item in items if item.status == "error")
    skipped_provider_names = tuple(item.provider_name for item in items if item.status == "skipped_fallback")

    selected_provider_names = tuple(dict.fromkeys(item.selected_provider for item in items if item.selected_provider))

    has_error = any(item.status == "error" for item in items)
    has_skipped = any(item.status == "skipped_fallback" for item in items)
    has_ok = any(item.status == "ok" for item in items)
    if has_skipped and has_error:
        overall_status = "fallback_degraded"
    elif has_skipped:
        overall_status = "fallback_applied"
    elif has_error and has_ok:
        overall_status = "partial_failure"
    elif has_error:
        overall_status = "failed"
    elif has_ok:
        overall_status = "ok"
    else:
        overall_status = "empty"

    return CompositionFallbackPanel(
        overall_status=overall_status,
        fallback_policy=str(composition_result.get("fallback_policy") or "none"),
        attempted_provider_names=attempted_provider_names,
        selected_provider_names=selected_provider_names,
        failed_provider_names=failed_provider_names,
        skipped_provider_names=skipped_provider_names,
        items=items,
    )


def _selection_reason_from_outcomes(outcomes: list[dict[str, Any]]) -> str:
    if any(str(outcome.get("status") or "") == "skipped_fallback" for outcome in outcomes):
        return "highest_priority_successful_provider_was_selected"
    if any(str(outcome.get("status") or "") == "ok" for outcome in outcomes):
        return "successful_provider_returned_a_result"
    if any(str(outcome.get("status") or "") == "error" for outcome in outcomes):
        return "no_successful_provider_available"
    return "no_provider_selected"


def _format_reason_codes(reason_codes: tuple[str, ...] | list[str] | None) -> str:
    values = [str(item) for item in (reason_codes or ()) if str(item)]
    return ", ".join(values) if values else "none"


def build_composition_outcome_detail_panel(
    composition_result: dict[str, Any],
    diagnostics_bundle: dict[str, Any],
) -> CompositionOutcomeDetailPanel:
    outcomes = list(composition_result.get("outcomes") or [])
    fallback_panel = build_composition_fallback_panel(composition_result)
    health_summary = diagnostics_bundle.get("health_summary") or {}
    evidence_summary = diagnostics_bundle.get("evidence_summary") or {}
    eligibility = diagnostics_bundle.get("eligibility") or {}

    provider_pairs = sorted({(str(outcome.get("provider_name") or ""), str(outcome.get("capability") or "")) for outcome in outcomes if outcome.get("provider_name") and outcome.get("capability")})

    summary_items = (
        CompositionOutcomeDetailItem(
            label="overall_status",
            value=fallback_panel.overall_status,
            detail="backend-computed composition status",
            status=fallback_panel.overall_status,
        ),
        CompositionOutcomeDetailItem(
            label="fallback_policy",
            value=fallback_panel.fallback_policy,
            detail="backend fallback policy used for this snapshot",
            status="neutral",
        ),
        CompositionOutcomeDetailItem(
            label="selection_reason",
            value=_selection_reason_from_outcomes(outcomes),
            detail="deterministic explanation of why the selected provider won",
            status="neutral",
        ),
        CompositionOutcomeDetailItem(
            label="selected_providers",
            value=", ".join(fallback_panel.selected_provider_names) or "none",
            detail="providers selected after fallback evaluation",
            status="healthy" if fallback_panel.selected_provider_names else "neutral",
        ),
    )

    path_items = tuple(
        CompositionOutcomeDetailItem(
            label=f"{str(outcome.get('provider_name') or '')} / {str(outcome.get('capability') or '')}",
            value=str(outcome.get("status") or "unknown"),
            detail=(
                f"priority={outcome.get('priority') if outcome.get('priority') is not None else 'n/a'} · "
                f"group={outcome.get('fallback_group') or 'none'} · "
                f"selected={outcome.get('fallback_selected_provider') or outcome.get('provider_name') or 'none'}"
            ),
            status=str(outcome.get("status") or "unknown"),
        )
        for outcome in sorted(outcomes, key=lambda item: (int(item.get("priority") or 10_000), str(item.get("provider_name") or "")))
    )

    eligibility_items_list: list[CompositionOutcomeDetailItem] = []
    evidence_items_list: list[CompositionOutcomeDetailItem] = []

    for provider_name, capability in provider_pairs:
        verdict = eligibility.get(provider_name, {}).get(capability)
        if verdict is not None:
            reason_text = _format_reason_codes(getattr(verdict, "reason_codes", ()))
            eligibility_items_list.append(
                CompositionOutcomeDetailItem(
                    label=f"{provider_name} / {capability}",
                    value=str(getattr(verdict, "classification_code", "UNCLASSIFIED")),
                    detail=f"state={getattr(verdict, 'eligibility', 'unknown')} · reasons={reason_text}",
                    status=str(getattr(verdict, "eligibility", "unknown")),
                )
            )

        bucket = evidence_summary.get(provider_name, {}).get(capability) or {}
        raw_count = int(bucket.get("raw_count") or 0)
        normalized_count = int(bucket.get("normalized_count") or 0)
        provenance_ready = raw_count > 0 and normalized_count > 0
        health_status = (health_summary.get(capability, {}).get("providers", {}).get(provider_name) or {}).get("status") or "unknown"
        evidence_items_list.append(
            CompositionOutcomeDetailItem(
                label=f"{provider_name} / {capability}",
                value=f"{raw_count} raw / {normalized_count} normalized",
                detail=f"provenance_ready={'yes' if provenance_ready else 'no'} · health={health_status}",
                status="healthy" if provenance_ready else "degraded",
            )
        )

    eligibility_items = tuple(eligibility_items_list)
    evidence_items = tuple(evidence_items_list)

    failure_items = tuple(
        CompositionOutcomeDetailItem(
            label=f"{str(outcome.get('provider_name') or '')} / {str(outcome.get('capability') or '')}",
            value=str((outcome.get("error") or {}).get("error_type") or "none"),
            detail=(
                f"{(outcome.get('error') or {}).get('error_message') or 'no error message'}"
                if str(outcome.get("status") or "") == "error"
                else f"skip_reason={outcome.get('fallback_selected_provider') or 'none'}"
            ),
            status="degraded" if str(outcome.get("status") or "") != "ok" else "healthy",
        )
        for outcome in outcomes
        if str(outcome.get("status") or "") in {"error", "skipped_fallback"}
    )

    sections: list[CompositionOutcomeDetailSection] = [
        CompositionOutcomeDetailSection(title="Summary", items=summary_items),
        CompositionOutcomeDetailSection(title="Outcome Path", items=path_items),
        CompositionOutcomeDetailSection(title="Eligibility", items=eligibility_items),
        CompositionOutcomeDetailSection(title="Evidence / Provenance", items=evidence_items),
    ]

    if failure_items:
        sections.append(CompositionOutcomeDetailSection(title="Failures / Skips", items=failure_items))

    return CompositionOutcomeDetailPanel(
        overall_status=fallback_panel.overall_status,
        fallback_policy=fallback_panel.fallback_policy,
        selection_reason=_selection_reason_from_outcomes(outcomes),
        selected_provider_names=fallback_panel.selected_provider_names,
        attempted_provider_names=fallback_panel.attempted_provider_names,
        failed_provider_names=fallback_panel.failed_provider_names,
        skipped_provider_names=fallback_panel.skipped_provider_names,
        sections=tuple(sections),
    )


def build_diagnostics_drawer_sections(
    diagnostics_bundle: dict[str, Any],
    *,
    composition_result: dict[str, Any] | None = None,
) -> tuple[DiagnosticsDrawerSection, ...]:
    health_summary = diagnostics_bundle.get("health_summary") or {}
    evidence_summary = diagnostics_bundle.get("evidence_summary") or {}
    correlation = diagnostics_bundle.get("correlation") or {}
    eligibility = diagnostics_bundle.get("eligibility") or {}

    provider_capabilities = _sorted_provider_capabilities(health_summary, evidence_summary, eligibility)

    overview_items = (
        DiagnosticsDrawerItem(
            label="health_manager",
            value="present" if diagnostics_bundle.get("health_manager_present") else "absent",
            detail="backend health manager available" if diagnostics_bundle.get("health_manager_present") else "backend health manager missing",
            status="healthy" if diagnostics_bundle.get("health_manager_present") else "degraded",
        ),
        DiagnosticsDrawerItem(
            label="capabilities",
            value=str(len(health_summary)),
            detail=", ".join(sorted(health_summary.keys())) or "none",
            status="neutral",
        ),
        DiagnosticsDrawerItem(
            label="providers",
            value=str(len(evidence_summary)),
            detail=", ".join(sorted(evidence_summary.keys())) or "none",
            status="neutral",
        ),
        DiagnosticsDrawerItem(
            label="provider_capabilities",
            value=str(len(provider_capabilities)),
            detail="deterministic union of health, evidence, and eligibility views",
            status="neutral",
        ),
    )

    health_items: list[DiagnosticsDrawerItem] = []
    evidence_items: list[DiagnosticsDrawerItem] = []
    eligibility_items: list[DiagnosticsDrawerItem] = []
    correlation_items: list[DiagnosticsDrawerItem] = []

    for provider_name, capability in provider_capabilities:
        health_bucket = health_summary.get(capability, {}).get("providers", {}).get(provider_name) or {}
        evidence_bucket = evidence_summary.get(provider_name, {}).get(capability) or {}
        verdict = eligibility.get(provider_name, {}).get(capability)
        correlation_bucket = correlation.get(provider_name, {}).get(capability) or {}

        health_status = str(health_bucket.get("status") or "unknown")
        eligibility_code = getattr(verdict, "classification_code", "UNCLASSIFIED")
        eligibility_state = getattr(verdict, "eligibility", "unknown")
        reason_codes = _format_reason_codes(getattr(verdict, "reason_codes", ()))
        degraded_or_down_count = correlation_bucket.get("degraded_or_down_evidence_count")
        total_evidence_count = correlation_bucket.get("total_evidence_count")

        health_items.append(
            DiagnosticsDrawerItem(
                label=f"{provider_name} / {capability}",
                value=health_status,
                detail=f"last_error={health_bucket.get('last_error_code') or 'none'} · updated={health_bucket.get('updated_at') or 'n/a'}",
                status=health_status,
            )
        )
        evidence_items.append(
            DiagnosticsDrawerItem(
                label=f"{provider_name} / {capability}",
                value=f"{int(evidence_bucket.get('raw_count') or 0)} raw / {int(evidence_bucket.get('normalized_count') or 0)} normalized",
                detail=f"symbols={', '.join(evidence_bucket.get('symbols') or []) or 'none'} · from={evidence_bucket.get('oldest_fetched_at') or 'n/a'} · to={evidence_bucket.get('newest_fetched_at') or 'n/a'}",
                status="healthy" if int(evidence_bucket.get('raw_count') or 0) and int(evidence_bucket.get('normalized_count') or 0) else "degraded",
            )
        )
        eligibility_items.append(
            DiagnosticsDrawerItem(
                label=f"{provider_name} / {capability}",
                value=str(eligibility_code),
                detail=f"state={eligibility_state} · reasons={reason_codes}",
                status=eligibility_state,
            )
        )
        correlation_items.append(
            DiagnosticsDrawerItem(
                label=f"{provider_name} / {capability}",
                value=f"{int(total_evidence_count or 0)} total",
                detail=f"degraded_or_down={int(degraded_or_down_count or 0)} · health={correlation_bucket.get('health_status') or health_status}",
                status="degraded" if int(degraded_or_down_count or 0) else "healthy",
            )
        )

    sections: list[DiagnosticsDrawerSection] = [
        DiagnosticsDrawerSection(title="Overview", items=overview_items),
        DiagnosticsDrawerSection(title="Health Signals", items=tuple(health_items)),
        DiagnosticsDrawerSection(title="Evidence Linkage", items=tuple(evidence_items)),
        DiagnosticsDrawerSection(title="Eligibility Reasons", items=tuple(eligibility_items)),
        DiagnosticsDrawerSection(title="Correlation", items=tuple(correlation_items)),
    ]

    if composition_result is not None:
        composition_items = [
            DiagnosticsDrawerItem(
                label="fallback_policy",
                value=str(composition_result.get("fallback_policy") or "none"),
                detail="backend fallback policy used for this snapshot",
                status="neutral",
            ),
            DiagnosticsDrawerItem(
                label="attempted",
                value=", ".join(composition_result.get("attempted_provider_names") or ()) or "none",
                detail="providers attempted in the snapshot",
                status="neutral",
            ),
            DiagnosticsDrawerItem(
                label="selected",
                value=", ".join(composition_result.get("selected_provider_names") or ()) or "none",
                detail="winning providers after fallback evaluation",
                status="healthy" if composition_result.get("selected_provider_names") else "neutral",
            ),
            DiagnosticsDrawerItem(
                label="failed",
                value=", ".join(composition_result.get("failed_provider_names") or ()) or "none",
                detail="providers that failed during composition",
                status="degraded" if composition_result.get("failed_provider_names") else "neutral",
            ),
            DiagnosticsDrawerItem(
                label="skipped",
                value=", ".join(composition_result.get("skipped_provider_names") or ()) or "none",
                detail="providers skipped by fallback policy",
                status="degraded" if composition_result.get("skipped_provider_names") else "neutral",
            ),
        ]
        sections.append(DiagnosticsDrawerSection(title="Composition Context", items=tuple(composition_items)))

    return tuple(sections)


def build_dashboard_shell_model(
    *,
    health_summary: dict[str, dict[str, Any]],
    evidence_summary: dict[str, dict[str, Any]],
    eligibility_view: dict[str, dict[str, Any]],
    diagnostics_bundle: dict[str, Any],
    composition_result: dict[str, Any] | None = None,
    composition_outcomes: list[dict[str, Any]] | None = None,
    quote_snapshot: Any | None = None,
    quote_watchlist_items: tuple[QuoteWatchItem, ...] | None = None,
    projection_bundle: DashboardProjectionBundle | None = None,
) -> dict[str, Any]:
    status_rows = build_provider_status_rows(health_summary, evidence_summary, eligibility_view)
    evidence_timeline_items = build_evidence_timeline_items(evidence_summary)
    composition_fallback_panel = build_composition_fallback_panel(composition_result) if composition_result is not None else None
    composition_outcome_detail_panel = (
        build_composition_outcome_detail_panel(composition_result, diagnostics_bundle)
        if composition_result is not None
        else None
    )
    quote_watch_panel = (
        build_quote_watch_panel(quote_snapshot, watchlist_items=quote_watchlist_items)
        if quote_snapshot is not None
        else None
    )
    diagnostics_sections = build_diagnostics_drawer_sections(diagnostics_bundle, composition_result=composition_result)
    diagnostics_drawer = {
        "health_manager_present": bool(diagnostics_bundle.get("health_manager_present")),
        "registry_snapshot": diagnostics_bundle.get("registry", {}),
        "capabilities": sorted(health_summary.keys()),
        "providers": sorted(evidence_summary.keys()),
        "status_row_count": len(status_rows),
        "sections": [asdict(section) for section in diagnostics_sections],
    }

    return {
        "provider_status_rows": [asdict(row) for row in status_rows],
        "evidence_timeline_items": [asdict(item) for item in evidence_timeline_items],
        "composition_fallback_panel": asdict(composition_fallback_panel) if composition_fallback_panel is not None else {},
        "composition_outcome_detail_panel": asdict(composition_outcome_detail_panel) if composition_outcome_detail_panel is not None else {},
        "quote_watch_panel": asdict(quote_watch_panel) if quote_watch_panel is not None else {},
        "diagnostics_drawer": diagnostics_drawer,
        "composition_outcomes": [build_composition_result_panel(outcome).__dict__ for outcome in (composition_outcomes or [])],
        "projection_bundle": asdict(projection_bundle) if projection_bundle is not None else {},
    }