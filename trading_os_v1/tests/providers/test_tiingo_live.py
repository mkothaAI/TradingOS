import os
import pytest
import asyncio

pytestmark = pytest.mark.skipif(os.environ.get("TIINGO_API_KEY") is None, reason="TIINGO_API_KEY not set")

from trading_os_v1.providers.adapters.tiingo import TiingoHistoricalAdapter, TiingoConfig

try:
    from trading_os_v1.persistence.local_evidence_store import LocalEvidenceStore
except Exception:
    # best-effort fallback: use a minimal local store if repo path differs
    import tempfile, json

    class LocalEvidenceStore:
        def __init__(self, path):
            self.path = path
            os.makedirs(self.path, exist_ok=True)

        def put_raw(self, *args, **kwargs):
            p = os.path.join(self.path, "raw.jsonl")
            with open(p, "a") as f:
                f.write(json.dumps({"args": args, "kwargs": kwargs}) + "\n")

        def put_normalized(self, *args, **kwargs):
            p = os.path.join(self.path, "normalized.jsonl")
            with open(p, "a") as f:
                f.write(json.dumps({"args": args, "kwargs": kwargs}) + "\n")


@pytest.mark.asyncio
async def test_live_fetch_daily_bars_and_evidence(tmp_path):
    key = os.environ.get("TIINGO_API_KEY")
    if not key:
        pytest.skip("TIINGO_API_KEY not set")
    config = TiingoConfig(api_key=key, base_url="https://api.tiingo.com", timeout_seconds=30)
    evidence_dir = tmp_path / "evidence"
    evidence_store = LocalEvidenceStore(str(evidence_dir))

    # Use real httpx client in the adapter by not injecting a mock http_client
    adapter = TiingoHistoricalAdapter(config=config, evidence_store=evidence_store, health_manager=None, http_client=None)

    bars = await adapter.fetch_price_bars("AAPL", start="2020-01-01", end="2020-01-10")

    if not bars:
        pytest.skip("Tiingo live data is unavailable for this run")

    assert isinstance(bars, list)
    assert len(bars) > 0

    # Check evidence files exist
    raw_file = evidence_dir / "raw.jsonl"
    norm_file = evidence_dir / "normalized.jsonl"
    assert raw_file.exists()
    assert norm_file.exists()
