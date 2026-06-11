from __future__ import annotations

from datetime import datetime

from .schemas import ProviderCapability, ProviderHealthStatus


_DOWN_ERROR_CODES = {"AUTH", "401", "403", "UNAUTHORIZED", "FORBIDDEN"}
_DEGRADED_ERROR_CODES = {"RATE_LIMIT", "429", "TIMEOUT", "SERVER_ERROR", "500"}


class ProviderHealthManager:
    def __init__(self) -> None:
        self._status_by_provider: dict[str, ProviderHealthStatus] = {}

    def get(self, provider_name: str) -> ProviderHealthStatus | None:
        return self._status_by_provider.get(provider_name)

    def record_success(
        self,
        provider_name: str,
        capability: ProviderCapability,
        latency_ms: float,
        quota_remaining: int | None = None,
        quota_reset_at: datetime | None = None,
        now: datetime | None = None,
    ) -> ProviderHealthStatus:
        observed_at = now or datetime.utcnow()
        current = self._status_by_provider.get(provider_name)
        status = ProviderHealthStatus(
            provider_name=provider_name,
            capability=capability,
            status="healthy",
            last_success_at=observed_at,
            last_failure_at=current.last_failure_at if current else None,
            latency_ms_p50=latency_ms,
            latency_ms_p95=latency_ms,
            quota_remaining=quota_remaining,
            quota_reset_at=quota_reset_at,
            staleness_seconds=None,
            last_error_code=None,
            last_error_message=None,
            degraded_reason=None,
            updated_at=observed_at,
        )
        self._status_by_provider[provider_name] = status
        return status

    def record_failure(
        self,
        provider_name: str,
        capability: ProviderCapability,
        error_code: str,
        error_message: str,
        now: datetime | None = None,
    ) -> ProviderHealthStatus:
        observed_at = now or datetime.utcnow()
        status_name = "down" if error_code.upper() in _DOWN_ERROR_CODES else "degraded"
        if error_code.upper() in _DEGRADED_ERROR_CODES:
            status_name = "degraded"
        current = self._status_by_provider.get(provider_name)
        status = ProviderHealthStatus(
            provider_name=provider_name,
            capability=capability,
            status=status_name,
            last_success_at=current.last_success_at if current else None,
            last_failure_at=observed_at,
            latency_ms_p50=current.latency_ms_p50 if current else None,
            latency_ms_p95=current.latency_ms_p95 if current else None,
            quota_remaining=0 if error_code.upper() in {"RATE_LIMIT", "429"} else (current.quota_remaining if current else None),
            quota_reset_at=current.quota_reset_at if current else None,
            staleness_seconds=current.staleness_seconds if current else None,
            last_error_code=error_code,
            last_error_message=error_message,
            degraded_reason=error_message if status_name == "degraded" else None,
            updated_at=observed_at,
        )
        self._status_by_provider[provider_name] = status
        return status

    def mark_degraded(
        self,
        provider_name: str,
        capability: ProviderCapability,
        reason: str,
        now: datetime | None = None,
    ) -> ProviderHealthStatus:
        observed_at = now or datetime.utcnow()
        current = self._status_by_provider.get(provider_name)
        status = ProviderHealthStatus(
            provider_name=provider_name,
            capability=capability,
            status="degraded",
            last_success_at=current.last_success_at if current else None,
            last_failure_at=current.last_failure_at if current else None,
            latency_ms_p50=current.latency_ms_p50 if current else None,
            latency_ms_p95=current.latency_ms_p95 if current else None,
            quota_remaining=current.quota_remaining if current else None,
            quota_reset_at=current.quota_reset_at if current else None,
            staleness_seconds=current.staleness_seconds if current else None,
            last_error_code=current.last_error_code if current else None,
            last_error_message=current.last_error_message if current else None,
            degraded_reason=reason,
            updated_at=observed_at,
        )
        self._status_by_provider[provider_name] = status
        return status