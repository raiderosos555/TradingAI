from .models import Blocked, TIMEFRAMES, number
from .indicators import indicators


def analyze(market, rule, now):
    bars = market["bars"]
    if len(bars) != rule["lookback"]:
        raise Blocked("Insufficient structure history")
    seconds = TIMEFRAMES[rule["timeframe"]]
    previous = 0
    for b in bars:
        for k in ("open", "high", "low", "close"):
            number(b[k], f"bar.{k}")
        if not b["low"] <= min(b["open"], b["close"]) <= max(b["open"], b["close"]) <= b["high"]:
            raise Blocked("Invalid OHLC bar")
        if b["time"] <= previous or b["time"] + seconds > now.timestamp():
            raise Blocked("Bars must be ordered and closed")
        previous = b["time"]
    if now.timestamp() - bars[-1]["time"] > seconds * 2.5:
        raise Blocked("Stale market structure")
    width = len(bars) // 3
    first, last = bars[:width], bars[-width:]
    h0, h1 = max(b["high"] for b in first), max(b["high"] for b in last)
    l0, l1 = min(b["low"] for b in first), min(b["low"] for b in last)
    trend = "UP" if h1 > h0 and l1 > l0 else "DOWN" if h1 < h0 and l1 < l0 else "RANGE"
    closes = [b["close"] for b in bars]
    def ema(period):
        result = closes[0]
        for price in closes[1:]:
            result += 2 / (period + 1) * (price - result)
        return result
    tr = [max(b["high"] - b["low"], abs(b["high"] - bars[i-1]["close"]),
              abs(b["low"] - bars[i-1]["close"])) for i, b in enumerate(bars) if i]
    changes = [b-a for a, b in zip(closes, closes[1:])][-14:]
    gain, loss = sum(max(x, 0) for x in changes), sum(max(-x, 0) for x in changes)
    return {"trend": trend, "support": min(b["low"] for b in bars),
            "resistance": max(b["high"] for b in bars), "ema_fast": ema(5), "ema_slow": ema(20),
            "momentum": closes[-1] - closes[0], "atr": sum(tr[-14:]) / len(tr[-14:]),
            "rsi_simple": 100 - 100 / (1 + gain / loss) if loss else (100 if gain else 50),
            "last_closed_at": bars[-1]["time"]}


def research(market, timeframe, now, lookback=60, breakout_window=20, breakout_atr=.1, consolidation_atr=6):
    """Closed-bar strategy features. Prior levels exclude the signal candle (no look-ahead)."""
    bars = market["bars"]
    if len(bars) < max(60, lookback, breakout_window+2):
        raise Blocked("At least 60 closed bars required for strategy research")
    # Validate all historical bars as well as the shorter structural window.
    analyze(market, {"lookback": len(bars), "timeframe": timeframe}, now)
    features = analyze({**market, "bars": bars[-lookback:]}, {"lookback": lookback, "timeframe": timeframe}, now)
    series = indicators(bars)
    latest = {k: v[-1] for k, v in series.items()}
    if any(v is None for v in latest.values()):
        raise Blocked("Indicator warm-up incomplete")
    prior, candle = bars[-breakout_window-1:-1], bars[-1]
    resistance, support = max(b["high"] for b in prior), min(b["low"] for b in prior)
    buffer = latest["atr14"] * breakout_atr
    breakout = "UP" if candle["close"] > resistance + buffer else "DOWN" if candle["close"] < support-buffer else None
    false_breakout = "UP" if candle["high"] > resistance+buffer and candle["close"] <= resistance else "DOWN" if candle["low"] < support-buffer and candle["close"] >= support else None
    return {**features, **latest, "timeframe": timeframe, "prior_support": support, "prior_resistance": resistance,
            "breakout": breakout, "false_breakout": false_breakout,
            "consolidating": resistance-support <= consolidation_atr * latest["atr14"],
            "volatility_pct": 100 * latest["atr14"] / candle["close"], "signal_bar": candle,
            "rules": {"lookback": lookback, "breakout_window": breakout_window, "breakout_atr": breakout_atr,
                      "consolidation_atr": consolidation_atr}}
