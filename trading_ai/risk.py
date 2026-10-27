from __future__ import annotations

import math
from decimal import Decimal, ROUND_FLOOR

from .analyzer import analyze
from .models import Blocked, KINDS, digest, number, timestamp, utcnow, validate_signal


def floor_volume(value, step):
    return float((Decimal(str(value)) / Decimal(str(step))).to_integral_value(rounding=ROUND_FLOOR) * Decimal(str(step)))


def on_grid(value, step):
    return math.isclose(value / step, round(value / step), abs_tol=1e-6)


class RiskManager:
    """Independent gate: never trusts prices, permissions or risk stated by the importer."""
    def __init__(self, config, broker, journal, activation=None, clock=utcnow, config_loader=None):
        self.c, self.b, self.j, self.activation, self.clock = config, broker, journal, activation, clock
        self.config_loader = config_loader

    def common(self, env, action):
        if self.config_loader:
            self.c = self.config_loader()
        c, now = self.c, self.clock()
        if hasattr(self.b, "time_offset") and self.b.time_offset != c.get("broker_time_offset_seconds", 0):
            raise Blocked("Broker clock configuration changed; reconnect with the new explicit offset")
        validate_signal(env["signal"])
        snap = self.b.snapshot()
        a, t = snap["account"], snap["terminal"]
        if a["login"] != c["account_login"] or a["server"] != c["account_server"] or not a["login"]:
            raise Blocked("Account login/server do not match local configuration")
        self.j.bind_account(a["login"], a["server"])
        if not t["connected"] or abs((now - timestamp(snap["as_of"])).total_seconds()) > c["risk"]["max_tick_age_seconds"]:
            raise Blocked("Disconnected or stale broker snapshot")
        for key in ("equity", "margin_free"):
            number(a[key], key, minimum=0 if action == "OPEN" else -float("inf"))
        if a["margin_mode"] not in {0, 1, 2}:
            raise Blocked("Unknown account netting/hedging mode")
        if c["mode"] != "DRY_RUN":
            if 'runtime' in c and action in {'OPEN', 'MODIFY_PENDING'}:
                from .runtime import require_authorization
                require_authorization(c, self.j, now)
            if not a["trade_allowed"] or not a["trade_expert"] or not t["trade_allowed"] or t["tradeapi_disabled"]:
                raise Blocked("Broker/terminal disables automated trading")
            if self.activation != f'{c["mode"]}:{a["login"]}':
                raise Blocked("This process has no manual trading activation")
            if c["mode"] == "DEMO" and a["trade_mode"] != 0:
                raise Blocked("DEMO requires a verified demo account")
            if c["mode"] == "LIVE" and (a["trade_mode"] != 2 or not c["live_enabled"] or a["login"] not in c["live_allowlist"]):
                raise Blocked("LIVE is locked")
            if not self.j.approved(env, a["login"], a["server"]):
                raise Blocked("Exact signal content has no local operator approval")
            policy = self.j.setting("approval_policy:"+digest(env))
            if policy and action in {"OPEN", "MODIFY_PENDING"}:
                from .strategy import policy_hash
                if now >= timestamp(policy["until"]) or policy["hash"] != policy_hash(c) or self.j.setting("strategy_policy") != policy:
                    raise Blocked("Strategy authorization expired or configuration changed")
        if self.j.uncertain():
            raise Blocked("Uncertain prior operation: reconcile before sending any operation")
        stopped = (self.j.root / "STOP").exists()
        if stopped and (action in {"OPEN", "MODIFY_PENDING"} or c["stop_policy"] == "freeze"):
            raise Blocked("Emergency STOP")
        s = env["signal"]
        if s["strategy"] not in c["strategies"]:
            raise Blocked("Strategy is not allowlisted")
        spec = c["symbols"].get(s["instrument"])
        if not spec or not spec["broker"]:
            raise Blocked("Exact broker symbol mapping is required; suffixes are never guessed")
        if action in {"OPEN", "MODIFY_PENDING"}:
            from .calendar import require_clear
            horizon = timestamp(s["valid_until"]) if KINDS[s["kind"]]>=2 else None
            require_clear(c,self.b,s["instrument"],now,horizon)
        if action in {"OPEN", "MODIFY_PENDING"} and c["mode"] != "DRY_RUN" and not spec.get("trading_enabled", True):
            raise Blocked("Instrument trading disabled until operator confirms its limits and costs")
        market = self.b.market(spec["broker"], s["structure"]["timeframe"], s["structure"]["lookback"])
        i, tick = market["info"], market["tick"]
        if market["symbol"] != spec["broker"] or i["name"] != spec["broker"]:
            raise Blocked("Broker symbol mismatch")
        for key in ("point", "trade_tick_size", "volume_min", "volume_max", "volume_step"):
            number(i[key], key)
        for key in ("bid", "ask"):
            number(tick[key], key)
        age = now.timestamp() - tick.get("time_msc", tick["time"] * 1000) / 1000
        if age < -2 or age > c["risk"]["max_tick_age_seconds"] or tick["ask"] < tick["bid"]:
            raise Blocked("Stale, future or crossed quote")
        if i["trade_mode"] == 0:
            raise Blocked("Symbol trading disabled")
        return snap, market, spec, now

    def daily_budget(self, snap, now):
        baseline = self.j.setting("day_start")
        a = snap["account"]
        if not baseline or baseline["date"] != now.date().isoformat() or baseline["account"] != a["login"] or baseline["server"] != a["server"]:
            raise Blocked("Missing verified equity at start of current UTC day")
        number(baseline["equity"], "day_start equity")
        if any(d["type"] not in {0, 1} for d in snap["deals"]):
            raise Blocked("Account cash adjustment today requires operator reconciliation of daily baseline")
        limit = baseline["equity"] * self.c["risk"]["max_daily_loss_pct"] / 100
        remaining = limit - max(0, baseline["equity"] - a["equity"])
        if remaining <= 0:
            raise Blocked("Daily equity loss limit reached (realized and unrealized)")
        return remaining

    def existing_risk(self, snap):
        total = 0
        for p in snap["positions"] + snap["orders"]:
            if p["sl"] <= 0:
                raise Blocked("Existing account exposure has no protective SL")
            side = p["type"] % 2
            price = p.get("price_current", p["price_open"])
            volume = p.get("volume", p.get("volume_current"))
            if p in snap["orders"]:
                price = p["price_open"]
            loss = self.b.profit(side, p["symbol"], volume, price, p["sl"])
            specs = [v for v in self.c["symbols"].values() if v["broker"] == p["symbol"]]
            if len(specs) != 1:
                raise Blocked("Cannot price cost buffer for existing account exposure")
            total += max(0, -loss) + specs[0]["cost_buffer_per_lot"] * volume
        return total

    @staticmethod
    def filling(info, pending=False):
        if pending:
            return 2  # RETURN, as specified for all pending orders
        if info["trade_exemode"] in {0, 1} or info["filling_mode"] & 1:
            return 0  # FOK
        if info["filling_mode"] & 2:
            return 1  # IOC; partial result freezes further operations
        if info["trade_exemode"] != 2:
            return 2
        raise Blocked("No permitted filling policy")

    def prepare_open(self, env, replacement=None):
        snap, market, spec, now = self.common(env, "MODIFY_PENDING" if replacement else "OPEN")
        s, c = env["signal"], self.c
        i, t = market["info"], market["tick"]
        target, original = None, None
        if replacement:
            old_env, ticket = replacement
            if s["id"] == old_env["signal"]["id"]:
                raise Blocked("Amendment needs a new independently approved signal ID")
            candidates = [o for o in snap["orders"] if o["ticket"] == ticket]
            if len(candidates) != 1:
                raise Blocked("Pending target no longer exists")
            target = candidates[0]
            original = self.owned(target, old_env, pending=True)
            if any(s[k] != old_env["signal"][k] for k in ("instrument", "kind", "strategy")) or KINDS[s["kind"]] < 2:
                raise Blocked("Amendment cannot change symbol, order type or strategy")
            if abs(target["price_open"]-(t["ask"] if s["kind"].startswith("BUY") else t["bid"])) <= i["trade_freeze_level"]*i["point"]:
                raise Blocked("Pending order is frozen")
            snap = {**snap, "orders": [o for o in snap["orders"] if o["ticket"] != ticket]}
        if not timestamp(s["valid_from"]) <= now < timestamp(s["valid_until"]):
            raise Blocked("Signal is expired or not yet active")
        if not 0 <= (now - timestamp(env["generated_at"])).total_seconds() <= c["risk"]["max_briefing_age_seconds"]:
            raise Blocked("Briefing expired or generated in the future")
        analysis = analyze(market, s["structure"], now)
        if analysis["trend"] != s["structure"]["trend"]:
            raise Blocked(f'Market structure disagrees: broker={analysis["trend"]}, briefing={s["structure"]["trend"]}')
        buy, kind = s["kind"].startswith("BUY"), KINDS[s["kind"]]
        if i["trade_mode"] == 3 or (i["trade_mode"] == 1 and not buy) or (i["trade_mode"] == 2 and buy):
            raise Blocked("Symbol is close-only or direction is forbidden")
        current = t["ask"] if buy else t["bid"]
        close_price = t["bid"] if buy else t["ask"]
        if (close_price <= s["structure"]["invalidation"] if buy else close_price >= s["structure"]["invalidation"]):
            raise Blocked("Setup already invalidated")
        point = i["point"]
        if (t["ask"] - t["bid"]) / point > spec["max_spread_points"] + 1e-6:
            raise Blocked("Spread exceeds limit")
        if spec.get('max_spread_atr_ratio') is not None and (t['ask']-t['bid']) > analysis['atr'] * spec['max_spread_atr_ratio']:
            raise Blocked('Spread too large relative to market ATR')
        if abs(current - s["entry"]) / point > spec["max_entry_deviation_points"]:
            raise Blocked("Broker price too far from briefing entry")
        if any(p["symbol"] == spec["broker"] for p in snap["positions"] + snap["orders"]):
            raise Blocked("Existing symbol exposure: no averaging or netting into another trade")
        if len(snap["positions"]) + len(snap["orders"]) >= c["risk"]["max_positions"]:
            raise Blocked("Position and reserved pending-order slot limit reached")
        flag = 1 if kind < 2 else 2 if kind < 4 else 4
        if i["order_mode"] & (flag | 16 | 32) != flag | 16 | 32:
            raise Blocked("Broker does not support this order with SL and TP")
        entry = current if kind < 2 else s["entry"]
        distance = max(i["trade_stops_level"], i["trade_freeze_level"]) * point
        for level in (s["sl"], s["tp"], entry):
            if not on_grid(level, i["trade_tick_size"]):
                raise Blocked("Price does not align with broker tick size")
        reference = close_price if kind < 2 else entry
        if not (s["sl"] < reference < s["tp"] if buy else s["tp"] < reference < s["sl"]):
            raise Blocked("SL/TP no longer valid at broker price")
        if min(abs(reference-s["sl"]), abs(s["tp"]-reference)) <= distance:
            raise Blocked("SL/TP violates stops/freeze distance")
        if kind >= 2:
            valid = {2: entry < t["ask"] - distance, 3: entry > t["bid"] + distance,
                     4: entry > t["ask"] + distance, 5: entry < t["bid"] - distance}[kind]
            if not valid:
                raise Blocked("Pending order is on wrong side or too near market")
            if not i["expiration_mode"] & 4:
                raise Blocked("Broker must support server-side specified expiration")
        worst = entry + (1 if buy else -1) * spec["deviation_points"] * point
        if not (s["sl"] < worst < s["tp"] if buy else s["tp"] < worst < s["sl"]):
            raise Blocked("Slippage allowance invalidates exits")
        if abs(s["tp"]-worst) / abs(worst-s["sl"]) < c["risk"]["min_rr"]:
            raise Blocked("Reward/risk below limit")
        side = 0 if buy else 1
        probe = i["volume_min"]
        per_lot = -self.b.profit(side, spec["broker"], probe, worst, s["sl"]) / probe + spec["cost_buffer_per_lot"]
        if per_lot <= 0:
            raise Blocked("Invalid calculated SL loss")
        budget = snap["account"]["equity"] * min(s["risk_pct"], c["risk"]["max_trade_pct"]) / 100
        volume = floor_volume(min(budget / per_lot, i["volume_max"], s.get("volume", i["volume_max"]), spec.get('max_volume', i['volume_max'])), i["volume_step"])
        if target:
            if target["volume_current"] > volume + 1e-9:
                raise Blocked("Amendment exceeds risk budget at immutable pending volume")
            volume = target["volume_current"]
        if volume < i["volume_min"] or not on_grid(volume, i["volume_step"]):
            raise Blocked("Risk budget cannot fund minimum lot")
        loss = per_lot * volume
        exposure = self.existing_risk(snap)
        if exposure + loss > snap["account"]["equity"] * c["risk"]["max_total_pct"] / 100:
            raise Blocked("Total account risk exceeds limit")
        if exposure + loss > self.daily_budget(snap, now):
            raise Blocked("Remaining daily loss budget cannot cover account exposure")
        margin = self.b.margin(side, spec["broker"], volume, worst)
        if margin > snap["account"]["margin_free"] * c["risk"]["margin_fraction"]:
            raise Blocked("Insufficient free margin reserve")
        tag = "TA:" + digest(env)[:24]
        request = {"action": 1 if kind < 2 else 5, "symbol": spec["broker"], "volume": volume,
                   "type": kind, "price": entry, "sl": s["sl"], "tp": s["tp"], "magic": c["magic"],
                   "comment": tag, "deviation": spec["deviation_points"], "type_filling": self.filling(i, kind >= 2)}
        if kind >= 2:
            request.update(type_time=2, expiration=int(timestamp(s["valid_until"]).timestamp()))
        elif i["trade_exemode"] == 2:
            request.pop("price")
        metadata = {"risk_cash": loss, "volume": volume, "margin": margin, "entry_reference": entry,
                    "fill_deviation_price": spec["deviation_points"] * i["point"],
                    "analysis": analysis, "broker_quote": t, "account": snap["account"], "tag": tag}
        if target:
            metadata.update(target_before=target, original_envelope=replacement[0], tag=original["payload"]["metadata"]["tag"])
            request = {k: request[k] for k in ("symbol", "price", "sl", "tp", "magic", "type_time", "expiration")}
            request.update(action=7, order=target["ticket"])
        return request, metadata

    def owned(self, target, env, pending=False):
        op = self.j.operation("open:" + self.j.root_id(env))
        if not op or op["status"] != "CONFIRMED" or target["magic"] != self.c["magic"]:
            raise Blocked("Position/order lacks confirmed local provenance")
        expected = op["payload"]["request"]["comment"]
        op = self.j.effective_operation(op)
        if digest(op["payload"]["envelope"]) != digest(env):
            raise Blocked("Use the current confirmed position plan")
        if target["symbol"] != op["payload"]["request"]["symbol"]:
            raise Blocked("Ownership symbol mismatch")
        if pending:
            if target["ticket"] != op["result"]["order"] or target["comment"] != expected:
                raise Blocked("Pending order ownership mismatch")
        else:
            deals = self.b.position_deals(target["identifier"])
            opening = [d for d in deals if d["entry"] == 0 and d["type"] in {0, 1}]
            if not opening or any(d["magic"] != self.c["magic"] or d["order"] != op["result"]["order"] for d in opening):
                raise Blocked("Mixed/foreign/netted position ownership")
            if any(d["type"] in {0, 1} and (d["magic"] != self.c["magic"] or d["entry"] not in {0, 1}) for d in deals):
                raise Blocked("Foreign modification or reversal detected")
            if target["type"] != KINDS[env["signal"]["kind"]] % 2:
                raise Blocked("Position direction no longer matches approved strategy")
        return op

    def prepare_managed(self, env, rule, ticket, close_volume=None):
        snap, market, spec, now = self.common(env, rule)
        s, i, t = env["signal"], market["info"], market["tick"]
        pending = rule in {"CANCEL_PENDING", "OPERATOR_CANCEL"}
        candidates = [p for p in snap["orders"] if p["ticket"] == ticket] if pending else [p for p in snap["positions"] if p["ticket"] == ticket]
        if len(candidates) != 1:
            raise Blocked("Target no longer exists at broker")
        p = candidates[0]
        op = self.owned(p, env, pending)
        stopped = (self.j.root / "STOP").exists()
        flatten = stopped and self.c["stop_policy"] == "flatten"
        buy = s["kind"].startswith("BUY")
        price = t["bid"] if buy else t["ask"]
        invalid = price <= s["structure"]["invalidation"] if buy else price >= s["structure"]["invalidation"]
        metadata = {"target_before": p, "tag": op["payload"]["metadata"]["tag"], "rule": rule}
        freeze = i["trade_freeze_level"] * i["point"]
        if pending:
            from .calendar import assessment
            calendar_state = assessment(self.c,self.b,s["instrument"],now)
            calendar_unsafe = calendar_state["status"] not in {"CLEAR","DISABLED"}
            try:
                daily_unsafe = self.existing_risk(snap) > self.daily_budget(snap, now)
            except Blocked:
                daily_unsafe = True
            if not (rule == "OPERATOR_CANCEL" or now >= timestamp(s["valid_until"]) or invalid or stopped or daily_unsafe or calendar_unsafe):
                raise Blocked("Pending order remains valid")
            metadata["reason"] = "Economic calendar: "+calendar_state.get("reason","") if calendar_unsafe else "expired / invalidated / STOP / insufficient daily risk budget"
            if abs(p["price_open"] - (t["ask"] if buy else t["bid"])) <= freeze:
                raise Blocked("Pending order is inside freeze distance")
            return {"action": 8, "order": ticket, "symbol": p["symbol"], "magic": self.c["magic"]}, metadata
        if (t["ask"] - t["bid"]) / i["point"] > spec["max_spread_points"] + 1e-6:
            raise Blocked("Spread exceeds limit for position operation")
        m = s["management"]
        initial_r = abs(op["payload"]["metadata"]["entry_reference"] - s["sl"])
        gained = (price - p["price_open"]) * (1 if buy else -1)
        base = {"symbol": p["symbol"], "position": ticket, "magic": self.c["magic"], "comment": metadata["tag"]}
        if rule in {"TP1", "TP2", "INVALIDATION", "STOP_CLOSE", "OPERATOR_CLOSE"}:
            crossed = lambda level: price >= level if buy else price <= level
            valid = {"TP1": m["tp1"] is not None and crossed(m["tp1"]) if m["tp1"] is not None else False,
                     "TP2": crossed(s["tp"]), "INVALIDATION": m["close_on_invalidation"] and invalid,
                     "STOP_CLOSE": flatten, "OPERATOR_CLOSE": True}[rule]
            if not valid:
                raise Blocked("Exit rule not triggered")
            volume = p["volume"]
            if rule == "OPERATOR_CLOSE" and close_volume is not None:
                number(close_volume, "close volume")
                volume = close_volume
            if rule == "TP1":
                volume = floor_volume(op["payload"]["request"]["volume"] * m["tp1_fraction"], i["volume_step"])
                if volume < i["volume_min"] or p["volume"] - volume < i["volume_min"] - 1e-9:
                    raise Blocked("TP1 leaves invalid minimum volume; retain server SL/TP")
            if (volume < i["volume_min"] or not on_grid(volume, i["volume_step"]) or volume > p["volume"]
                    or 1e-9 < p["volume"]-volume < i["volume_min"]-1e-9):
                raise Blocked("Close volume invalid")
            if p["sl"] and abs(price-p["sl"]) <= freeze or p["tp"] and abs(price-p["tp"]) <= freeze:
                raise Blocked("Position inside broker freeze level")
            base.update(action=1, type=1 if buy else 0, volume=volume, price=price,
                        deviation=spec["deviation_points"], type_filling=self.filling(i))
            # Market execution omits request.price; preserve the checked quote and
            # limit in the durable intent for post-fill and restart verification.
            metadata.update(entry_reference=price, fill_deviation_price=spec["deviation_points"] * i["point"])
            if i["trade_exemode"] == 2:
                base.pop("price")
            return base, metadata
        if rule == "BREAK_EVEN":
            if m["break_even_r"] is None or gained < m["break_even_r"] * initial_r:
                raise Blocked("Break even threshold not met")
            sl = p["price_open"]
        elif rule == "TRAILING":
            if m["trailing_distance"] is None or gained < max(initial_r, m["trailing_distance"]):
                raise Blocked("Trailing threshold not met")
            raw = price - m["trailing_distance"] * (1 if buy else -1)
            grid = raw / i["trade_tick_size"]
            sl = (math.floor(grid) if buy else math.ceil(grid)) * i["trade_tick_size"]
        else:
            raise Blocked("Unsupported management rule")
        if not on_grid(sl, i["trade_tick_size"]) or not p["sl"] or (sl <= p["sl"] if buy else sl >= p["sl"]):
            raise Blocked("SL change must strictly reduce existing risk on the tick grid")
        distance = max(i["trade_stops_level"], i["trade_freeze_level"]) * i["point"]
        if abs(price-p["sl"]) <= freeze or abs(price-p["tp"]) <= freeze:
            raise Blocked("Existing SL/TP is frozen")
        if (sl >= price if buy else sl <= price) or abs(price-sl) <= distance:
            raise Blocked("New SL violates broker stop/freeze distance")
        base.update(action=6, sl=round(sl, i["digits"]), tp=p["tp"])
        return base, metadata

    def prepare_pending_tighten(self, env, ticket, new_sl):
        """An explicit local operator request may only tighten a still-valid pending order's SL."""
        snap, market, spec, now = self.common(env, "MODIFY_PENDING")
        candidates = [o for o in snap["orders"] if o["ticket"] == ticket]
        if len(candidates) != 1:
            raise Blocked("Pending order no longer exists")
        p = candidates[0]
        self.owned(p, env, pending=True)
        s, i, t = env["signal"], market["info"], market["tick"]
        number(new_sl, "new SL")
        if now >= timestamp(s["valid_until"]):
            raise Blocked("Expired pending order must be canceled")
        if analyze(market, s["structure"], now)["trend"] != s["structure"]["trend"]:
            raise Blocked("Market structure disagrees")
        if self.existing_risk(snap) > self.daily_budget(snap, now):
            raise Blocked("Insufficient daily risk budget; cancel pending order")
        buy = s["kind"].startswith("BUY")
        if not (p["sl"] < new_sl < p["price_open"] if buy else p["price_open"] < new_sl < p["sl"]):
            raise Blocked("Pending SL amendment must strictly reduce risk")
        distance = max(i["trade_stops_level"], i["trade_freeze_level"]) * i["point"]
        if not on_grid(new_sl, i["trade_tick_size"]) or abs(new_sl-p["price_open"]) <= distance:
            raise Blocked("Pending SL violates tick grid or stop/freeze distance")
        if abs(p["price_open"]-(t["ask"] if buy else t["bid"])) <= distance:
            raise Blocked("Pending entry is inside stops/freeze distance")
        if (t["ask"]-t["bid"]) / i["point"] > spec["max_spread_points"]:
            raise Blocked("Spread exceeds limit")
        if (t["bid"] <= s["structure"]["invalidation"] if buy else t["ask"] >= s["structure"]["invalidation"]):
            raise Blocked("Setup invalidated; cancel pending order")
        request = {"action": 7, "order": ticket, "symbol": p["symbol"], "price": p["price_open"],
                   "sl": new_sl, "tp": p["tp"], "type_time": 2, "expiration": p["time_expiration"],
                   "magic": self.c["magic"]}
        return request, {"target_before": p, "rule": "TIGHTEN_PENDING", "reason": "Operator requested lower pending-order risk"}
