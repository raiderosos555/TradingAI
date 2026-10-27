from __future__ import annotations

import hashlib
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path


class Blocked(ValueError):
    """A deliberate fail-closed decision, safe to display in the journal."""


def utcnow():
    return datetime.now(timezone.utc)


def timestamp(value):
    if not isinstance(value, str):
        raise Blocked("Timestamp must be an ISO 8601 string with timezone")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise Blocked("Invalid ISO 8601 timestamp") from exc
    if result.tzinfo is None:
        raise Blocked("Timestamp without timezone")
    return result.astimezone(timezone.utc)


def number(value, name, minimum=0, maximum=float("inf"), strict=True):
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value):
        raise Blocked(f"{name}: expected a finite number")
    if (value <= minimum if strict else value < minimum) or value > maximum:
        raise Blocked(f"{name}: outside permitted range")
    return value


def fields(obj, required, optional=()):
    if not isinstance(obj, dict):
        raise Blocked("Expected JSON object")
    missing, unknown = set(required) - obj.keys(), obj.keys() - set(required) - set(optional)
    if missing or unknown:
        raise Blocked(f"Invalid fields: missing={sorted(missing)}, unknown={sorted(unknown)}")


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,80}", value):
        raise Blocked("Invalid identifier")


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise Blocked(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def read_json(path):
    path = Path(path)
    if path.stat().st_size > 2_000_000:
        raise Blocked("JSON exceeds 2 MB")
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=_unique,
                          parse_constant=lambda x: (_ for _ in ()).throw(Blocked(f"Invalid number {x}")))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise Blocked(f"Invalid JSON: {exc}") from exc


KINDS = {"BUY": 0, "SELL": 1, "BUY_LIMIT": 2, "SELL_LIMIT": 3, "BUY_STOP": 4, "SELL_STOP": 5}
TIMEFRAMES = {"M1": 60, "M5": 300, "M15": 900, "M30": 1800, "H1": 3600, "H4": 14400, "D1": 86400}


def validate_signal(s):
    fields(s, ("id", "instrument", "strategy", "kind", "entry", "sl", "tp", "risk_pct",
               "valid_from", "valid_until", "reason", "structure", "management"), ("volume",))
    for key in ("id", "instrument", "strategy"):
        identifier(s[key])
    if s["kind"] not in KINDS:
        raise Blocked("Unsupported order kind")
    for key in ("entry", "sl", "tp"):
        number(s[key], key)
    number(s["risk_pct"], "risk_pct", maximum=.25)
    if "volume" in s:
        number(s["volume"], "volume")
    buy = s["kind"].startswith("BUY")
    if not (s["sl"] < s["entry"] < s["tp"] if buy else s["tp"] < s["entry"] < s["sl"]):
        raise Blocked("SL/entry/TP ordering conflicts with direction")
    if timestamp(s["valid_until"]) <= timestamp(s["valid_from"]):
        raise Blocked("Empty validity interval")
    if not isinstance(s["reason"], str) or not 1 <= len(s["reason"]) <= 4000:
        raise Blocked("Reason is required (maximum 4000 characters)")
    st = s["structure"]
    fields(st, ("timeframe", "trend", "lookback", "invalidation"))
    if st["timeframe"] not in TIMEFRAMES or st["trend"] not in {"UP", "DOWN", "RANGE"}:
        raise Blocked("Unknown structure rule")
    if type(st["lookback"]) is not int or not 6 <= st["lookback"] <= 100:
        raise Blocked("Structure lookback must be 6..100")
    number(st["invalidation"], "invalidation")
    if not (st["invalidation"] < s["entry"] if buy else st["invalidation"] > s["entry"]):
        raise Blocked("Invalidation conflicts with direction")
    m = s["management"]
    fields(m, ("break_even_r", "trailing_distance", "tp1", "tp1_fraction", "close_on_invalidation"))
    for key in ("break_even_r", "trailing_distance", "tp1"):
        if m[key] is not None:
            number(m[key], key)
    number(m["tp1_fraction"], "tp1_fraction", maximum=.9)
    if type(m["close_on_invalidation"]) is not bool:
        raise Blocked("close_on_invalidation must be boolean")
    if m["tp1"] is not None and not (s["entry"] < m["tp1"] < s["tp"] if buy else s["tp"] < m["tp1"] < s["entry"]):
        raise Blocked("TP1 must be strictly between entry and TP2")
    return s


def validate_briefing(b):
    fields(b, ("schema_version", "briefing_id", "session", "generated_at", "signals"))
    if b["schema_version"] != "1.0" or b["session"] not in {"morning", "evening"}:
        raise Blocked("Unsupported briefing version/session")
    identifier(b["briefing_id"])
    generated = timestamp(b["generated_at"])
    if not isinstance(b["signals"], list) or len(b["signals"]) > 100:
        raise Blocked("Expected at most 100 signals")
    seen = set()
    for s in b["signals"]:
        validate_signal(s)
        if s["id"] in seen:
            raise Blocked("Duplicate signal ID")
        seen.add(s["id"])
        if timestamp(s["valid_from"]) < generated or (timestamp(s["valid_until"]) - generated).total_seconds() > 86400:
            raise Blocked("Validity must follow generation and last at most 24h")
    return b


def envelope(b, s):
    return {"briefing_id": b["briefing_id"], "session": b["session"],
            "generated_at": b["generated_at"], "signal": s}


def load_config(path):
    c = read_json(path)
    fields(c, ("mode", "terminal_path", "account_login", "account_server", "live_enabled", "live_allowlist",
               "magic", "strategies", "symbols", "risk", "stop_policy"), ("engine", "collection", "briefings", "broker_time_offset_seconds", "calendar", "runtime"))
    offset = c.get("broker_time_offset_seconds", 0)
    if type(offset) is not int or not -43200 <= offset <= 50400 or offset % 900:
        raise Blocked("Broker time offset must be an explicit quarter-hour offset within -12h..+14h")
    if c["mode"] not in {"DRY_RUN", "DEMO", "LIVE"} or c["stop_policy"] not in {"manage", "freeze", "flatten"}:
        raise Blocked("Invalid mode/STOP policy")
    if type(c["live_enabled"]) is not bool or type(c["account_login"]) is not int or c["account_login"] < 0:
        raise Blocked("Invalid account/activation configuration")
    if type(c["magic"]) is not int or not 1 <= c["magic"] <= 2**31 - 1:
        raise Blocked("Invalid magic")
    if not isinstance(c["account_server"], str) or not isinstance(c["terminal_path"], str):
        raise Blocked("Invalid terminal/server")
    if not isinstance(c["live_allowlist"], list) or any(type(x) is not int or x <= 0 for x in c["live_allowlist"]):
        raise Blocked("Invalid LIVE account allowlist")
    if not isinstance(c["strategies"], list) or not c["strategies"]:
        raise Blocked("Empty strategy allowlist")
    for x in c["strategies"]:
        identifier(x)
    if not isinstance(c["symbols"], dict):
        raise Blocked("Invalid symbol mapping")
    for alias, spec in c["symbols"].items():
        identifier(alias)
        fields(spec, ("broker", "max_spread_points", "max_entry_deviation_points", "deviation_points", "cost_buffer_per_lot"), ("trading_enabled", "max_volume", "max_spread_atr_ratio"))
        for k in ('max_volume', 'max_spread_atr_ratio'):
            if k in spec:
                number(spec[k], k)
        if type(spec.get("trading_enabled", True)) is not bool:
            raise Blocked("trading_enabled must be boolean")
        if not isinstance(spec["broker"], str):
            raise Blocked("Broker symbol must be an explicit string")
        for k in ("max_spread_points", "max_entry_deviation_points", "cost_buffer_per_lot"):
            number(spec[k], k)
        if type(spec["deviation_points"]) is not int or not 0 <= spec["deviation_points"] <= 100:
            raise Blocked("Invalid execution deviation")
    r = c["risk"]
    fields(r, ("max_trade_pct", "max_total_pct", "max_daily_loss_pct", "max_positions", "min_rr",
               "max_tick_age_seconds", "max_briefing_age_seconds", "margin_fraction"))
    for k, maximum in {"max_trade_pct": .25, "max_total_pct": .5, "max_daily_loss_pct": 1,
                       "margin_fraction": .5, "max_tick_age_seconds": 60,
                       "max_briefing_age_seconds": 86400, "min_rr": 20}.items():
        number(r[k], k, maximum=maximum)
    max_slots = 7 if c['mode'] == 'DEMO' else 2
    if type(r["max_positions"]) is not int or not 1 <= r["max_positions"] <= max_slots:
        raise Blocked(f"max_positions must be between 1 and {max_slots} in {c['mode']}")
    from .strategy import engine_config
    engine_config(c)
    collection = c.get("collection", {"enabled": False, "interval_seconds": 60})
    fields(collection, ("enabled", "interval_seconds"))
    if type(collection["enabled"]) is not bool or type(collection["interval_seconds"]) is not int or not 10 <= collection["interval_seconds"] <= 3600:
        raise Blocked("Invalid collection configuration")
    from .calendar import calendar_config
    calendar_config(c)
    if 'runtime' in c:
        fields(c['runtime'], ('authorization_id', 'starts_at', 'ends_at'))
        identifier(c['runtime']['authorization_id'])
        if timestamp(c['runtime']['starts_at']) >= timestamp(c['runtime']['ends_at']):
            raise Blocked('Runtime authorization window is empty')
        if c['mode'] != 'DEMO' or c['live_enabled'] or c['live_allowlist']:
            raise Blocked('Continuous runtime supports DEMO only')
    schedule = c.get("briefings", {"timezone": "Europe/Warsaw", "morning": "09:00", "evening": "18:00"})
    fields(schedule, ("timezone", "morning", "evening"))
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
    try:
        ZoneInfo(schedule["timezone"])
    except (ZoneInfoNotFoundError, TypeError) as exc:
        raise Blocked("Invalid briefing timezone or missing tzdata package") from exc
    for key in ("morning", "evening"):
        if not isinstance(schedule[key], str) or not re.fullmatch(r"(?:[01][0-9]|2[0-3]):[0-5][0-9]", schedule[key]):
            raise Blocked("Briefing schedule must use HH:MM")
    return c
