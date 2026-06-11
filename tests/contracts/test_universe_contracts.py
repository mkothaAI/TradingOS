import json
from backend.schemas.models_requests import UniverseRequest
from pathlib import Path


def test_universe_request_schema_validates_example_fixture():
    p = Path('tests/fixtures/contracts/universe_request_valid.json')
    data = json.loads(p.read_text())
    req = UniverseRequest.model_validate(data)
    assert req.universe_config.allowed_markets == ['US']


def test_universe_response_shape_ok():
    # construct minimal response
    # import here to avoid circular
    from backend.schemas.models_responses import UniverseResponse
    from backend.schemas.shared import RequestMeta, ResponseStatus
    from backend.schemas.models_responses import UniverseItem
    from backend.schemas.shared import UniverseStats
    from datetime import date
    meta = RequestMeta(request_id='r', as_of_date=date(2026, 5, 16))
    universe_items = [UniverseItem(ticker='AAPL', metadata={'ticker':'AAPL','exchange':'NASDAQ','sector':'Tech','market_cap':1000,'lot_size':1,'tradable':True})]
    stats = UniverseStats(count=1, total_market_cap=1000, sector_exposures={'Tech': 1.0})
    resp = UniverseResponse(meta=meta, status=ResponseStatus.OK, universe_list=universe_items, universe_stats=stats, errors=[])
    assert resp.status == ResponseStatus.OK
