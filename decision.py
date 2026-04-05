import re
import math
def parse_market_range(title: str):
    title = title.strip().lower()
    match = re.match(r"(\d+\.?\d*)-(\d+\.?\d*)", title)
    if match:
        return float(match.group(1)), float(match.group(2))
    match = re.match(r"(\d+\.?\d*)\s*f\s*or below", title)
    if match:
        return -math.inf, float(match.group(1))
    match = re.match(r"(\d+\.?\d*)\s*f\s*or higher", title)
    if match:
        return float(match.group(1)), math.inf
    return None, None
def market_edge(market, predicted_value):
    lower, upper = parse_market_range(market["groupItemTitle"])
    if lower is None and upper is None:
        return None
    if predicted_value < lower:
        return lower - predicted_value
    elif predicted_value > upper:
        return predicted_value - upper
    else:
        return 0.0
def best_market(markets, predicted_value):
    scored = []
    for m in markets:
        edge = market_edge(m, predicted_value)
        if edge is None:
            continue
        scored.append((edge, m))
    scored.sort(key=lambda x: x[0])
    best = scored[0]
    second_best = scored[1] if len(scored) > 1 else None
    return best, second_best
