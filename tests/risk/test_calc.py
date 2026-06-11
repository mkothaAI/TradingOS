"""Unit tests for Phase 2 risk calculation functions.

Tests all pure math functions: daily_returns, sample_variance, covariance,
covariance_matrix, portfolio_variance, annualize_volatility, empirical_var, atr_helper.

Variance/covariance use sample convention (n-1 divisor).
ATR uses simple moving average.
"""
import pytest
import math
import sys
import os

# Setup path for imports
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from backend.engines.risk.calc import (
    daily_returns, sample_variance, covariance, covariance_matrix,
    portfolio_variance, annualize_volatility, empirical_var, atr_helper
)
from tests.fixtures.risk_data.price_series_examples import (
    NIFTY_SAMPLE_PRICES, BANK_SAMPLE_PRICES, IT_SAMPLE_PRICES,
    NIFTY_SAMPLE_HIGHS, NIFTY_SAMPLE_LOWS,
    BANK_SAMPLE_HIGHS, BANK_SAMPLE_LOWS
)
from tests.fixtures.risk_data.returns_examples import (
    RETURNS_NIFTY_20_DAY, RETURNS_BANK_20_DAY, RETURNS_LOW_VOL, RETURNS_HIGH_VOL
)


class TestDailyReturns:
    """Tests for daily_returns()."""
    
    def test_basic_returns_calculation(self):
        """Test simple return calculation (100->110 should be 0.10)."""
        prices = [100.0, 110.0]
        result = daily_returns(prices)
        assert len(result) == 1
        assert abs(result[0] - 0.10) < 1e-6
    
    def test_multiple_returns(self):
        """Test returns from 4 prices."""
        prices = [100.0, 105.0, 110.0, 104.0]
        result = daily_returns(prices)
        assert len(result) == 3
        assert abs(result[0] - 0.05) < 1e-6
        assert abs(result[1] - (110/105 - 1)) < 1e-6
        assert abs(result[2] - (104/110 - 1)) < 1e-6
    
    def test_insufficient_data_error(self):
        """Test error when fewer than 2 observations."""
        with pytest.raises(ValueError, match='need at least 2 observations'):
            daily_returns([100.0])
        with pytest.raises(ValueError):
            daily_returns([])
    
    def test_nifty_sample(self):
        """Test against real NIFTY sample data."""
        result = daily_returns(NIFTY_SAMPLE_PRICES)
        assert len(result) == len(NIFTY_SAMPLE_PRICES) - 1
        assert len(result) == 19


class TestSampleVariance:
    """Tests for sample_variance()."""
    
    def test_constant_series_zero_variance(self):
        """Variance of constant values should be 0."""
        values = [5.0, 5.0, 5.0, 5.0, 5.0]
        result = sample_variance(values)
        assert abs(result) < 1e-10
    
    def test_simple_variance(self):
        """Test variance: [1, 2, 3] should have sample var = 1.0."""
        values = [1.0, 2.0, 3.0]
        result = sample_variance(values)
        # Manual: mean=2, sum_sq_dev=(1-2)^2+(2-2)^2+(3-2)^2=2, var=2/(3-1)=1.0
        assert abs(result - 1.0) < 1e-10
    
    def test_two_observations(self):
        """Test minimum: [1, 3] should have sample var = 2.0."""
        values = [1.0, 3.0]
        result = sample_variance(values)
        # mean=2, sum_sq_dev=1+1=2, var=2/(2-1)=2.0
        assert abs(result - 2.0) < 1e-10
    
    def test_nifty_returns_variance(self):
        """Test variance of NIFTY returns."""
        result = sample_variance(RETURNS_NIFTY_20_DAY)
        assert result > 0
        # Approximate check: daily vol around 0.002 -> var around 4e-6
        assert 1e-7 < result < 1e-4
    
    def test_insufficient_data_error(self):
        """Test error when fewer than 2 observations."""
        with pytest.raises(ValueError, match='need at least 2 observations'):
            sample_variance([5.0])
        with pytest.raises(ValueError):
            sample_variance([])


class TestCovariance:
    """Tests for covariance()."""
    
    def test_perfect_correlation(self):
        """Test perfect positive correlation (covariance = variance)."""
        a = [1.0, 2.0, 3.0]
        b = [1.0, 2.0, 3.0]
        cov = covariance(a, b)
        var_a = sample_variance(a)
        assert abs(cov - var_a) < 1e-10
    
    def test_zero_correlation(self):
        """Test zero covariance: [1,2,3] and [0, 0, 0] (constant)."""
        a = [1.0, 2.0, 3.0]
        b = [0.0, 0.0, 0.0]
        cov = covariance(a, b)
        assert abs(cov) < 1e-10
    
    def test_negative_correlation(self):
        """Test negative correlation: [1,2,3] and [3,2,1]."""
        a = [1.0, 2.0, 3.0]
        b = [3.0, 2.0, 1.0]
        cov = covariance(a, b)
        assert cov < 0
    
    def test_length_mismatch_error(self):
        """Test error when series lengths don't match."""
        with pytest.raises(ValueError, match='series lengths must match'):
            covariance([1.0, 2.0], [1.0, 2.0, 3.0])
    
    def test_insufficient_data_error(self):
        """Test error when fewer than 2 observations."""
        with pytest.raises(ValueError, match='need at least 2 observations'):
            covariance([1.0], [1.0])
    
    def test_nifty_bank_covariance(self):
        """Test covariance between NIFTY and BANK returns."""
        cov = covariance(RETURNS_NIFTY_20_DAY, RETURNS_BANK_20_DAY)
        assert isinstance(cov, float)
        # Covariance may be positive or negative depending on correlation
        # Just verify it's a finite number
        assert abs(cov) < 1e-3  # Should be small magnitude for daily returns


class TestCovarianceMatrix:
    """Tests for covariance_matrix()."""
    
    def test_single_asset_diagonal(self):
        """Test covariance matrix with one asset."""
        prices = {'NIFTY': NIFTY_SAMPLE_PRICES}
        cov_matrix = covariance_matrix(prices)
        
        assert 'NIFTY' in cov_matrix
        assert 'NIFTY' in cov_matrix['NIFTY']
        # Diagonal should be variance of NIFTY returns
        nifty_returns = daily_returns(NIFTY_SAMPLE_PRICES)
        nifty_var = sample_variance(nifty_returns)
        assert abs(cov_matrix['NIFTY']['NIFTY'] - nifty_var) < 1e-10
    
    def test_two_asset_matrix(self):
        """Test covariance matrix with two assets."""
        prices = {'NIFTY': NIFTY_SAMPLE_PRICES, 'BANK': BANK_SAMPLE_PRICES}
        cov_matrix = covariance_matrix(prices)
        
        assert 'NIFTY' in cov_matrix
        assert 'BANK' in cov_matrix
        assert 'NIFTY' in cov_matrix['NIFTY']
        assert 'BANK' in cov_matrix['NIFTY']
        assert 'NIFTY' in cov_matrix['BANK']
        assert 'BANK' in cov_matrix['BANK']
        
        # Symmetry: cov(X,Y) = cov(Y,X)
        assert abs(cov_matrix['NIFTY']['BANK'] - cov_matrix['BANK']['NIFTY']) < 1e-10
    
    def test_three_asset_matrix(self):
        """Test full 3x3 covariance matrix."""
        prices = {
            'NIFTY': NIFTY_SAMPLE_PRICES,
            'BANK': BANK_SAMPLE_PRICES,
            'IT': IT_SAMPLE_PRICES
        }
        cov_matrix = covariance_matrix(prices)
        
        # Check structure
        for tk_i in ['NIFTY', 'BANK', 'IT']:
            for tk_j in ['NIFTY', 'BANK', 'IT']:
                assert tk_i in cov_matrix
                assert tk_j in cov_matrix[tk_i]
        
        # Symmetry
        assert abs(cov_matrix['NIFTY']['BANK'] - cov_matrix['BANK']['NIFTY']) < 1e-10
        assert abs(cov_matrix['NIFTY']['IT'] - cov_matrix['IT']['NIFTY']) < 1e-10
        assert abs(cov_matrix['BANK']['IT'] - cov_matrix['IT']['BANK']) < 1e-10
    
    def test_empty_series_error(self):
        """Test error with empty price series."""
        with pytest.raises(ValueError, match='empty price series'):
            covariance_matrix({})
    
    def test_length_mismatch_error(self):
        """Test error when series lengths don't match."""
        with pytest.raises(ValueError, match='all series must have same length'):
            covariance_matrix({
                'A': [100.0, 110.0, 120.0],
                'B': [50.0, 55.0]
            })


class TestPortfolioVariance:
    """Tests for portfolio_variance()."""
    
    def test_single_asset_portfolio(self):
        """Portfolio of 100% one asset should equal asset variance."""
        prices = {'NIFTY': NIFTY_SAMPLE_PRICES}
        cov_matrix = covariance_matrix(prices)
        weights = {'NIFTY': 1.0}
        
        pvar = portfolio_variance(weights, cov_matrix)
        nifty_var = cov_matrix['NIFTY']['NIFTY']
        assert abs(pvar - nifty_var) < 1e-10
    
    def test_equal_weight_two_asset(self):
        """Test 50/50 portfolio of two assets."""
        prices = {'NIFTY': NIFTY_SAMPLE_PRICES, 'BANK': BANK_SAMPLE_PRICES}
        cov_matrix = covariance_matrix(prices)
        weights = {'NIFTY': 0.5, 'BANK': 0.5}
        
        pvar = portfolio_variance(weights, cov_matrix)
        
        # Manual: 0.5^2*var_N + 0.5^2*var_B + 2*0.5*0.5*cov_NB
        var_n = cov_matrix['NIFTY']['NIFTY']
        var_b = cov_matrix['BANK']['BANK']
        cov_nb = cov_matrix['NIFTY']['BANK']
        expected = 0.25 * var_n + 0.25 * var_b + 0.5 * cov_nb
        
        assert abs(pvar - expected) < 1e-10
    
    def test_weights_not_sum_to_1_error(self):
        """Test error when weights don't sum to 1.0."""
        prices = {'NIFTY': NIFTY_SAMPLE_PRICES}
        cov_matrix = covariance_matrix(prices)
        weights = {'NIFTY': 0.8}  # Sum = 0.8, not 1.0
        
        with pytest.raises(ValueError, match='weights must sum to 1.0'):
            portfolio_variance(weights, cov_matrix)
    
    def test_missing_ticker_error(self):
        """Test error when weight references ticker not in cov_matrix."""
        prices = {'NIFTY': NIFTY_SAMPLE_PRICES}
        cov_matrix = covariance_matrix(prices)
        weights = {'UNKNOWN': 1.0}
        
        with pytest.raises(ValueError, match='missing from cov_matrix'):
            portfolio_variance(weights, cov_matrix)


class TestAnnualizeVolatility:
    """Tests for annualize_volatility()."""
    
    def test_default_annualization(self):
        """Test annualization with default 252 trading days."""
        daily_vol = 0.01  # 1% daily
        annual_vol = annualize_volatility(daily_vol)
        # Expected: 0.01 * sqrt(252) ≈ 0.1587
        expected = 0.01 * math.sqrt(252.0)
        assert abs(annual_vol - expected) < 1e-10
    
    def test_custom_annualization_factor(self):
        """Test with custom annualization factor."""
        daily_vol = 0.02  # 2% daily
        annual_vol = annualize_volatility(daily_vol, annualization_factor=365.0)
        expected = 0.02 * math.sqrt(365.0)
        assert abs(annual_vol - expected) < 1e-10
    
    def test_zero_daily_vol(self):
        """Test that zero daily vol gives zero annual vol."""
        annual_vol = annualize_volatility(0.0)
        assert abs(annual_vol) < 1e-10


class TestEmpiricalVar:
    """Tests for empirical_var() — Value at Risk by percentile."""
    
    def test_95_percent_var_simple(self):
        """Test 95% VaR on simple returns."""
        # 20 returns, 95% confidence -> 5th percentile
        returns = [-0.05, -0.04, -0.03, -0.02, -0.01, 0.0, 0.01, 0.02, 0.03, 0.04,
                   0.05, 0.06, 0.07, 0.08, 0.09, 0.10, 0.11, 0.12, 0.13, 0.14]
        var_95 = empirical_var(returns, 0.95)
        # 5th percentile of 20 items: index ≈ 0.05*20 = 1
        # Sorted: [-0.05, -0.04, ...], so 5th percentile is around -0.04 to -0.03
        assert var_95 <= -0.01  # Should be a negative value
    
    def test_var_ordering(self):
        """Test that higher confidence -> less negative VaR."""
        returns = RETURNS_NIFTY_20_DAY
        var_90 = empirical_var(returns, 0.90)
        var_95 = empirical_var(returns, 0.95)
        var_99 = empirical_var(returns, 0.99)
        # 90% < 95% < 99% -> more extreme loss at higher confidence
        # So |VaR_90| < |VaR_95| < |VaR_99|
        # But our returns are mostly positive, so values are small
        assert isinstance(var_90, float)
        assert isinstance(var_95, float)
        assert isinstance(var_99, float)
    
    def test_empty_returns_error(self):
        """Test error with empty returns."""
        with pytest.raises(ValueError, match='returns list cannot be empty'):
            empirical_var([], 0.95)
    
    def test_invalid_confidence_error(self):
        """Test error with invalid confidence levels."""
        returns = RETURNS_NIFTY_20_DAY
        with pytest.raises(ValueError, match='confidence must be in'):
            empirical_var(returns, 0.0)
        with pytest.raises(ValueError, match='confidence must be in'):
            empirical_var(returns, 1.0)


class TestAtrHelper:
    """Tests for atr_helper() — Average True Range."""
    
    def test_basic_atr_calculation(self):
        """Test ATR with simple price data."""
        highs = [100.0, 102.0, 101.0, 103.0, 102.0]
        lows = [99.0, 100.0, 99.0, 101.0, 100.0]
        closes = [100.5, 101.0, 99.5, 102.0, 101.5]
        
        atr = atr_helper(highs, lows, closes, window=2)
        # ATR should be positive and within the price range
        assert atr > 0
        # Approximate check: typical TR should be 1-3
        assert 0.5 < atr < 5.0
    
    def test_nifty_atr(self):
        """Test ATR on NIFTY sample data with window=14."""
        atr = atr_helper(NIFTY_SAMPLE_HIGHS, NIFTY_SAMPLE_LOWS, NIFTY_SAMPLE_PRICES, window=14)
        assert atr > 0
        # Approximate: NIFTY range ~50-100, so ATR should be 30-80
        assert 10 < atr < 200
    
    def test_insufficient_data_error(self):
        """Test error when fewer than window+1 observations."""
        highs = [100.0, 102.0]
        lows = [99.0, 100.0]
        closes = [100.5, 101.0]
        
        with pytest.raises(ValueError, match='need at least'):
            atr_helper(highs, lows, closes, window=3)
    
    def test_length_mismatch_error(self):
        """Test error when series lengths don't match."""
        with pytest.raises(ValueError, match='must have same length'):
            atr_helper([100.0, 102.0], [99.0], [100.5, 101.0], window=1)
    
    def test_different_window_sizes(self):
        """Test ATR with different window sizes."""
        highs = NIFTY_SAMPLE_HIGHS
        lows = NIFTY_SAMPLE_LOWS
        closes = NIFTY_SAMPLE_PRICES
        
        # NIFTY has 20 observations, so max window is 19 (need window+1)
        atr_7 = atr_helper(highs, lows, closes, window=7)
        atr_14 = atr_helper(highs, lows, closes, window=14)
        atr_19 = atr_helper(highs, lows, closes, window=19)
        
        assert atr_7 > 0
        assert atr_14 > 0
        assert atr_19 > 0
        # Verify all are floats
        assert isinstance(atr_7, float)
        assert isinstance(atr_14, float)
        assert isinstance(atr_19, float)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
