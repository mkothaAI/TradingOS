"""Synthetic return vectors for Phase 2 risk tests."""


RETURNS_NIFTY_20_DAY = [
    0.00266, 0.00265, -0.00105, 0.00211, 0.00158, -0.00105, 0.00265, 0.00155,
    -0.00526, 0.00263, 0.00144, 0.00110, 0.00109, -0.00157, 0.00260, 0.00105,
    -0.00052, 0.00263, 0.00110
]
"""19 daily returns from NIFTY_SAMPLE_PRICES (close-to-close, ~0.1-0.3% typical)"""

RETURNS_BANK_20_DAY = [
    0.01042, 0.01031, 0.01020, -0.00606, 0.01227, 0.00803, -0.00399, 0.00995,
    0.00984, -0.00394, 0.01370, 0.00971, -0.00385, 0.01350, 0.00952, -0.00379,
    0.01327, 0.00926, -0.00373
]
"""19 daily returns from BANK_SAMPLE_PRICES (~0.6-1.4% typical, higher volatility)"""

RETURNS_LOW_VOL = [
    0.0005, 0.0008, -0.0002, 0.0003, 0.0006, -0.0001, 0.0004, 0.0007,
    -0.0003, 0.0002, 0.0006, -0.0002, 0.0004, 0.0008, -0.0001, 0.0003,
    0.0007, -0.0003, 0.0005
]
"""19 returns with low volatility (~0.05% typical, stable/defensive stock)"""

RETURNS_HIGH_VOL = [
    -0.0250, 0.0320, -0.0180, 0.0420, -0.0150, 0.0380, -0.0280, 0.0450,
    -0.0200, 0.0390, -0.0310, 0.0470, -0.0220, 0.0410, -0.0320, 0.0480,
    -0.0240, 0.0460, -0.0330
]
"""19 returns with high volatility (~2-4% swings, cyclical/speculative stock)"""
