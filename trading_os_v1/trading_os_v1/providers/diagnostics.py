from __future__ import annotations

from typing import Any

from trading_os_v1.providers.eligibility import summarize_provider_eligibility
from trading_os_v1.providers.evidence_summaries import correlate_health_and_evidence, summarize_local_evidence
from trading_os_v1.providers.health import ProviderHealthManager
from trading_os_v1.providers.health_summaries import summarize_health
from trading_os_v1.providers.local_evidence_store import LocalEvidenceStore
from trading_os_v1.providers.registry import ProviderRegistry
from trading_os_v1.providers.schemas import ProviderCapability


def _registry_snapshot(registry: ProviderRegistry) -> dict[str, list[dict[str, Any]]]:
    snapshot: dict[str, list[dict[str, Any]]] = {}
    for capability, bindings in sorted(registry._bindings.items(), key=lambda item: item[0].value):
        snapshot[capability.value] = [
            {
                "provider_name": binding.provider_name,
                "priority": binding.priority,
                "enabled": binding.enabled,
            }
            for binding in sorted(bindings, key=lambda item: (item.priority, item.provider_name))
        ]
    return snapshot


def build_provider_diagnostic_bundle(
    registry: ProviderRegistry,
    health_manager: ProviderHealthManager,
    evidence_store: LocalEvidenceStore,
    /,
    *,
    temp_dir: str | None = None,
) -> dict[str, Any]:
    summary = summarize_health(registry)
    evidence_source = temp_dir or evidence_store.base_dir
    evidence_summary = summarize_local_evidence(evidence_source)
    correlation = correlate_health_and_evidence(summary, evidence_summary)
    eligibility = summarize_provider_eligibility(summary, evidence_summary)

    return {
        "registry": _registry_snapshot(registry),
        "health_summary": summary,
        "evidence_summary": evidence_summary,
        "correlation": correlation,
        "eligibility": eligibility,
        "health_manager_present": health_manager is not None,
    }