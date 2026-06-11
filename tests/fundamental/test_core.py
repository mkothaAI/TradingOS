"""Core tests for Fundamental engine (Phase 7).

16 tests: validation, pass cases, fail cases, missing data, config, ordering, integration.
"""
import pytest
from datetime import date
from backend.engines.fundamental.calc import (
    validate_config_keys,
    check_roe_threshold,
    check_net_margin_threshold,
    check_debt_ebitda_ceiling,
    evaluate_fundamental_checks,
    evaluate_fundamental_universe,
    KNOWN_CONFIG_KEYS,
    CANONICAL_REASON_ORDER,
)
from backend.engines.fundamental.assembler import (
    compute_fundamental,
    build_fundamental_response,
)
from backend.schemas.shared import RequestMeta


# ============================================================================
# HAPPY-PATH PASS TESTS (4)
# ============================================================================


def test_empty_config_pass_all(fundamental_data_valid, fundamental_config_empty):
    """Empty config should pass all tickers (no checks to fail)."""
    result = evaluate_fundamental_universe(fundamental_data_valid, fundamental_config_empty)
    for ticker in fundamental_data_valid.keys():
        assert result[ticker]["fundamental_pass"] is True
        assert result[ticker]["reasons"] == []


def test_single_roe_check_pass(fundamental_data_valid):
    """Single ROE check passing for all tickers."""
    config = {"min_roe": 0.05}  # All tickers >= 0.05
    result = evaluate_fundamental_universe(fundamental_data_valid, config)
    for ticker in fundamental_data_valid.keys():
        assert result[ticker]["fundamental_pass"] is True
        assert result[ticker]["reasons"] == []


def test_multiple_checks_pass(fundamental_data_valid):
    """Multiple checks passing."""
    config = {
        "min_roe": 0.05,
        "min_net_margin": 0.05,
        "max_debt_ebitda": 5.0,
    }
    result = evaluate_fundamental_universe(fundamental_data_valid, config)
    for ticker in fundamental_data_valid.keys():
        assert result[ticker]["fundamental_pass"] is True
        assert result[ticker]["reasons"] == []


def test_boundary_values_pass(fundamental_config_boundary):
    """Pass on boundary (equality): ROE >= 0.15, Margin >= 0.20, Debt <= 1.5."""
    data = {
        "T1": {"roe": 0.15, "net_margin": 0.20, "debt_ebitda": 1.5},
        "T2": {"roe": 0.15, "net_margin": 0.20, "debt_ebitda": 1.5},
    }
    result = evaluate_fundamental_universe(data, fundamental_config_boundary)
    for ticker in data.keys():
        assert result[ticker]["fundamental_pass"] is True
        assert result[ticker]["reasons"] == []


# ============================================================================
# FAIL TESTS (3)
# ============================================================================


def test_roe_fail(fundamental_data_valid):
    """ROE below threshold (0.08 < 0.10)."""
    config = {"min_roe": 0.10}
    result = evaluate_fundamental_universe(fundamental_data_valid, config)
    # TICKER3 has ROE 0.08 (fails), others pass
    assert result["TICKER3"]["fundamental_pass"] is False
    assert result["TICKER3"]["reasons"] == ["ROE_FAIL"]
    assert result["TICKER1"]["fundamental_pass"] is True


def test_margin_fail(fundamental_data_valid):
    """Net Margin below threshold (0.05 < 0.15)."""
    config = {"min_net_margin": 0.15}
    result = evaluate_fundamental_universe(fundamental_data_valid, config)
    # TICKER3 and TICKER5 have margins < 0.15 (fail)
    assert result["TICKER3"]["fundamental_pass"] is False
    assert "MARGIN_FAIL" in result["TICKER3"]["reasons"]
    assert result["TICKER5"]["fundamental_pass"] is False
    assert "MARGIN_FAIL" in result["TICKER5"]["reasons"]


def test_debt_fail(fundamental_data_valid):
    """Debt/EBITDA above ceiling (3.0 > 2.5)."""
    config = {"max_debt_ebitda": 2.5}
    result = evaluate_fundamental_universe(fundamental_data_valid, config)
    # TICKER3 has debt 3.0 (fails), TICKER5 has debt 4.0 (fails)
    assert result["TICKER3"]["fundamental_pass"] is False
    assert "DEBT_FAIL" in result["TICKER3"]["reasons"]
    assert result["TICKER5"]["fundamental_pass"] is False
    assert "DEBT_FAIL" in result["TICKER5"]["reasons"]


# ============================================================================
# MISSING DATA TESTS (5)
# ============================================================================


def test_roe_missing_code(fundamental_data_missing_roe):
    """ROE missing should emit ROE_MISSING, not ROE_FAIL."""
    config = {"min_roe": 0.12}
    result = evaluate_fundamental_universe(fundamental_data_missing_roe, config)
    # TICKER1 has roe: None (missing), TICKER3 has no roe key (missing)
    assert result["TICKER1"]["fundamental_pass"] is False
    assert result["TICKER1"]["reasons"] == ["ROE_MISSING"]
    assert result["TICKER3"]["fundamental_pass"] is False
    assert result["TICKER3"]["reasons"] == ["ROE_MISSING"]


def test_margin_missing_code(fundamental_data_missing_margin):
    """Net Margin missing should emit MARGIN_MISSING."""
    config = {"min_net_margin": 0.12}
    result = evaluate_fundamental_universe(fundamental_data_missing_margin, config)
    # TICKER1 has net_margin: None (missing), TICKER3 has no net_margin key
    assert result["TICKER1"]["fundamental_pass"] is False
    assert result["TICKER1"]["reasons"] == ["MARGIN_MISSING"]
    assert result["TICKER3"]["fundamental_pass"] is False
    assert result["TICKER3"]["reasons"] == ["MARGIN_MISSING"]


def test_debt_missing_code(fundamental_data_missing_debt):
    """Debt/EBITDA missing should emit DEBT_MISSING."""
    config = {"max_debt_ebitda": 2.5}
    result = evaluate_fundamental_universe(fundamental_data_missing_debt, config)
    # TICKER1 has debt_ebitda: None (missing), TICKER3 has no debt_ebitda key
    assert result["TICKER1"]["fundamental_pass"] is False
    assert result["TICKER1"]["reasons"] == ["DEBT_MISSING"]
    assert result["TICKER3"]["fundamental_pass"] is False
    assert result["TICKER3"]["reasons"] == ["DEBT_MISSING"]


def test_multiple_missing_same_ticker():
    """Multiple fields missing for same ticker."""
    data = {"TICKER1": {"roe": None, "net_margin": None}}
    config = {"min_roe": 0.10, "min_net_margin": 0.10}
    result = evaluate_fundamental_universe(data, config)
    assert result["TICKER1"]["fundamental_pass"] is False
    # Reasons in canonical order: ROE_MISSING (0), MARGIN_MISSING (1)
    assert result["TICKER1"]["reasons"] == ["ROE_MISSING", "MARGIN_MISSING"]


def test_unconfigured_missing_field_ignored():
    """Missing field not in config should not affect pass."""
    ticker_data = {"roe": 0.15, "net_margin": 0.20}  # debt_ebitda missing
    config = {"min_roe": 0.10, "min_net_margin": 0.12}  # debt_ebitda not configured
    result = evaluate_fundamental_checks("TICKER1", ticker_data, config)
    assert result["fundamental_pass"] is True
    assert result["reasons"] == []


# ============================================================================
# CONFIG VALIDATION TESTS (2)
# ============================================================================


def test_unknown_config_keys_raise_error():
    """Unknown config keys should raise ValueError."""
    config = {"min_roe": 0.10, "unknown_key": 1.0}
    data = {"TICKER1": {"roe": 0.15}}
    with pytest.raises(ValueError, match="Unknown config keys"):
        evaluate_fundamental_checks("TICKER1", data, config)


def test_known_config_keys_accepted():
    """All known config keys should be accepted without error."""
    config = {"min_roe": 0.10, "min_net_margin": 0.12, "max_debt_ebitda": 2.5}
    ticker_data = {"roe": 0.15, "net_margin": 0.20, "debt_ebitda": 1.5}
    # Should not raise
    result = evaluate_fundamental_checks("TICKER1", ticker_data, config)
    assert result["fundamental_pass"] is True


# ============================================================================
# DETERMINISTIC ORDERING TEST (1)
# ============================================================================


def test_reason_codes_canonical_order():
    """Reason codes must be in canonical order: ROE → Margin → Debt."""
    # Create a ticker that fails multiple checks
    ticker_data = {"roe": 0.05, "net_margin": 0.05, "debt_ebitda": 5.0}
    config = {"min_roe": 0.10, "min_net_margin": 0.10, "max_debt_ebitda": 3.0}
    result = evaluate_fundamental_checks("TICKER1", ticker_data, config)
    # Should have all three failures
    assert result["fundamental_pass"] is False
    # Order: ROE_FAIL (order 0), MARGIN_FAIL (order 1), DEBT_FAIL (order 2)
    assert result["reasons"] == ["ROE_FAIL", "MARGIN_FAIL", "DEBT_FAIL"]


# ============================================================================
# INTEGRATION TEST (1)
# ============================================================================


def test_integration_multiple_tickers_mixed():
    """Multiple tickers, mixed results: pass, fail, missing."""
    data = {
        "PASS": {"roe": 0.15, "net_margin": 0.20, "debt_ebitda": 1.5},
        "FAIL_ROE": {"roe": 0.08, "net_margin": 0.20, "debt_ebitda": 1.5},
        "FAIL_MARGIN": {"roe": 0.15, "net_margin": 0.05, "debt_ebitda": 1.5},
        "FAIL_DEBT": {"roe": 0.15, "net_margin": 0.20, "debt_ebitda": 4.0},
        "MISSING_ALL": {"roe": None, "net_margin": None, "debt_ebitda": None},
    }
    config = {
        "min_roe": 0.10,
        "min_net_margin": 0.10,
        "max_debt_ebitda": 3.0,
    }
    result = evaluate_fundamental_universe(data, config)
    
    # Pass case
    assert result["PASS"]["fundamental_pass"] is True
    assert result["PASS"]["reasons"] == []
    
    # Fail ROE
    assert result["FAIL_ROE"]["fundamental_pass"] is False
    assert result["FAIL_ROE"]["reasons"] == ["ROE_FAIL"]
    
    # Fail Margin
    assert result["FAIL_MARGIN"]["fundamental_pass"] is False
    assert result["FAIL_MARGIN"]["reasons"] == ["MARGIN_FAIL"]
    
    # Fail Debt
    assert result["FAIL_DEBT"]["fundamental_pass"] is False
    assert result["FAIL_DEBT"]["reasons"] == ["DEBT_FAIL"]
    
    # Missing all fields
    assert result["MISSING_ALL"]["fundamental_pass"] is False
    # All three missing in canonical order
    assert result["MISSING_ALL"]["reasons"] == ["ROE_MISSING", "MARGIN_MISSING", "DEBT_MISSING"]


# ============================================================================
# ASSEMBLER/RESPONSE TESTS (Contract validation)
# ============================================================================


def test_compute_fundamental_assembler(fundamental_data_valid, fundamental_config_multiple):
    """Assembler orchestrates fundamental computation correctly."""
    result = compute_fundamental(fundamental_data_valid, fundamental_config_multiple)
    assert isinstance(result, dict)
    for ticker in fundamental_data_valid.keys():
        assert "fundamental_pass" in result[ticker]
        assert "reasons" in result[ticker]


def test_build_fundamental_response(fundamental_data_valid, fundamental_config_multiple, request_meta):
    """Response contract properly formatted."""
    fundamental_result = evaluate_fundamental_universe(
        fundamental_data_valid, fundamental_config_multiple
    )
    response = build_fundamental_response(fundamental_result, request_meta)
    
    # Contract validation
    assert response.meta == request_meta
    assert response.status.value == "OK"
    assert isinstance(response.results, dict)
    assert len(response.results) == len(fundamental_data_valid)
    
    # Each FundamentalItem has required fields
    for ticker, item in response.results.items():
        assert hasattr(item, "fundamental_pass")
        assert hasattr(item, "reasons")
        assert isinstance(item.fundamental_pass, bool)
        assert isinstance(item.reasons, list)
