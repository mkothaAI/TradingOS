from __future__ import annotations

from collections import defaultdict
from typing import Any

from trading_os_v1.providers.health import ProviderHealthManager
from trading_os_v1.providers.registry import ProviderBinding, ProviderRegistry
from trading_os_v1.providers.schemas import ProviderCapability, ProviderHealthStatus


_STATUS_RANK = {
    "healthy": 0,
    "degraded": 1,
    "down": 2,
    "disabled": 3,
}


def _status_rank(status: str) -> int:
    return _STATUS_RANK.get(status, 0)


def _empty_capability_summary(capability: ProviderCapability) -> dict[str, Any]:
    return {
        "capability": capability.value,
        "capability_status": None,
        "providers": {},
    }


def _summarize_health_status(status: ProviderHealthStatus) -> dict[str, Any]:
    return {
        "provider_name": status.provider_name,
        "capability": status.capability.value,
        "status": status.status,
        "last_success_at": status.last_success_at,
        "last_failure_at": status.last_failure_at,
        "latency_ms_p50": status.latency_ms_p50,
        "latency_ms_p95": status.latency_ms_p95,
        "quota_remaining": status.quota_remaining,
        "quota_reset_at": status.quota_reset_at,
        "degraded_reason": status.degraded_reason,
        "last_error_code": status.last_error_code,
        "last_error_message": status.last_error_message,
        "updated_at": status.updated_at,
    }


def summarize_health(
    subject: ProviderRegistry | ProviderHealthManager,
    /,
    *,
    capabilities: list[ProviderCapability] | None = None,
) -> dict[str, dict[str, Any]]:
    if isinstance(subject, ProviderRegistry):
        manager = subject._health
        binding_map: dict[ProviderCapability, list[ProviderBinding]] = defaultdict(list)
        for capability, bindings in subject._bindings.items():
            for binding in bindings:
                binding_map[capability].append(binding)
    else:
        manager = subject
        binding_map = defaultdict(list)

    selected_capabilities = capabilities or list(ProviderCapability)
    summary: dict[str, dict[str, Any]] = {}

    for capability in selected_capabilities:
        capability_summary = _empty_capability_summary(capability)
        provider_bindings = sorted(binding_map.get(capability, []), key=lambda item: (item.provider_name, item.priority))
        worst_rank = -1
        worst_status: str | None = None

        for binding in provider_bindings:
            provider_name = binding.provider_name
            status = manager.get(provider_name)
            if status is None and not binding.enabled:
                provider_summary = {
                    "provider_name": provider_name,
                    "capability": capability.value,
                    "status": "disabled",
                    "last_success_at": None,
                    "last_failure_at": None,
                    "latency_ms_p50": None,
                    "latency_ms_p95": None,
                    "quota_remaining": None,
                    "quota_reset_at": None,
                    "degraded_reason": None,
                    "last_error_code": None,
                    "last_error_message": None,
                    "updated_at": None,
                }
            else:
                provider_summary = _summarize_health_status(status) if status else {
                    "provider_name": provider_name,
                    "capability": capability.value,
                    "status": None,
                    "last_success_at": None,
                    "last_failure_at": None,
                    "latency_ms_p50": None,
                    "latency_ms_p95": None,
                    "quota_remaining": None,
                    "quota_reset_at": None,
                    "degraded_reason": None,
                    "last_error_code": None,
                    "last_error_message": None,
                    "updated_at": None,
                }
            capability_summary["providers"][provider_name] = provider_summary

            if status is not None:
                rank = _status_rank(status.status)
                if rank > worst_rank:
                    worst_rank = rank
                    worst_status = status.status
            elif not binding.enabled and _status_rank("disabled") > worst_rank:
                worst_rank = _status_rank("disabled")
                worst_status = "disabled"

        capability_summary["capability_status"] = worst_status
        summary[capability.value] = capability_summary

    return summary