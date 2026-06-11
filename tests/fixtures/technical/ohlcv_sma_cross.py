"""OHLCV fixture engineered to produce an SMA cross at last bar."""

# Construct a 21-day series where short SMA(5) crosses above long SMA(20)
# Long SMA will be high initially, then short SMA will jump.
OHLCV_SMA_CROSS = []
for i in range(15):
    OHLCV_SMA_CROSS.append({'date': f'2026-01-{i+1:02d}', 'open': 119.8, 'high': 120.3, 'low': 119.5, 'close': 120.0, 'volume': 100})
for i in range(15, 20):
    OHLCV_SMA_CROSS.append({'date': f'2026-01-{i+1:02d}', 'open': 99.8, 'high': 100.3, 'low': 99.5, 'close': 100.0, 'volume': 100})
"""Deterministic SMA-cross fixture.

First 20 closes are flat at 100.0 (so prior short and long SMAs equal 100.0).
The final close is 200.0 which makes the short-window SMA jump above the
long-window SMA (short crosses above long) for short_window=5, long_window=20.
"""

OHLCV_SMA_CROSS = []
for i in range(20):
     close = 100.0
     OHLCV_SMA_CROSS.append({'date': f'2026-01-{i+1:02d}', 'open': close - 0.1, 'high': close + 0.2, 'low': close - 0.3, 'close': close, 'volume': 100})

# Final day big jump to trigger cross
OHLCV_SMA_CROSS.append({'date': '2026-01-21', 'open': 199.0, 'high': 201.0, 'low': 198.0, 'close': 200.0, 'volume': 200})
