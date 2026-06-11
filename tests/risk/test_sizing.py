"""Unit tests for Phase 2 position sizing functions.

Tests all business-level sizing models: position_size_total_equity,
position_size_percentage_volatility, position_size_percentage_margin,
enforce_max_position_cap.
"""
import pytest
import sys
import os

# Setup path for imports
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from backend.engines.risk.sizing import (
    position_size_total_equity,
    position_size_percentage_volatility,
    position_size_percentage_margin,
    enforce_max_position_cap
)


class TestPositionSizeTotalEquity:
    """Tests for position_size_total_equity()."""
    
    def test_basic_sizing(self):
        """Test basic position size calculation."""
        # equity=100k, risk=1%, stop_distance=100 -> qty=10
        qty = position_size_total_equity(100000.0, 0.01, 100.0)
        assert qty == 10
    
    def test_small_stop_large_qty(self):
        """Test with small stop distance -> larger position."""
        # equity=100k, risk=1%, stop=50 -> qty=20
        qty = position_size_total_equity(100000.0, 0.01, 50.0)
        assert qty == 20
    
    def test_large_stop_small_qty(self):
        """Test with large stop distance -> smaller position."""
        # equity=100k, risk=1%, stop=500 -> qty=2
        qty = position_size_total_equity(100000.0, 0.01, 500.0)
        assert qty == 2
    
    def test_zero_risk_zero_qty(self):
        """Test zero risk percent -> zero position."""
        qty = position_size_total_equity(100000.0, 0.0, 100.0)
        assert qty == 0
    
    def test_invalid_equity_error(self):
        """Test error with non-positive equity."""
        with pytest.raises(ValueError, match='total_equity must be > 0'):
            position_size_total_equity(-100000.0, 0.01, 100.0)
        with pytest.raises(ValueError, match='total_equity must be > 0'):
            position_size_total_equity(0.0, 0.01, 100.0)
    
    def test_invalid_risk_error(self):
        """Test error with negative risk."""
        with pytest.raises(ValueError, match='per_trade_risk_pct must be >= 0'):
            position_size_total_equity(100000.0, -0.01, 100.0)
    
    def test_invalid_stop_distance_error(self):
        """Test error with non-positive stop distance."""
        with pytest.raises(ValueError, match='stop_distance_per_share must be > 0'):
            position_size_total_equity(100000.0, 0.01, 0.0)
        with pytest.raises(ValueError, match='stop_distance_per_share must be > 0'):
            position_size_total_equity(100000.0, 0.01, -100.0)


class TestPositionSizePercentageVolatility:
    """Tests for position_size_percentage_volatility()."""
    
    def test_basic_atr_sizing(self):
        """Test ATR-based position sizing."""
        # equity=100k, risk=1%, ATR=50, multiplier=2 -> stop=100 -> qty=10
        qty = position_size_percentage_volatility(100000.0, 0.01, 50.0, 2.0)
        assert qty == 10
    
    def test_higher_multiplier_smaller_qty(self):
        """Test that higher multiplier -> larger stop -> smaller qty."""
        qty_m1 = position_size_percentage_volatility(100000.0, 0.01, 50.0, 1.0)  # stop=50 -> qty=20
        qty_m2 = position_size_percentage_volatility(100000.0, 0.01, 50.0, 2.0)  # stop=100 -> qty=10
        assert qty_m2 < qty_m1
    
    def test_higher_atr_smaller_qty(self):
        """Test that higher ATR -> larger stop -> smaller qty."""
        qty_atr50 = position_size_percentage_volatility(100000.0, 0.01, 50.0, 2.0)  # stop=100 -> qty=10
        qty_atr100 = position_size_percentage_volatility(100000.0, 0.01, 100.0, 2.0)  # stop=200 -> qty=5
        assert qty_atr100 < qty_atr50
    
    def test_invalid_atr_error(self):
        """Test error with non-positive ATR."""
        with pytest.raises(ValueError, match='atr_value must be > 0'):
            position_size_percentage_volatility(100000.0, 0.01, 0.0, 2.0)
        with pytest.raises(ValueError, match='atr_value must be > 0'):
            position_size_percentage_volatility(100000.0, 0.01, -50.0, 2.0)
    
    def test_invalid_multiplier_error(self):
        """Test error with non-positive multiplier."""
        with pytest.raises(ValueError, match='atr_multiplier must be > 0'):
            position_size_percentage_volatility(100000.0, 0.01, 50.0, 0.0)
        with pytest.raises(ValueError, match='atr_multiplier must be > 0'):
            position_size_percentage_volatility(100000.0, 0.01, 50.0, -2.0)


class TestPositionSizePercentageMargin:
    """Tests for position_size_percentage_margin()."""
    
    def test_basic_margin_sizing(self):
        """Test basic margin-constrained sizing."""
        # equity=100k, margin_pct=0.5, price=500 -> qty=100
        qty = position_size_percentage_margin(100000.0, 0.5, 500.0)
        assert qty == 100
    
    def test_lower_price_higher_qty(self):
        """Test that lower price -> higher qty."""
        qty_p100 = position_size_percentage_margin(100000.0, 0.5, 100.0)  # qty=500
        qty_p500 = position_size_percentage_margin(100000.0, 0.5, 500.0)  # qty=100
        assert qty_p100 > qty_p500
    
    def test_higher_margin_pct_higher_qty(self):
        """Test that higher margin % -> higher qty."""
        qty_m30 = position_size_percentage_margin(100000.0, 0.3, 500.0)  # qty=60
        qty_m50 = position_size_percentage_margin(100000.0, 0.5, 500.0)  # qty=100
        assert qty_m50 > qty_m30
    
    def test_invalid_equity_error(self):
        """Test error with non-positive equity."""
        with pytest.raises(ValueError, match='total_equity must be > 0'):
            position_size_percentage_margin(0.0, 0.5, 500.0)
        with pytest.raises(ValueError, match='total_equity must be > 0'):
            position_size_percentage_margin(-100000.0, 0.5, 500.0)
    
    def test_invalid_margin_pct_error(self):
        """Test error with non-positive margin percent."""
        with pytest.raises(ValueError, match='max_margin_pct must be > 0'):
            position_size_percentage_margin(100000.0, 0.0, 500.0)
        with pytest.raises(ValueError, match='max_margin_pct must be > 0'):
            position_size_percentage_margin(100000.0, -0.5, 500.0)
    
    def test_invalid_price_error(self):
        """Test error with non-positive price."""
        with pytest.raises(ValueError, match='current_price must be > 0'):
            position_size_percentage_margin(100000.0, 0.5, 0.0)
        with pytest.raises(ValueError, match='current_price must be > 0'):
            position_size_percentage_margin(100000.0, 0.5, -500.0)


class TestEnforceMaxPositionCap:
    """Tests for enforce_max_position_cap()."""
    
    def test_within_cap_returns_qty(self):
        """Test position within cap -> returns (qty, None)."""
        qty, reason = enforce_max_position_cap(100, 100000.0, 500.0, 0.10)
        # notional = 100 * 500 = 50k, max = 100k * 0.10 = 10k... wait, 50k > 10k
        # Actually: notional = 50k, max_allowed = 10k, so exceeds cap
        
        # Let me recalculate: qty=10, max_cap = 10%, so notional=5k, max=10k
        qty, reason = enforce_max_position_cap(10, 100000.0, 500.0, 0.10)
        assert qty == 10
        assert reason is None
    
    def test_exceeds_cap_returns_zero(self):
        """Test position exceeding cap -> returns (0, 'POSITION_CAP_EXCEEDED')."""
        # notional = 100 * 500 = 50k, max = 100k * 0.10 = 10k -> exceeds
        qty, reason = enforce_max_position_cap(100, 100000.0, 500.0, 0.10)
        assert qty == 0
        assert reason == 'POSITION_CAP_EXCEEDED'
    
    def test_exactly_at_cap_returns_qty(self):
        """Test position exactly at cap -> returns (qty, None)."""
        # notional = 20 * 500 = 10k, max = 100k * 0.10 = 10k -> exactly at cap
        qty, reason = enforce_max_position_cap(20, 100000.0, 500.0, 0.10)
        assert qty == 20
        assert reason is None
    
    def test_zero_qty_always_allowed(self):
        """Test zero position always passes cap."""
        qty, reason = enforce_max_position_cap(0, 100000.0, 500.0, 0.01)
        assert qty == 0
        assert reason is None
    
    def test_invalid_equity_error(self):
        """Test error with non-positive equity."""
        with pytest.raises(ValueError, match='total_equity must be > 0'):
            enforce_max_position_cap(10, 0.0, 500.0, 0.10)
        with pytest.raises(ValueError, match='total_equity must be > 0'):
            enforce_max_position_cap(10, -100000.0, 500.0, 0.10)
    
    def test_invalid_price_error(self):
        """Test error with non-positive price."""
        with pytest.raises(ValueError, match='current_price must be > 0'):
            enforce_max_position_cap(10, 100000.0, 0.0, 0.10)
        with pytest.raises(ValueError, match='current_price must be > 0'):
            enforce_max_position_cap(10, 100000.0, -500.0, 0.10)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
