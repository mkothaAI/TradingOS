"""Pure calculation functions for portfolio risk metrics.

Phase 2: All variance/covariance use sample convention (divide by n-1).
ATR uses simple moving average over window (no Wilder smoothing in v1).
"""
from typing import List, Dict
import math


def daily_returns(closes: List[float]) -> List[float]:
    """Compute daily returns from close prices.
    
    Formula: r_t = (close_t / close_{t-1}) - 1
    
    Args:
        closes: ordered list of close prices (at least 2)
        
    Returns:
        list of returns (length = len(closes) - 1)
        
    Raises:
        ValueError: if fewer than 2 observations
    """
    if len(closes) < 2:
        raise ValueError('daily_returns: need at least 2 observations')
    
    returns = []
    for i in range(1, len(closes)):
        r = (closes[i] / closes[i-1]) - 1
        returns.append(r)
    return returns


def sample_variance(values: List[float]) -> float:
    """Compute sample variance (divide by n-1).
    
    Convention: uses sample variance (unbiased estimator).
    Formula: Σ(x_i - mean)^2 / (n - 1)
    
    Args:
        values: list of numbers (at least 2 required)
        
    Returns:
        sample variance (float)
        
    Raises:
        ValueError: if fewer than 2 observations
    """
    if len(values) < 2:
        raise ValueError('sample_variance: need at least 2 observations')
    
    n = len(values)
    mean = sum(values) / n
    sum_sq_dev = sum((x - mean) ** 2 for x in values)
    return sum_sq_dev / (n - 1)


def covariance(values_a: List[float], values_b: List[float]) -> float:
    """Compute sample covariance between two series.
    
    Convention: uses sample covariance (divide by n-1).
    Formula: Σ((a_i - mean_a) * (b_i - mean_b)) / (n - 1)
    
    Args:
        values_a: first series (at least 2 observations)
        values_b: second series (must match length of values_a)
        
    Returns:
        covariance (float)
        
    Raises:
        ValueError: if length < 2 or lengths don't match
    """
    if len(values_a) < 2:
        raise ValueError('covariance: need at least 2 observations')
    if len(values_a) != len(values_b):
        raise ValueError('covariance: series lengths must match')
    
    n = len(values_a)
    mean_a = sum(values_a) / n
    mean_b = sum(values_b) / n
    
    sum_prod_dev = sum((values_a[i] - mean_a) * (values_b[i] - mean_b) for i in range(n))
    return sum_prod_dev / (n - 1)


def covariance_matrix(price_series: Dict[str, List[float]]) -> Dict[str, Dict[str, float]]:
    """Compute covariance matrix from multiple asset price series.
    
    Converts each series to returns, then computes pairwise covariances.
    Pure math function: no lookback requirements enforced here.
    
    Args:
        price_series: dict mapping ticker -> list of close prices
                     (all must be same length >= 2)
                     
    Returns:
        dict of dict {ticker_i: {ticker_j: covariance_ij}}
        
    Raises:
        ValueError: if any series has < 2 observations or lengths don't match
    """
    if not price_series:
        raise ValueError('covariance_matrix: empty price series')
    
    tickers = list(price_series.keys())
    
    # Validate all series exist and have consistent length
    for tk in tickers:
        if tk not in price_series:
            raise ValueError(f'covariance_matrix: missing ticker {tk}')
    
    series_length = len(price_series[tickers[0]])
    for tk in tickers:
        if len(price_series[tk]) != series_length:
            raise ValueError('covariance_matrix: all series must have same length')
        if series_length < 2:
            raise ValueError('covariance_matrix: need at least 2 observations per series')
    
    # Convert to returns
    returns_dict = {}
    for tk in tickers:
        returns_dict[tk] = daily_returns(price_series[tk])
    
    # Compute pairwise covariances
    cov_matrix = {}
    for i, tk_i in enumerate(tickers):
        cov_matrix[tk_i] = {}
        for j, tk_j in enumerate(tickers):
            if i == j:
                # Variance on diagonal
                cov_matrix[tk_i][tk_j] = sample_variance(returns_dict[tk_i])
            else:
                cov_matrix[tk_i][tk_j] = covariance(returns_dict[tk_i], returns_dict[tk_j])
    
    return cov_matrix


def portfolio_variance(weights: Dict[str, float], cov_matrix: Dict[str, Dict[str, float]]) -> float:
    """Compute portfolio variance from weights and covariance matrix.
    
    Formula: Σ_i(W_i^2 σ_i^2) + 2Σ_{i<j}(W_i W_j cov_ij)
    
    Args:
        weights: dict ticker -> weight (should sum to ~1.0)
        cov_matrix: output from covariance_matrix()
        
    Returns:
        portfolio variance (float)
        
    Raises:
        ValueError: if weights don't sum to ~1.0 or missing tickers
    """
    # Check weights sum to ~1.0
    weight_sum = sum(weights.values())
    if abs(weight_sum - 1.0) > 0.001:
        raise ValueError(f'portfolio_variance: weights must sum to 1.0, got {weight_sum}')
    
    # Check all tickers in weights are in cov_matrix
    for tk in weights.keys():
        if tk not in cov_matrix:
            raise ValueError(f'portfolio_variance: ticker {tk} missing from cov_matrix')
    
    tickers = list(weights.keys())
    pvar = 0.0
    
    # Diagonal terms: W_i^2 * σ_i^2
    for i, tk_i in enumerate(tickers):
        w_i = weights[tk_i]
        var_i = cov_matrix[tk_i][tk_i]
        pvar += (w_i ** 2) * var_i
    
    # Off-diagonal terms: 2 * W_i * W_j * cov_ij (for i < j)
    for i in range(len(tickers)):
        for j in range(i + 1, len(tickers)):
            tk_i = tickers[i]
            tk_j = tickers[j]
            w_i = weights[tk_i]
            w_j = weights[tk_j]
            cov_ij = cov_matrix[tk_i][tk_j]
            pvar += 2 * w_i * w_j * cov_ij
    
    return pvar


def annualize_volatility(daily_volatility: float, annualization_factor: float = 252.0) -> float:
    """Convert daily volatility to annualized volatility.
    
    Formula: annual_vol = daily_vol * sqrt(annualization_factor)
    
    Convention: annualization_factor=252.0 (trading days/year) is example-derived from Varsity.
    Requires human confirmation before becoming production default.
    
    Args:
        daily_volatility: daily volatility (float, e.g., 0.02)
        annualization_factor: default 252 trading days per year
        
    Returns:
        annualized volatility (float)
    """
    return daily_volatility * math.sqrt(annualization_factor)


def empirical_var(returns: List[float], confidence: float) -> float:
    """Compute empirical Value at Risk by percentile method.
    
    Convention: confidence=0.95 (95% VaR) is example-derived from Varsity.
    Requires human confirmation before becoming production default.
    
    Args:
        returns: list of returns (at least 1)
        confidence: confidence level in (0, 1), e.g., 0.95
        
    Returns:
        VaR value (negative number representing loss threshold)
        
    Raises:
        ValueError: if returns empty or confidence not in (0,1)
    """
    if not returns:
        raise ValueError('empirical_var: returns list cannot be empty')
    if not (0 < confidence < 1):
        raise ValueError(f'empirical_var: confidence must be in (0,1), got {confidence}')
    
    # Sort returns
    sorted_returns = sorted(returns)
    n = len(sorted_returns)
    
    # Percentile: select value at (1 - confidence) quantile
    # For 95% confidence, we want the 5th percentile (0.05 quantile)
    percentile_idx = int((1 - confidence) * n)
    # Clamp to valid range
    percentile_idx = max(0, min(percentile_idx, n - 1))
    
    return sorted_returns[percentile_idx]


def atr_helper(highs: List[float], lows: List[float], closes: List[float], window: int = 14) -> float:
    """Compute Average True Range (ATR) using simple moving average.
    
    Convention: ATR in v1 uses simple moving average (SMA) of true range.
    No Wilder smoothing in Phase 2.
    
    Algorithm:
    - TR_i = max(high_i - low_i, abs(high_i - close_{i-1}), abs(low_i - close_{i-1}))
    - ATR = SMA(TR, window)
    
    Args:
        highs: list of high prices (at least window+1)
        lows: list of low prices (same length as highs)
        closes: list of close prices (same length as highs)
        window: lookback window (default 14)
        
    Returns:
        ATR value (float, > 0)
        
    Raises:
        ValueError: if insufficient data or mismatched lengths
    """
    if len(highs) < window + 1:
        raise ValueError(f'atr_helper: need at least {window+1} observations for window={window}')
    if len(highs) != len(lows) or len(highs) != len(closes):
        raise ValueError('atr_helper: highs, lows, closes must have same length')
    
    # Compute true range for each period (starting from period 1, since TR_0 uses close_{-1})
    true_ranges = []
    for i in range(1, len(highs)):
        tr = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i-1]),
            abs(lows[i] - closes[i-1])
        )
        true_ranges.append(tr)
    
    # Simple moving average of TR over window
    atr = sum(true_ranges[-window:]) / window
    
    return atr
