from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from .schemas import ProviderHealthStatus


ProviderVerdictState = Literal["healthy", "degraded", "terminal"]
ProviderEligibilityState = Literal["eligible", "not_eligible"]


_TERMINAL_ERROR_CODES = {"AUTH", "401", "403", "UNAUTHORIZED", "FORBIDDEN"}


def _get_value(source: Any, key: str, default: Any = None) -> Any:
    if source is None:
        return default
    if isinstance(source, dict):
        return source.get(key, default)
    return getattr(source, key, default)


def _normalize_status(source: ProviderHealthStatus | dict[str, Any] | None) -> str | None:
    status = _get_value(source, "status")
    return str(status) if status is not None else None


def _normalize_error_code(source: ProviderHealthStatus | dict[str, Any] | None) -> str | None:
    error_code = _get_value(source, "last_error_code")
    return str(error_code).upper() if error_code is not None else None


def _evidence_counts(evidence_status: dict[str, Any] | None) -> tuple[int, int, int]:
    if evidence_status is None:
        return 0, 0, 0
    raw_count = int(evidence_status.get("raw_count") or 0)
    normalized_count = int(evidence_status.get("normalized_count") or 0)
    total_count = int(evidence_status.get("total_count") or (raw_count + normalized_count))
    return raw_count, normalized_count, total_count


def _classify_health_state(health_status: ProviderHealthStatus | dict[str, Any] | None) -> ProviderVerdictState:
    status = _normalize_status(health_status)
    error_code = _normalize_error_code(health_status)

    if status in {"down", "disabled"}:
        return "terminal"
    if error_code in _TERMINAL_ERROR_CODES:
        return "terminal"
    if status == "healthy":
        return "healthy"
    if status == "degraded":
        return "degraded"
    return "degraded"


@dataclass(frozen=True)
class ProviderEligibilityVerdict:
    provider_name: str
    capability: str
    health_state: ProviderVerdictState
    eligibility: ProviderEligibilityState
    classification_code: str
    reason_codes: tuple[str, ...]
    raw_count: int
    normalized_count: int
    total_count: int
    health_status: str | None
    last_error_code: str | None


def classify_provider_eligibility(
    provider_name: str,
    capability: str,
    health_status: ProviderHealthStatus | dict[str, Any] | None,
    evidence_status: dict[str, Any] | None,
) -> ProviderEligibilityVerdict:
    health_state = _classify_health_state(health_status)
    health_status_name = _normalize_status(health_status)
    error_code = _normalize_error_code(health_status)
    raw_count, normalized_count, total_count = _evidence_counts(evidence_status)

    reason_codes: list[str] = []

    if health_state == "terminal":
        if health_status_name == "disabled":
            reason_codes.append("HEALTH_DISABLED")
            classification_code = "TERMINAL_DISABLED_NOT_ELIGIBLE"
        elif error_code in _TERMINAL_ERROR_CODES:
            reason_codes.append(f"HEALTH_ERROR_{error_code}")
            classification_code = "TERMINAL_AUTH_NOT_ELIGIBLE"
        else:
            reason_codes.append("HEALTH_TERMINAL")
            classification_code = "TERMINAL_DOWN_NOT_ELIGIBLE"
        return ProviderEligibilityVerdict(
            provider_name=provider_name,
            capability=capability,
            health_state=health_state,
            eligibility="not_eligible",
            classification_code=classification_code,
            reason_codes=tuple(reason_codes),
            raw_count=raw_count,
            normalized_count=normalized_count,
            total_count=total_count,
            health_status=health_status_name,
            last_error_code=error_code,
        )

    evidence_complete = raw_count > 0 and normalized_count > 0
    evidence_present = total_count > 0

    if not evidence_present:
        reason_codes.append("NO_EVIDENCE")
        return ProviderEligibilityVerdict(
            provider_name=provider_name,
            capability=capability,
            health_state="degraded",
            eligibility="not_eligible",
            classification_code="DEGRADED_NO_EVIDENCE_NOT_ELIGIBLE",
            reason_codes=tuple(reason_codes),
            raw_count=raw_count,
            normalized_count=normalized_count,
            total_count=total_count,
            health_status=health_status_name,
            last_error_code=error_code,
        )

    if not evidence_complete:
        if raw_count == 0:
            reason_codes.append("MISSING_RAW_EVIDENCE")
        if normalized_count == 0:
            reason_codes.append("MISSING_NORMALIZED_EVIDENCE")
        return ProviderEligibilityVerdict(
            provider_name=provider_name,
            capability=capability,
            health_state="degraded",
            eligibility="not_eligible",
            classification_code="DEGRADED_PARTIAL_EVIDENCE_NOT_ELIGIBLE",
            reason_codes=tuple(reason_codes),
            raw_count=raw_count,
            normalized_count=normalized_count,
            total_count=total_count,
            health_status=health_status_name,
            last_error_code=error_code,
        )

    if health_state == "healthy":
        return ProviderEligibilityVerdict(
            provider_name=provider_name,
            capability=capability,
            health_state="healthy",
            eligibility="eligible",
            classification_code="HEALTHY_ELIGIBLE",
            reason_codes=("HEALTH_OK", "EVIDENCE_COMPLETE"),
            raw_count=raw_count,
            normalized_count=normalized_count,
            total_count=total_count,
            health_status=health_status_name,
            last_error_code=error_code,
        )

    reason_codes.append("HEALTH_DEGRADED")
    return ProviderEligibilityVerdict(
        provider_name=provider_name,
        capability=capability,
        health_state="degraded",
        eligibility="eligible",
        classification_code="DEGRADED_EVIDENCE_ELIGIBLE",
        reason_codes=tuple(reason_codes),
        raw_count=raw_count,
        normalized_count=normalized_count,
        total_count=total_count,
        health_status=health_status_name,
        last_error_code=error_code,
    )


def summarize_provider_eligibility(
    health_summary: dict[str, dict[str, Any]],
    evidence_summary: dict[str, dict[str, Any]],
) -> dict[str, dict[str, ProviderEligibilityVerdict]]:
    verdicts: dict[str, dict[str, ProviderEligibilityVerdict]] = {}

    provider_names = set(evidence_summary.keys())
    for capability_bucket in health_summary.values():
        provider_names.update(capability_bucket.get("providers", {}).keys())

    for provider_name in sorted(provider_names):
        provider_verdicts: dict[str, ProviderEligibilityVerdict] = {}

        capability_names = set(evidence_summary.get(provider_name, {}).keys())
        for capability, capability_bucket in health_summary.items():
            if provider_name in capability_bucket.get("providers", {}):
                capability_names.add(capability)

        for capability in sorted(capability_names):
            health_bucket = health_summary.get(capability, {}).get("providers", {}).get(provider_name)
            evidence_bucket = evidence_summary.get(provider_name, {}).get(capability)
            provider_verdicts[capability] = classify_provider_eligibility(
                provider_name=provider_name,
                capability=capability,
                health_status=health_bucket,
                evidence_status=evidence_bucket,
            )

        verdicts[provider_name] = provider_verdicts

    return verdicts