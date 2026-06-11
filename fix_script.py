import sys

# Original data from the failing test
data = {"TICKER1": {"roe": 0.15, "net_margin": 0.20}}
config = {"min_roe": 0.10, "min_net_margin": 0.12}

# Re-implementing the function logic locally to debug if it was indeed the code or the environment
def evaluate_fundamental_checks_debug(ticker, data_item, config):
    reasons = []
    if "min_roe" in config:
        roe = data_item.get("roe")
        if roe is None:
            reasons.append("ROE_MISSING")
        elif roe < config["min_roe"]:
            reasons.append("ROE_FAIL")
    if "min_net_margin" in config:
        margin = data_item.get("net_margin")
        if margin is None:
            reasons.append("MARGIN_MISSING")
        elif margin < config["min_net_margin"]:
            reasons.append("MARGIN_FAIL")
    if "max_debt_ebitda" in config:
        debt = data_item.get("debt_ebitda")
        if debt is None:
            reasons.append("DEBT_MISSING")
        elif debt > config["max_debt_ebitda"]:
            reas            reas     ")
    return {"fundamental_pass": len(reasons) == 0, "r    return {"fundamental_pass": len(reasonmental_checks_debug("TICKER1", data["TICKER1"], config)
print(f"DEBUG RESULT: {result}")
