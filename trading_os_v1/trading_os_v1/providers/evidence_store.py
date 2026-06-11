from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol

from .schemas import ProviderMeta


class EvidenceStore(Protocol):
    async def put_raw(
        self,
        *,
        capability: str,
        provider_name: str,
        symbol: str | None,
        fetched_at: datetime,
        payload: dict[str, Any],
        meta: ProviderMeta,
    ) -> str: ...

    async def put_normalized(
        self,
        *,
        capability: str,
        provider_name: str,
        symbol: str | None,
        fetched_at: datetime,
        normalized_payload: dict[str, Any],
        raw_evidence_id: str,
    ) -> str: ...

    async def get_raw(self, evidence_id: str) -> dict[str, Any] | None: ...

    async def get_normalized(self, evidence_id: str) -> dict[str, Any] | None: ...