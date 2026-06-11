"""Fixtures for Universe engine tests (Phase 6)."""
import pytest
from datetime import date


@pytest.fixture
def ticker_metadata_valid():
    """Valid diverse ticker metadata, all eligible after filters."""
    return [
        {"ticker": "AAPL", "exchange": "NASDAQ", "sector": "Tech", "market_cap": 2800000000, "lot_size": 1, "tradable": True},
        {"ticker": "MSFT", "exchange": "NASDAQ", "sector": "Tech", "market_cap": 2700000000, "lot_size": 1, "tradable": True},
        {"ticker": "BAC", "exchange": "NYSE", "sector": "Finance", "market_cap": 300000000, "lot_size": 1, "tradable": True},
        {"ticker": "JPM", "exchange": "NYSE", "sector": "Finance", "market_cap": 400000000, "lot_size": 1, "tradable": True},
        {"ticker": "JNJ", "exchange": "NYSE", "sector": "Health", "market_cap": 420000000, "lot_size": 1, "tradable": True},
    ]


@pytest.fixture
def ticker_metadata_mixed():
    """Mixed metadata: some valid, some invalid (for testing filters)."""
    return [
        # Valid
        {"ticker": "AAPL", "exchange": "NASDAQ", "sector": "Tech", "market_cap": 2800000000, "lot_size": 1, "tradable": True},
        # Invalid: tradable=False
        {"ticker": "XYZ", "exchange": "NASDAQ", "sector": "Tech", "market_cap": 500000, "lot_size": 1, "tradable": False},
        # Invalid: lot_size=0
        {"ticker": "ILL1", "exchange": "NASDAQ", "sector": "Tech", "market_cap": 1000000, "lot_size": 0, "tradable": True},
        # Valid
        {"ticker": "BAC", "exchange": "NYSE", "sector": "Finance", "market_cap": 300000000, "lot_size": 1, "tradable": True},
        # Invalid: missing market_cap
        {"ticker": "BAD1", "exchange": "NYSE", "sector": "Finance", "lot_size": 1, "tradable": True},
        # Invalid: missing sector
        {"ticker": "BAD2", "exchange": "NYSE", "market_cap": 100000000, "lot_size": 1, "tradable": True},
        # Invalid: exchange not US
        {"ticker": "TSM", "exchange": "TSE", "sector": "Tech", "market_cap": 1500000000, "lot_size": 1, "tradable": True},
        # Valid
        {"ticker": "MSFT", "exchange": "NASDAQ", "sector": "Tech", "market_cap": 2700000000, "lot_size": 1, "tradable": True},
    ]


@pytest.fixture
def ticker_metadata_duplicates():
    """Metadata with duplicate tickers."""
    return [
        {"ticker": "AAPL", "exchange": "NASDAQ", "sector": "Tech", "market_cap": 2800000000, "lot_size": 1, "tradable": True},
        {"ticker": "MSFT", "exchange": "NASDAQ", "sector": "Tech", "market_cap": 2700000000, "lot_size": 1, "tradable": True},
        {"ticker": "AAPL", "exchange": "NASDAQ", "sector": "Tech", "market_cap": 2900000000, "lot_size": 1, "tradable": True},  # Duplicate
    ]


@pytest.fixture
def ticker_metadata_empty():
    """Empty metadata list."""
    return []


@pytest.fixture
def request_meta_valid():
    """Valid RequestMeta fixture."""
    from backend.schemas.shared import RequestMeta
    return RequestMeta(request_id="test-123", as_of_date=date(2026, 5, 16))
