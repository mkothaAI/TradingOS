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
    if sma_short_prev <= sma_long_prev and sma_short_t > sma_long_t:
        return 1
    return 0

closes = [120.0]*15 + [100.0]*5 + [200.0]
print("Testing with [120]*15 + [100]*5 + [200]")
print(f"Signal: {check(closes)}")
