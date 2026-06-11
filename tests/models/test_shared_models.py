import json
from datetime import date
from backend.schemas.shared import RequestMeta, PriceBar, TickerMetadata, ResponseStatus


def test_requestmeta_and_response_status_enum():
    m = RequestMeta(request_id='uuid-1', as_of_date=date(2026,5,16))
    assert m.request_id == 'uuid-1'
    assert isinstance(m.as_of_date, date)
    assert ResponseStatus.OK.value == 'OK'


def test_pricebar_and_ticker_metadata_strict_types():
    pb = PriceBar(date=date(2026,5,15), open=10.0, high=11.0, low=9.5, close=10.5, volume=1000)
    assert pb.close == 10.5
    tm = TickerMetadata(ticker='AAPL', exchange='NASDAQ', tradable=True)
    assert tm.tradable is True
