from tests.fixtures.technical.ohlcv_sma_cross import OHLCV_SMA_CROSS

def get_sma(data, window):
    return sum(data[-window:]) / window

def check(closes):
    short_window = 5
    long_window = 20
    sma_short_t = get_sma(closes, short_window)
    sma_long_t = get_sma(closes, long_window)
    prev_series = closes[:-1]
    sma_short_prev = get_sma(prev_series, short_window)
    sma_long_prev = get_sma(prev_series, long_window)
    print(f"Prev: short={sma_short_prev}, long={sma_long_prev}")
    print(f"Curr: short={sma_short_t}, long={sma_long_t}")

closes = [b['close'] for b in OHLCV_SMA_CROSS]
print("Original:")
check(closes)

# Try making it cross: set early closes lower
new_closes = []
base = 100.0
for i in range(21):
    close = base + i * 0.5
    new_closes.append(close)

# Adjust to force sma_short_prev < sma_long_prev
# Current sma_long_prev is avg of first 20: 100 to 109.5 => 104.75
# Current sma_short_prev is avg of indices 15,16,17,18,19: 107.5, 108, 108.5, 109# Current sma_short_prev is a drop the short ones.

for i in range(15):
    new_closes[i] = 120.0 # High values for long SMA

for i in range(15, 21):
    new_closes[i] = 100.0 # Low values to start with

new_closes[20] = 150.0 # Big jump at the end

print("\nModified:")
check(new_closes)
