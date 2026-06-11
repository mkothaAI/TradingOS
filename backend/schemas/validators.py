"""Business-level validators/helpers separate from shape schemas."""
from typing import Dict, List


def check_min_lookback(price_series: Dict[str, list], min_lookback: int = 60) -> Dict[str, str]:
    """Return dict of ticker->error_code for tickers that fail min lookback."""
    errors = {}
    for tk, series in price_series.items():
        if not isinstance(series, list) or len(series) < min_lookback:
            errors[tk] = 'INSUFFICIENT_HISTORY'
    return errors
