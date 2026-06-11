from __future__ import annotations

import asyncio
import time
from datetime import datetime

import pytest

from trading_os_v1.providers.async_composition import ProviderCallSpec, compose_provider_calls
from trading_os_v1.providers.diagnostics import build_provider_diagnostic_bundle
from trading_os_v1.providers.evidence_summaries import summarize_evidence_eligibility_view, summarize_local_evidence
from trading_os_v1.providers.health import ProviderHealthManager
from trading_os_v1.providers.health_summaries import summarize_health
from trading_os_v1.providers.local_evidence_store import LocalEvidenceStore
from trading_os_v1.providers.registry import ProviderBinding, ProviderRegistry
from trading_os_v1.providers.schemas import ProviderCapability, ProviderMeta


@pytest.mark.asyncio
async def test_one_provider_succeeds_multiple_succeed(tmp_path) -> None:
    start_order: list[str] = []

    async def provider_a() -> dict[str, str]:
        start_order.append("a")
        await asyncio.sleep(0.06)
        return {"provider": "provider_a"}

    async def provider_b() -> dict[str, str]:
        start_order.append("b")
        await asyncio.sleep(0.06)
        return {"provider": "provider_b"}

    registry = ProviderRegistry(ProviderHealthManager())
    registry.register(
        ProviderBinding(
            capability=ProviderCapability.MARKET_DATA,
            provider_name="provider_a",
            factory=lambda: object(),
            priority=0,
        )
    )
    registry.register(
        ProviderBinding(
            capability=ProviderCapability.NEWS,
            provider_name="provider_b",
            factory=lambda: object(),
            priority=0,
        )
    )
    registry.set_health(
        registry._health.record_success("provider_a", ProviderCapability.MARKET_DATA, latency_ms=5.0, now=datetime(2024, 1, 15, 15, 30))
    )
    registry.set_health(
        registry._health.record_success("provider_b", ProviderCapability.NEWS, latency_ms=6.0, now=datetime(2024, 1, 15, 15, 30))
    )

    store = LocalEvidenceStore(tmp_path)
    raw_a = await store.put_raw(
        capability=ProviderCapability.MARKET_DATA.value,
        provider_name="provider_a",
        symbol="AAPL",
        fetched_at=datetime(2024, 1, 15, 15, 30),
        payload={"v": 1},
        meta=ProviderMeta(provider_name="provider_a", received_at=datetime(2024, 1, 15, 15, 30)),
    )
    await store.put_normalized(
        capability=ProviderCapability.MARKET_DATA.value,
        provider_name="provider_a",
        symbol="AAPL",
        fetched_at=datetime(2024, 1, 15, 15, 30),
        normalized_payload={"v": 1},
        raw_evidence_id=raw_a,
    )
    raw_b = await store.put_raw(
        capability=ProviderCapability.NEWS.value,
        provider_name="provider_b",
        symbol="AAPL",
        fetched_at=datetime(2024, 1, 15, 15, 30),
        payload={"v": 2},
        meta=ProviderMeta(provider_name="provider_b", received_at=datetime(2024, 1, 15, 15, 30)),
    )
    await store.put_normalized(
        capability=ProviderCapability.NEWS.value,
        provider_name="provider_b",
        symbol="AAPL",
        fetched_at=datetime(2024, 1, 15, 15, 30),
        normalized_payload={"v": 2},
        raw_evidence_id=raw_b,
    )

    calls = [
        ProviderCallSpec(provider_name="provider_a", capability=ProviderCapability.MARKET_DATA.value, call=provider_a),
        ProviderCallSpec(provider_name="provider_b", capability=ProviderCapability.NEWS.value, call=provider_b),
    ]

    start = time.perf_counter()
    result = await compose_provider_calls(
        calls,
        health_summary=summarize_health(registry),
        evidence_source=store,
    )
    elapsed = time.perf_counter() - start

    assert set(start_order) == {"a", "b"}
    assert elapsed < 0.11
    assert result["successful"]["provider_a"][ProviderCapability.MARKET_DATA.value]["provider"] == "provider_a"
    assert result["successful"]["provider_b"][ProviderCapability.NEWS.value]["provider"] == "provider_b"
    assert result["eligibility"]["provider_a"][ProviderCapability.MARKET_DATA.value].classification_code == "HEALTHY_ELIGIBLE"
    assert result["eligibility"]["provider_b"][ProviderCapability.NEWS.value].classification_code == "HEALTHY_ELIGIBLE"


@pytest.mark.asyncio
async def test_partial_provider_failure() -> None:
    async def ok_provider() -> dict[str, str]:
        await asyncio.sleep(0.01)
        return {"provider": "ok_provider"}

    async def bad_provider() -> dict[str, str]:
        await asyncio.sleep(0.01)
        raise TimeoutError("transient timeout")

    result = await compose_provider_calls(
        [
            ProviderCallSpec(provider_name="ok_provider", capability=ProviderCapability.MARKET_DATA.value, call=ok_provider),
            ProviderCallSpec(provider_name="bad_provider", capability=ProviderCapability.NEWS.value, call=bad_provider),
        ]
    )

    assert result["successful"]["ok_provider"][ProviderCapability.MARKET_DATA.value]["provider"] == "ok_provider"
    assert result["failures"]["bad_provider"][ProviderCapability.NEWS.value]["error_type"] == "TimeoutError"
    assert "transient timeout" in result["failures"]["bad_provider"][ProviderCapability.NEWS.value]["error_message"]


@pytest.mark.asyncio
async def test_eligibility_preservation(tmp_path) -> None:
    registry = ProviderRegistry(ProviderHealthManager())
    registry.register(
        ProviderBinding(
            capability=ProviderCapability.MARKET_DATA,
            provider_name="primary_market",
            factory=lambda: object(),
            priority=0,
        )
    )
    registry.set_health(
        registry._health.record_success("primary_market", ProviderCapability.MARKET_DATA, latency_ms=8.0, now=datetime(2024, 1, 15, 15, 30))
    )

    store = LocalEvidenceStore(tmp_path)
    raw_id = await store.put_raw(
        capability=ProviderCapability.MARKET_DATA.value,
        provider_name="primary_market",
        symbol="AAPL",
        fetched_at=datetime(2024, 1, 15, 15, 30),
        payload={"last": 100.0},
        meta=ProviderMeta(provider_name="primary_market", received_at=datetime(2024, 1, 15, 15, 30)),
    )
    await store.put_normalized(
        capability=ProviderCapability.MARKET_DATA.value,
        provider_name="primary_market",
        symbol="AAPL",
        fetched_at=datetime(2024, 1, 15, 15, 30),
        normalized_payload={"last": 100.0},
        raw_evidence_id=raw_id,
    )

    async def provider_ok() -> dict[str, str]:
        return {"provider": "primary_market"}

    health_summary = summarize_health(registry)
    evidence_summary = summarize_local_evidence(store)

    composition_result = await compose_provider_calls(
        [ProviderCallSpec(provider_name="primary_market", capability=ProviderCapability.MARKET_DATA.value, call=provider_ok)],
        health_summary=health_summary,
        evidence_summary=evidence_summary,
    )
    direct_view = summarize_evidence_eligibility_view(health_summary, evidence_summary=evidence_summary)
    registry_view = registry.provider_eligibility_view(evidence_summary)
    diagnostics_view = build_provider_diagnostic_bundle(registry, registry._health, store, temp_dir=str(tmp_path))["eligibility"]

    composed = composition_result["eligibility"]["primary_market"][ProviderCapability.MARKET_DATA.value]
    assert composed.classification_code == direct_view["primary_market"][ProviderCapability.MARKET_DATA.value].classification_code
    assert composed.classification_code == registry_view["primary_market"][ProviderCapability.MARKET_DATA.value].classification_code
    assert composed.classification_code == diagnostics_view["primary_market"][ProviderCapability.MARKET_DATA.value].classification_code


@pytest.mark.asyncio
async def test_fallback_behavior() -> None:
    async def slow_primary() -> dict[str, str]:
        await asyncio.sleep(0.02)
        return {"provider": "primary"}

    async def fast_backup() -> dict[str, str]:
        await asyncio.sleep(0.01)
        return {"provider": "backup"}

    result = await compose_provider_calls(
        [
            ProviderCallSpec(
                provider_name="primary",
                capability=ProviderCapability.MARKET_DATA.value,
                call=slow_primary,
                fallback_group="market_data_chain",
                priority=0,
            ),
            ProviderCallSpec(
                provider_name="backup",
                capability=ProviderCapability.MARKET_DATA.value,
                call=fast_backup,
                fallback_group="market_data_chain",
                priority=10,
            ),
        ],
        fallback_policy="best_available",
    )

    assert result["successful"]["primary"][ProviderCapability.MARKET_DATA.value]["provider"] == "primary"
    assert "backup" not in result["successful"]

    skipped = [
        item
        for item in result["outcomes"]
        if item["provider_name"] == "backup"
    ][0]
    assert skipped["status"] == "skipped_fallback"
    assert skipped["fallback_selected_provider"] == "primary"