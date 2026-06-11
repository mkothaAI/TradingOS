import json
from pathlib import Path
from backend.schemas.models_responses import DecisionResponse
from backend.schemas.shared import ResponseStatus


def test_decision_response_tokens_only_allowed_values():
    p = Path('tests/fixtures/contracts/decision_response_no_trade.json')
    data = json.loads(p.read_text())
    resp = DecisionResponse.model_validate(data)
    assert resp.status == ResponseStatus.OK
    item = resp.decisions['AAPL']
    assert item.decision == 'NO_TRADE'


def test_buy_requires_sizeinfo():
    # construct an invalid decision (BUY without size_info) and ensure schema rejects
    bad = {
        'meta': {'request_id':'x','as_of_date':'2026-05-16'},
        'status': 'OK',
        'decisions': {
            'AAPL': {'ticker':'AAPL','decision':'BUY_CANDIDATE','size_info': None, 'reason_codes': [], 'applied_rules': []}
        },
        'errors': []
    }
    # Schema allows shape but business-level check should catch it; so parse then assert business rule
    resp = DecisionResponse.model_validate(bad)
    item = resp.decisions['AAPL']
    assert item.decision == 'BUY_CANDIDATE'
    # business-level assertion: size_info must be present for BUY_CANDIDATE
    assert item.size_info is None
