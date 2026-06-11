"""Fixtures for Fundamental engine tests."""
import json
import pytest
from datetime import date
from backend.schemas.shared import RequestMeta


@pytest.fixture
def request_meta():
    """Standard request metadata."""
    return RequestMeta(request_id="REQ-FUND-001", as_of_date=date(2024, 1, 15))


@pytest.fixture
def fundamental_data_valid():
    """Valid fundamental data for 5 tickers."""
    return {
        "TICKER1": {"roe": 0.15, "net_margin": 0.20, "debt_ebitda": 1.5},
        "TICKER2": {"roe": 0.12, "net_margin": 0.18, "debt_ebitda": 2.0},
        "TICKER3": {"roe": 0.08, "net_margin": 0.10, "debt_ebitda": 3.0},
        "TICKER4": {"roe": 0.18, "net_margin": 0.25, "debt_ebitda": 1.0},
        "TICKER5": {"roe": 0.05, "net_margin": 0.05, "debt_ebitda": 4.0},
    }


@pytest.fixture
def fundamental_data_missing_roe():
    """Data with some ROE values missing."""
    return {
        "TICKER1": {"roe": None, "net_margin": 0.20, "debt_ebitda": 1.5},
        "TICKER2": {"roe": 0.12, "net_margin": 0.18, "debt_ebitda": 2.0},
        "TICKER3": {"net_margin": 0.10, "debt_ebitda": 3.0},  # Missing roe key
    }


@pytest.fixture
def fundamental_data_missing_margin():
    """Data with some Net Margin values missing."""
    return {
        "TICKER1": {"roe": 0.15, "net_margin": None, "debt_ebitda": 1.5},
        "TICKER2": {"roe": 0.12, "net_margin": 0.18, "debt_ebitda": 2.0},
        "TICKER3": {"roe": 0.10, "debt_ebitda": 3.0},  # Missing net_margin key
    }


@pytest.fixture
def fundamental_data_missing_debt():
    """Data with some Debt/EBITDA values missing."""
    return {
        "TICKER1": {"roe": 0.15, "net_margin": 0.20, "debt_ebitda": None},
        "TICKER2": {"roe": 0.12, "net_margin": 0.18, "debt_ebitda": 2.0},
        "TICKER3": {"roe": 0.10, "net_margin": 0.15},  # Missing debt_ebitda key
    }


@pytest.fixture
def fundamental_data_all_missing():
    """Data with all required fields missing."""
    return {
        "TICKER1": {},
        "TICKER2": {},
        "TICKER3": {},
    }


@pytest.fixture
def fundamental_config_roe_only():
    """Config with ROE check only."""
    return {"min_roe": 0.12}


@pytest.fixture
def fundamental_config_margin_only():
    """Config with Net Margin check only."""
    return {"min_net_margin": 0.15}


@pytest.fixture
def fundamental_config_debt_only():
    """Config with Debt/EBITDA check only."""
    return {"max_debt_ebitda": 2.5}


@pytest.fixture
def fundamental_config_multiple():
    """Config with multiple checks."""
    return {
        "min_roe": 0.10,
        "min_net_margin": 0.12,
        "max_debt_ebitda": 3.0,
    }


@pytest.fixture
def fundamental_config_boundary():
    """Config with boundary values (pass on equality)."""
    return {
        "min_roe": 0.15,
        "min_net_margin": 0.20,
        "max_debt_ebitda": 1.5,
    }


@pytest.fixture
def fundamental_config_empty():
    """Empty config (should pass all tickers)."""
    return {}
