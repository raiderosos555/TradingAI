from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

from .analyzer import research
from .models import Blocked, TIMEFRAMES, digest, envelope, fields, number, timestamp, validate_briefing


DEFAULT_ENGINE = {"enabled": True, "timeframe": "H1", "bars": 200, "lookback": 60, "breakout_window": 20,
    "breakout_atr": .1, "consolidation_atr": 6, "stop_atr": 1.5, "reward_r": 2, "valid_bars": 2,
    "risk_pct": .25, "break_even_r": 1, "trailing_atr": 1, "tp1_r": 1, "tp1_fraction": .5,
    "enable_breakout": True, "enable_false_breakout": True}


def engine_config(config):
    e = {**DEFAULT_ENGINE, **config.get("engine", {})}
    fields(e, DEFAULT_ENGINE.keys())
    for k in ("enabled", "enable_breakout", "enable_false_breakout"):
        if type(e[k]) is not bool:
            raise Blocked(f"engine.{k} must be boolean")
    if e["timeframe"] not in TIMEFRAMES:
        raise Blocked("Invalid engine timeframe")
    for k, lo, hi in (("bars", 60, 10000), ("lookback", 6, 100), ("breakout_window", 3, 100), ("valid_bars", 1, 24)):
        if type(e[k]) is not int or not lo <= e[k] <= hi:
            raise Blocked(f"engine.{k} out of range")
    if e["bars"] < max(60, e["lookback"], e["breakout_window"]+2):
        raise Blocked("Engine history too short")
    for k in ("breakout_atr", "consolidation_atr", "stop_atr", "reward_r", "risk_pct", "break_even_r", "trailing_atr", "tp1_r", "tp1_fraction"):
        number(e[k], "engine."+k)
    if e["risk_pct"] > .25 or e["tp1_fraction"] >= 1 or e["reward_r"] <= e["tp1_r"]:
        raise Blocked("Invalid engine risk/exit parameters")
    return e


def policy_hash(c):
    return digest({"engine": engine_config(c), "symbols": c["symbols"], "risk": c["risk"],
                   "account": [c["account_login"], c["account_server"]], "magic": c["magic"], "mode": c["mode"],
                   "strategies": c["strategies"], "broker_time_offset_seconds": c.get("broker_time_offset_seconds", 0),
                   "calendar": c.get("calendar", {}), "runtime": c.get('runtime')})


class SignalEngine:
    """Local deterministic strategies; no AI calls or inherited ChatGPT authority."""
    def __init__(self, config, broker, journal=None):
        self.c, self.b, self.j = config, broker, journal
        self.e = engine_config(config)

    def evaluate(self, alias, now):
        e = self.e
        spec = self.c["symbols"].get(alias)
        if not spec or not spec["broker"]:
            raise Blocked("Configure exact broker symbol before analysis")
        market = self.b.market(spec["broker"], e["timeframe"], e["bars"])
        tick_age = now.timestamp() - market["tick"].get("time_msc", market["tick"]["time"]*1000)/1000
        if not -2 <= tick_age <= self.c["risk"]["max_tick_age_seconds"]:
            raise Blocked("Stale quote: no fresh strategy proposal")
        f = research(market, e["timeframe"], now, e["lookback"], e["breakout_window"], e["breakout_atr"], e["consolidation_atr"])
        direction, name = None, None
        if e["enable_breakout"]:
            if f["breakout"] == "UP" and f["trend"] == "UP" and f["ema20"] > f["ema50"] and f["macd_histogram"] > 0 and 50 <= f["rsi14"] <= 80:
                direction, name = "BUY", "local_breakout_v1"
            elif f["breakout"] == "DOWN" and f["trend"] == "DOWN" and f["ema20"] < f["ema50"] and f["macd_histogram"] < 0 and 20 <= f["rsi14"] <= 50:
                direction, name = "SELL", "local_breakout_v1"
        if direction is None and e["enable_false_breakout"] and f["consolidating"]:
            if f["false_breakout"] == "DOWN" and f["rsi14"] < 50:
                direction, name = "BUY", "local_false_breakout_v1"
            elif f["false_breakout"] == "UP" and f["rsi14"] > 50:
                direction, name = "SELL", "local_false_breakout_v1"
        if direction is None or name not in self.c["strategies"]:
            return {"instrument": alias, "analysis": f, "signal": None, "reason": "No complete allowlisted setup"}
        bar_end = datetime.fromtimestamp(f["signal_bar"]["time"] + TIMEFRAMES[e["timeframe"]], timezone.utc)
        expiry = bar_end + timedelta(seconds=min(86400, e["valid_bars"] * TIMEFRAMES[e["timeframe"]]))
        if now >= expiry:
            raise Blocked("Strategy setup expired")
        sid = "local-" + digest([name, alias, f["signal_bar"]["time"], policy_hash(self.c)])[:32]
        if self.j:
            row = self.j.db.execute("SELECT payload FROM signals WHERE id=?", (sid,)).fetchone()
            if row:
                import json
                return {"instrument": alias, "analysis": f, "signal": json.loads(row[0]), "reason": "Existing immutable signal for this candle"}
        buy = direction == "BUY"
        entry = market["tick"]["ask"] if buy else market["tick"]["bid"]
        step = market["info"]["trade_tick_size"]
        distance = max(e["stop_atr"]*f["atr14"],
                       (max(market["info"]["trade_stops_level"], market["info"]["trade_freeze_level"])+2)*market["info"]["point"])
        anchor = f["signal_bar"]["low"] if buy else f["signal_bar"]["high"]
        sl_raw = min(anchor-step, entry-distance) if buy else max(anchor+step, entry+distance)
        round_price = lambda x, up: round((math.ceil(x/step) if up else math.floor(x/step))*step, market["info"]["digits"])
        sl = round_price(sl_raw, not buy)
        delta = abs(entry-sl)
        tp = round_price(entry+(1 if buy else -1)*delta*e["reward_r"], buy)
        tp1 = round_price(entry+(1 if buy else -1)*delta*e["tp1_r"], buy)
        signal = {"id": sid, "instrument": alias, "strategy": name, "kind": direction, "entry": entry,
                  "sl": sl, "tp": tp, "risk_pct": e["risk_pct"], "valid_from": bar_end.isoformat(), "valid_until": expiry.isoformat(),
                  "reason": f'{name}: closed-bar {f["breakout"] or f["false_breakout"]}; EMA20/50, RSI14, MACD, ATR14; no profitability claim',
                  "structure": {"timeframe": e["timeframe"], "trend": f["trend"], "lookback": e["lookback"], "invalidation": sl},
                  "management": {"break_even_r": e["break_even_r"], "trailing_distance": round_price(f["atr14"]*e["trailing_atr"], True),
                                 "tp1": tp1, "tp1_fraction": e["tp1_fraction"], "close_on_invalidation": True}}
        briefing = {"schema_version": "1.0", "briefing_id": "engine-"+sid, "session": "morning" if bar_end.hour < 12 else "evening",
                    "generated_at": bar_end.isoformat(), "signals": [signal]}
        validate_briefing(briefing)
        env = envelope(briefing, signal)
        if self.j:
            self.j.register(env)
            self.j.set_setting("generated:"+digest(env), policy_hash(self.c))
        return {"instrument": alias, "analysis": f, "signal": env, "reason": signal["reason"]}

    def scan(self, now):
        results = []
        if not self.e["enabled"]:
            return results
        for alias in self.c["symbols"]:
            try:
                item = self.evaluate(alias, now)
                env = item["signal"]
                if env and self.j:
                    policy = self.j.setting("strategy_policy")
                    if (policy and policy["hash"] == policy_hash(self.c) and now < timestamp(policy["until"])
                            and self.j.setting("generated:"+digest(env)) == policy["hash"]):
                        if (not self.j.approved(env, self.c["account_login"], self.c["account_server"])
                                or self.j.setting('approval_policy:'+digest(env)) != policy):
                            self.j.approve(env, self.c["account_login"], self.c["account_server"], policy=policy)
                results.append(item)
            except (Blocked, KeyError) as exc:
                results.append({"instrument": alias, "signal": None, "analysis": None, "reason": str(exc)})
        return results
