from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .health import ProviderHealthManager
from .schemas import ProviderCapability, ProviderHealthStatus


@dataclass(frozen=True)
class ProviderBinding:
    capability: ProviderCapability
    provider_name: str
    factory: Callable[[], Any]
    priority: int = 100
    enabled: bool = True


class ProviderRegistry:
    def __init__(self, health_manager: ProviderHealthManager | None = None) -> None:
        self._health = health_manager or ProviderHealthManager()
        self._bindings: dict[ProviderCapability, list[ProviderBinding]] = {}
        self._instances: dict[str, Any] = {}

    def register(self, binding: ProviderBinding) -> None:
        bindings = self._bindings.setdefault(binding.capability, [])
        bindings.append(binding)
        bindings.sort(key=lambda item: (item.priority, item.provider_name))

    def resolve(self, capability: ProviderCapability) -> Any:
        candidates = self.resolve_all(capability)
        if not candidates:
            raise KeyError(f"No provider registered for capability {capability.value}")
        return candidates[0]

    def resolve_all(self, capability: ProviderCapability) -> list[Any]:
        bindings = self._bindings.get(capability, [])
        scored: list[tuple[int, str, ProviderBinding]] = []
        for binding in bindings:
            if not binding.enabled:
                continue
            health = self._health.get(binding.provider_name)
            if health and health.status in {"down", "disabled"}:
                continue
            scored.append((binding.priority, binding.provider_name, binding))
        scored.sort(key=lambda item: (item[0], item[1]))

        resolved: list[Any] = []
        for _, provider_name, binding in scored:
            if provider_name not in self._instances:
                self._instances[provider_name] = binding.factory()
            resolved.append(self._instances[provider_name])
        return resolved

    def health(self, provider_name: str) -> ProviderHealthStatus | None:
        return self._health.get(provider_name)

    def set_health(self, status: ProviderHealthStatus) -> None:
        self._health._status_by_provider[status.provider_name] = status

    def provider_eligibility_view(
        self,
        evidence_summary: dict[str, dict[str, Any]],
    ) -> dict[str, dict[str, Any]]:
        from .eligibility import summarize_provider_eligibility
        from .health_summaries import summarize_health

        health_summary = summarize_health(self)
        return summarize_provider_eligibility(health_summary, evidence_summary)

    def provider_eligibility_view_from_evidence_store(
        self,
        evidence_source: Any,
    ) -> dict[str, dict[str, Any]]:
        from .evidence_summaries import summarize_local_evidence

        evidence_summary = summarize_local_evidence(evidence_source)
        return self.provider_eligibility_view(evidence_summary)