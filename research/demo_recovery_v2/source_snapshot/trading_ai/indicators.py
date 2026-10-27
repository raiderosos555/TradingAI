"""Deterministic indicators; None denotes an insufficient warm-up, never a fabricated value."""
from .models import Blocked, number


def ema(values, period):
    if type(period) is not int or period < 1:
        raise Blocked("EMA period must be a positive integer")
    result = [None] * len(values)
    if len(values) < period:
        return result
    current = sum(values[:period]) / period
    result[period - 1] = current
    for k in range(period, len(values)):
        current += 2 / (period + 1) * (values[k] - current)
        result[k] = current
    return result


def wilder(values, period):
    result = [None] * len(values)
    if len(values) < period:
        return result
    current = sum(values[:period]) / period
    result[period - 1] = current
    for k in range(period, len(values)):
        current = (current * (period - 1) + values[k]) / period
        result[k] = current
    return result


def rsi(closes, period=14):
    changes = [b-a for a, b in zip(closes, closes[1:])]
    gains = wilder([max(x, 0) for x in changes], period)
    losses = wilder([max(-x, 0) for x in changes], period)
    return [None] + [None if g is None else (100 - 100/(1 + g/l) if l else (100 if g else 50)) for g, l in zip(gains, losses)]


def atr(bars, period=14):
    ranges = [max(b["high"]-b["low"], abs(b["high"]-bars[k-1]["close"]), abs(b["low"]-bars[k-1]["close"]))
              for k, b in enumerate(bars) if k]
    return [None] + wilder(ranges, period)


def macd(closes, fast=12, slow=26, signal=9):
    fasts, slows = ema(closes, fast), ema(closes, slow)
    line = [None if s is None or f is None else f-s for f, s in zip(fasts, slows)]
    start = max(fast, slow) - 1
    signal_line = [None] * min(start, len(line)) + ema(line[start:], signal)
    histogram = [None if s is None or m is None else m-s for m, s in zip(line, signal_line)]
    return {"line": line, "signal": signal_line, "histogram": histogram}


def indicators(bars):
    for b in bars:
        for k in ("open", "high", "low", "close"):
            number(b[k], k)
    closes = [b["close"] for b in bars]
    m = macd(closes)
    return {"ema20": ema(closes, 20), "ema50": ema(closes, 50), "rsi14": rsi(closes),
            "atr14": atr(bars), "macd": m["line"], "macd_signal": m["signal"], "macd_histogram": m["histogram"]}
