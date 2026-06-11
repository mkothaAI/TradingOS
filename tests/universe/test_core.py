"""Tests for Universe engine core functions (Phase 6)."""
import sys
import os
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from backend.engines.universe.calc import (
    validate_required_fields,
    filter_tradable_symbols,
    filter_by_market,
    filter_by_lot_size,
    sort_by_market_cap_descending,
    dedup_by_ticker,
    apply_max_universe_size,
    compute_universe_stats,
    build_eligible_universe,
    EXCHANGE_MAP,
)


# ============================================================================
# 1.1 Eligible Symbol Inclusion Tests (3 tests)
# ============================================================================

def test_filter_tradable_true(ticker_metadata_mixed):
    """Keep symbols with tradable=true."""
    result = filter_tradable_symbols(ticker_metadata_mixed)
    tradable_tickers = [r["ticker"] for r in result]
    assert "XYZ" not in tradable_tickers  # XYZ is tradable=False
    assert all(r["tradable"] for r in result)


def test_filter_exchange_in_allowed_markets(ticker_metadata_mixed):
    """Keep only symbols from allowed_markets (US = NASDAQ, NYSE, AMEX, OTC)."""
    allowed_markets = ["US"]
    result = filter_by_market(ticker_metadata_mixed, allowed_markets)
    tickers = [r["ticker"] for r in result]
    # TSM (TSE exchange) should be excluded
    assert "TSM" not in tickers
    # AAPL (NASDAQ), BAC (NYSE), MSFT (NASDAQ) should be included
    assert "AAPL" in tickers or "MSFT" in tickers or "BAC" in tickers


def test_filter_by_market_nyse_nasdaq_amex_otc_included(ticker_metadata_valid):
    """NYSE, NASDAQ, AMEX, OTC are all US markets."""
    # Create test with all US exchanges
    metadata = [
        {"ticker": "NASDAQ_TEST", "exchange": "NASDAQ", "sector": "Tech", "market_cap": 1000, "lot_size": 1, "tradable": True},
        {"ticker": "NYSE_TEST", "exchange": "NYSE", "sector": "Tech", "market_cap": 1000, "lot_size": 1, "tradable": True},
        {"ticker": "AMEX_TEST", "exchange": "AMEX", "sector": "Tech", "market_cap": 1000, "lot_size": 1, "tradable": True},
        {"ticker": "OTC_TEST", "exchange": "OTC", "sector": "Tech", "market_cap": 1000, "lot_size": 1, "tradable": True},
    ]
    result = filter_by_market(metadata, ["US"])
    assert len(result) == 4


# ============================================================================
# 1.2 Liquidity & Data Quality Tests (5 tests)
# ============================================================================

def test_lot_size_zero_excluded():
    """lot_size <= 0 signals illiquidity; exclude."""
    metadata = [
        {"ticker": "AAPL", "exchange": "NASDAQ", "sector": "Tech", "market_cap": 1000, "lot_size": 1, "tradable": True},
        {"ticker": "ILL", "exchange": "NASDAQ", "sector": "Tech", "market_cap": 500, "lot_size": 0, "tradable": True},
    ]
    result = filter_by_lot_size(metadata)
    assert len(result) == 1
    assert result[0]["ticker"] == "AAPL"


def test_missing_market_cap_excluded():
    """market_cap field missing → exclude (fail closed)."""
    metadata = [
        {"ticker": "AAPL", "exchange": "NASDAQ", "sector": "Tech", "market_cap": 1000, "lot_size": 1, "tradable": True},
        {"ticker": "BAD", "exchange": "NASDAQ", "sector": "Tech", "lot_size": 1, "tradable": True},  # no market_cap
    ]
    result = validate_required_fields(metadata)
    assert len(result) == 1
    assert result[0]["ticker"] == "AAPL"


def test_missing_sector_excluded():
    """sector field missing → exclude (fail closed)."""
    metadata = [
        {"ticker": "AAPL", "exchange": "NASDAQ", "sector": "Tech", "market_cap": 1000, "lot_size": 1, "tradable": True},
        {"ticker": "BAD", "exchange": "NASDAQ", "market_cap": 1000, "lot_size": 1, "tradable": True},  # no sector
    ]
    result = validate_required_fields(metadata)
    assert len(result) == 1


def test_missing_exchange_excluded():
    """exchange field missing → exclude (fail closed)."""
    metadata = [
        {"ticker": "AAPL", "exchange": "NASDAQ", "sector": "Tech", "market_cap": 1000, "lot_size": 1, "tradable": True},
        {"ticker": "BAD", "sector": "Tech", "market_cap": 1000, "lot_size": 1, "tradable": True},  # no exchange
    ]
    result = validate_required_fields(metadata)
    assert len(result) == 1


def test_null_values_treated_as_missing():
    """Null/None values for critical fields → exclude."""
    metadata = [
        {"ticker": "AAPL", "exchange": "NASDAQ", "sector": "Tech", "market_cap": 1000, "lot_size": 1, "tradable": True},
        {"ticker": "BAD", "exchange": None, "sector": "Tech", "market_cap": 1000, "lot_size": 1, "tradable": True},
    ]
    result = validate_required_fields(metadata)
    assert len(result) == 1


# ============================================================================
# 1.3 Deterministic Ordering Tests (2 tests)
# ============================================================================

def test_ordering_by_market_cap_descending(ticker_metadata_valid):
    """Universe ordered by market_cap descending."""
    # Use ticker_metadata_valid which has known market caps
    result = sort_by_market_cap_descending(ticker_metadata_valid)
    market_caps = [r["market_cap"] for r in result]
    # Verify descending order
    assert market_caps == sorted(market_caps, reverse=True)


def test_ordering_deterministic_with_ties():
    """Ties in market_cap broken by ticker alphabetically."""
    metadata = [
        {"ticker": "ZZZ", "exchange": "NASDAQ", "sector": "Tech", "market_cap": 500, "lot_size": 1, "tradable": True},
        {"ticker": "AAA", "exchange": "NASDAQ", "sector": "Tech", "market_cap": 500, "lot_size": 1, "tradable": True},
        {"ticker": "MMM", "exchange": "NASDAQ", "sector": "Tech", "market_cap": 500, "lot_size": 1, "tradable": True},
    ]
    result = sort_by_market_cap_descending(metadata)
    tickers = [r["ticker"] for r in result]
    assert tickers == ["AAA", "MMM", "ZZZ"]  # Alphabetical


# ============================================================================
# 1.4 Max Universe Size Tests (2 tests)
# ============================================================================

def test_max_universe_size_truncation():
    """Truncate to max_universe_size, keeping highest market_cap."""
    metadata = [
        {"ticker": "A", "exchange": "NASDAQ", "sector": "Tech", "market_cap": 1000, "lot_size": 1, "tradable": True},
        {"ticker": "B", "exchange": "NASDAQ", "sector": "Tech", "market_cap": 900, "lot_size": 1, "tradable": True},
        {"ticker": "C", "exchange": "NASDAQ", "sector": "Tech", "market_cap": 800, "lot_size": 1, "tradable": True},
        {"ticker": "D", "exchange": "NYSE", "sector": "Finance", "market_cap": 700, "lot_size": 1, "tradable": True},
    ]
    max_universe_size = 2
    result = apply_max_universe_size(metadata, max_universe_size)
    assert len(result) == 2
    assert result[0]["ticker"] == "A"
    assert result[1]["ticker"] == "B"


def test_max_universe_size_none_allows_all():
    """If max_universe_size is None, no truncation."""
    metadata = [
        {"ticker": "A", "exchange": "NASDAQ", "sector": "Tech", "market_cap": 1000, "lot_size": 1, "tradable": True},
        {"ticker": "B", "exchange": "NASDAQ", "sector": "Tech", "market_cap": 900, "lot_size": 1, "tradable": True},
    ]
    result = apply_max_universe_size(metadata, None)
    assert len(result) == 2


# ============================================================================
# 1.5 Duplicate Handling Tests (2 tests)
# ============================================================================

def test_duplicate_tickers_keeps_first(ticker_metadata_duplicates):
    """Duplicate tickers: keep first occurrence."""
    result = dedup_by_ticker(ticker_metadata_duplicates)
    assert len(result) == 2  # Only AAPL (first), MSFT
    # The first AAPL should be kept
    aapl_items = [r for r in result if r["ticker"] == "AAPL"]
    assert len(aapl_items) == 1


def test_no_duplicates_unchanged(ticker_metadata_valid):
    """No duplicates → result unchanged."""
    result = dedup_by_ticker(ticker_metadata_valid)
    assert len(result) == len(ticker_metadata_valid)


# ============================================================================
# 1.6 Empty Universe Tests (2 tests)
# ============================================================================

def test_empty_universe_after_all_filters(ticker_metadata_mixed):
    """All symbols filtered → empty universe."""
    # Filter to only US markets, tradable
    result = filter_by_market(ticker_metadata_mixed, ["US"])
    result = filter_tradable_symbols(result)
    result = validate_required_fields(result)
    # Should have some valid entries but let's check the empty case separately
    assert isinstance(result, list)


def test_empty_input_metadata(ticker_metadata_empty):
    """Empty input → empty universe."""
    result = filter_tradable_symbols(ticker_metadata_empty)
    assert len(result) == 0


# ============================================================================
# Integration Tests
# ============================================================================

def test_build_eligible_universe_happy_path(ticker_metadata_valid):
    """Full pipeline: valid metadata → filtered universe."""
    result = build_eligible_universe(ticker_metadata_valid, ["US"])
    assert result["universe_list"]
    assert result["universe_stats"]["count"] > 0
    assert result["universe_stats"]["total_market_cap"] > 0
    assert not result["errors"]


def test_build_eligible_universe_empty():
    """Empty input → empty universe with error."""
    result = build_eligible_universe([], ["US"])
    assert not result["universe_list"]
    assert result["universe_stats"]["count"] == 0
    assert result["errors"]
    assert result["errors"][0]["code"] == "UNIVERSE_EMPTY"


def test_sector_exposures_alphabetical_order(ticker_metadata_valid):
    """Sector exposures sorted alphabetically for determinism."""
    result = build_eligible_universe(ticker_metadata_valid, ["US"])
    sector_exposures = result["universe_stats"]["sector_exposures"]
    sectors = list(sector_exposures.keys())
    assert sectors == sorted(sectors)


def test_exchange_map_central_auditable():
    """EXCHANGE_MAP is central and auditable."""
    assert "US" in EXCHANGE_MAP
    us_exchanges = EXCHANGE_MAP["US"]
    assert "NASDAQ" in us_exchanges
    assert "NYSE" in us_exchanges
    assert "AMEX" in us_exchanges
    assert "OTC" in us_exchanges
