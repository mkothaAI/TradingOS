from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Literal, Sequence

from trading_os_v1.providers.evidence_summaries import summarize_evidence_eligibility_view


FallbackPolicy = Literal["none", "best_available"]


@dataclass(frozen=True)
class ProviderCallSpec:
    provider_name: str
    capability: str
    call: Callable[[], Awaitable[Any]]
    fallback_group: str | None = None
    priority: int = 100


def _serialize_exception(error: Exception) -> dict[str, str]:
    return {
        "error_type": type(error).__name__,
        "error_message": str(error),
    }


async def _run_call(spec: ProviderCallSpec) -> dict[str, Any]:
    try:
        value = await spec.call()
        return {
            "provider_name": spec.provider_name,
            "capability": spec.capability,
            "status": "ok",
            "value": value,
            "fallback_group": spec.fallback_group,
            "priority": spec.priority,
        }
    except Exception as error:
        return {
            "provider_name": spec.provider_name,
            "capability": spec.capability,
            "status": "error",
            "value": None,
            "error": _serialize_exception(error),
            "fallback_group": spec.fallback_group,
            "priority": spec.priority,
        }


def _apply_best_available_fallback(outcomes: list[dict[str, Any]]) -> None:
    grouped_indices: dict[str, list[int]] = {}
    for index, outcome in enumerate(outcomes):
        group = outcome.get("fallback_group")
        if not group:
            continue
        grouped_indices.setdefault(str(group), []).append(index)

    for indices in grouped_indices.values():
        candidates = [
            outcomes[index]
            for index in indices
            if outcomes[index].get("status") == "ok"
        ]
        if not candidates:
            continue
        winner = sorted(candidates, key=lambda item: (int(item.get("priority", 100)), str(item.get("provider_name", ""))))[0]
        winner_provider = winner["provider_name"]
        winner_capability = winner["capability"]

        for index in indices:
            outcome = outcomes[index]
            if outcome.get("status") != "ok":
                continue
            same_winner = (
                outcome.get("provider_name") == winner_provider
                and outcome.get("capability") == winner_capability
            )
            if same_winner:
                continue
            outcome["status"] = "skipped_fallback"
            outcome["fallback_selected_provider"] = winner_provider
            outcome["value"] = None


async def compose_provider_calls(
    provider_calls: Sequence[ProviderCallSpec],
    *,
    health_summary: dict[str, dict[str, Any]] | None = None,
    evidence_source: Any = None,
    evidence_summary: dict[str, dict[str, Any]] | None = None,
    fallback_policy: FallbackPolicy = "none",
) -> dict[str, Any]:
    tasks = [asyncio.create_task(_run_call(spec)) for spec in provider_calls]
    gathered = await asyncio.gather(*tasks, return_exceptions=True)

    outcomes: list[dict[str, Any]] = []
    for index, item in enumerate(gathered):
        if isinstance(item, Exception):
            spec = provider_calls[index]
            outcomes.append(
                {
                    "provider_name": spec.provider_name,
                    "capability": spec.capability,
                    "status": "error",
                    "value": None,
                    "error": _serialize_exception(item),
                    "fallback_group": spec.fallback_group,
                    "priority": spec.priority,
                }
            )
        else:
            outcomes.append(item)

    if fallback_policy == "best_available":
        _apply_best_available_fallback(outcomes)

    successful: dict[str, dict[str, Any]] = {}
    failures: dict[str, dict[str, Any]] = {}
    for outcome in outcomes:
        provider_name = str(outcome.get("provider_name"))
        capability = str(outcome.get("capability"))
        status = str(outcome.get("status"))
        if status == "ok":
            successful.setdefault(provider_name, {})[capability] = outcome.get("value")
        elif status == "error":
            failures.setdefault(provider_name, {})[capability] = outcome.get("error")

    eligibility_view: dict[str, dict[str, Any]] = {}
    if health_summary is not None:
        eligibility_view = summarize_evidence_eligibility_view(
            health_summary,
            evidence_source=evidence_source,
            evidence_summary=evidence_summary,
        )

    return {
        "outcomes": outcomes,
        "successful": successful,
        "failures": failures,
        "eligibility": eligibility_view,
        "fallback_policy": fallback_policy,
    }