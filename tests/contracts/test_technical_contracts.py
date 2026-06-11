import json
from pathlib import Path
from backend.schemas.models_requests import TechnicalRequest
from backend.schemas.validators import check_min_lookback


def test_technical_request_shape_validates_pricebar_structure():
    p = Path('tests/fixtures/contracts/technical_request_insufficient.json')
    data = json.loads(p.read_text())
    req = TechnicalRequest.model_validate(data)
    assert 'AAPL' in req.price_series


def test_technical_business_insufficient_history_flags_error():
    p = Path('tests/fixtures/contracts/technical_request_insufficient.json')
    data = json.loads(p.read_text())
    req = TechnicalRequest.model_validate(data)
    errs = check_min_lookback(req.price_series, min_lookback=60)
    assert errs.get('AAPL') == 'INSUFFICIENT_HISTORY'
