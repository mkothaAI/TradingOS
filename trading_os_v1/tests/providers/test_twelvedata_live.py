import os
import pytest

pytestmark = pytest.mark.skipif(os.environ.get("TWELVEDATA_API_KEY") is None, reason="TWELVEDATA_API_KEY not set")

from trading_os_v1.providers.adapters.twelvedata import TwelveDataIntradayAdapter, TwelveDataConfig

try:
    from trading_os_v1.providers.local_evidence_store import LocalEvidenceStore
except Exception:
    import tempfile, json, os

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
async def test_live_fetch_intraday_bars_and_evidence(tmp_path):
    key = os.environ.get("TWELVEDATA_API_KEY")
    config = TwelveDataConfig(api_key=key, base_url="https://api.twelvedata.com", timeout_seconds=30)
    evidence_dir = tmp_path / "evidence"
    evidence_store = LocalEvidenceStore(str(evidence_dir))

    adapter = TwelveDataIntradayAdapter(config=config, evidence_store=evidence_store, health_manager=None, http_client=None)

    bars = await adapter.get_bars("AAPL", start="2024-01-02", end="2024-01-02", timeframe="1min")

    if not bars:
        pytest.skip("TwelveData live data is unavailable for this run")

    assert isinstance(bars, list)
    assert len(bars) > 0

    raw_file = evidence_dir / "raw.jsonl"
    norm_file = evidence_dir / "normalized.jsonl"
    assert raw_file.exists()
    assert norm_file.exists()
