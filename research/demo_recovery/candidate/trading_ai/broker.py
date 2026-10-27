from __future__ import annotations

import math
from datetime import datetime, timezone, timedelta

from .models import Blocked, utcnow


def plain(value):
    if hasattr(value, "_asdict"):
        return {k: plain(v) for k, v in value._asdict().items()}
    if isinstance(value, (list, tuple)):
        return [plain(v) for v in value]
    if isinstance(value, dict):
        return {k: plain(v) for k, v in value.items()}
    if hasattr(value, "item"):
        return value.item()
    return value


class MT5Broker:
    """The sole adapter to the official package. Construction does not send trades."""
    def __init__(self, terminal_path, time_offset_seconds=0):
        try:
            import MetaTrader5 as mt5
        except ImportError as exc:
            raise Blocked("Install the optional MetaTrader5 package in a dedicated Python environment") from exc
        self.mt5 = mt5
        self.time_offset = time_offset_seconds
        self.terminal_path = terminal_path
        if not terminal_path or not mt5.initialize(path=terminal_path, timeout=10000):
            raise Blocked(f"MT5 initialization failed: {mt5.last_error()}")

    def reconnect(self):
        self.mt5.shutdown()
        if not self.mt5.initialize(path=self.terminal_path, timeout=10000):
            raise Blocked(f"MT5 reconnect failed: {self.mt5.last_error()}")

    def paths(self):
        info = self.required(self.mt5.terminal_info(), "terminal_info")
        return {k: info[k] for k in ("path", "data_path", "commondata_path")}

    def close(self):
        self.mt5.shutdown()

    def required(self, value, operation):
        if value is None:
            raise Blocked(f"MT5 {operation} failed: {self.mt5.last_error()}")
        return self.normalize(plain(value))

    def normalize(self, value):
        if isinstance(value, list):
            return [self.normalize(x) for x in value]
        if not isinstance(value, dict):
            return value
        result = {k: self.normalize(v) for k,v in value.items()}
        for k in ("time", "time_msc", "time_setup", "time_setup_msc", "time_done", "time_done_msc", "time_expiration", "time_update", "time_update_msc", "expiration"):
            if k in result and isinstance(result[k], (int,float)) and result[k] and self.time_offset:
                result["broker_raw_"+k] = result[k]
                result[k] -= self.time_offset * (1000 if k.endswith("msc") else 1)
        return result

    def broker_time(self, dt):
        return dt + timedelta(seconds=self.time_offset)

    def broker_request(self, request):
        request = dict(request)
        if request.get("expiration"):
            request["expiration"] += self.time_offset
        return request

    def snapshot(self):
        m = self.mt5
        now = utcnow()
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        terminal = self.required(m.terminal_info(), "terminal_info")
        if not terminal["connected"]:
            raise Blocked("MT5 disconnected")
        account = self.required(m.account_info(), "account_info")
        # Export only operational account fields, never name/password or personal details.
        keys = ("login", "server", "trade_mode", "margin_mode", "currency", "balance", "equity",
                "margin_free", "profit", "trade_allowed", "trade_expert")
        return {"as_of": now.isoformat(), "account": {k: account[k] for k in keys},
                "terminal": {k: terminal[k] for k in ("connected", "trade_allowed", "tradeapi_disabled")},
                "positions": self.required(m.positions_get(), "positions_get"),
                "orders": self.required(m.orders_get(), "orders_get"),
                "deals": self.required(m.history_deals_get(self.broker_time(start), self.broker_time(now)), "history_deals_get")}

    def inventory(self):
        return [{k: x[k] for k in ("name", "description", "path", "visible", "trade_mode")}
                for x in self.required(self.mt5.symbols_get(), "symbols_get")]

    def market(self, symbol, timeframe="H1", count=20):
        m = self.mt5
        info = self.required(m.symbol_info(symbol), "symbol_info")
        if not info["visible"] and not m.symbol_select(symbol, True):
            raise Blocked("Cannot select configured broker symbol")
        tick = self.required(m.symbol_info_tick(symbol), "symbol_info_tick")
        rates = m.copy_rates_from_pos(symbol, getattr(m, "TIMEFRAME_" + timeframe), 1, count)
        if rates is None or len(rates) != count:
            raise Blocked("Incomplete closed-bar history")
        bars = [self.normalize({k: plain(row[k]) for k in rates.dtype.names}) for row in rates]
        return {"symbol": symbol, "info": info, "tick": tick, "bars": bars}

    def rates(self, symbol, timeframe, start, end):
        from .models import TIMEFRAMES
        if timeframe not in TIMEFRAMES or start.tzinfo is None or end.tzinfo is None or start >= end:
            raise Blocked("Invalid history interval/timeframe")
        rates = self.mt5.copy_rates_range(symbol, getattr(self.mt5, "TIMEFRAME_"+timeframe), self.broker_time(start), self.broker_time(end))
        if rates is None:
            raise Blocked(f"MT5 history unavailable: {self.mt5.last_error()}")
        rows = [self.normalize({k: plain(row[k]) for k in rates.dtype.names}) for row in rates]
        return [row for row in rows if row["time"] + TIMEFRAMES[timeframe] <= min(end.timestamp(), utcnow().timestamp())]

    def ticks(self, symbol, start, end):
        if start.tzinfo is None or end.tzinfo is None or start >= end or end-start > timedelta(hours=1):
            raise Blocked("Tick requests must use UTC-aware intervals of at most one hour")
        ticks = self.mt5.copy_ticks_range(symbol, self.broker_time(start), self.broker_time(end), self.mt5.COPY_TICKS_ALL)
        if ticks is None:
            raise Blocked(f"MT5 tick history unavailable: {self.mt5.last_error()}")
        rows = [self.normalize({k: plain(row[k]) for k in ticks.dtype.names}) for row in ticks]
        return [row for row in rows if start.timestamp()*1000 <= row["time_msc"] < end.timestamp()*1000]

    def history(self, start, end):
        return {"deals": self.required(self.mt5.history_deals_get(self.broker_time(start), self.broker_time(end)), "history deals"),
                "orders": self.required(self.mt5.history_orders_get(self.broker_time(start), self.broker_time(end)), "history orders")}

    def position_deals(self, identifier):
        return self.required(self.mt5.history_deals_get(position=identifier), "position history")

    def order_history(self, ticket):
        return self.required(self.mt5.history_orders_get(ticket=ticket), "order history")

    def profit(self, side, symbol, volume, start, end):
        value = self.mt5.order_calc_profit(side, symbol, volume, start, end)
        if value is None or not math.isfinite(value):
            raise Blocked("order_calc_profit unavailable")
        return value

    def margin(self, side, symbol, volume, price):
        value = self.mt5.order_calc_margin(side, symbol, volume, price)
        if value is None or not math.isfinite(value) or value < 0:
            raise Blocked("order_calc_margin unavailable")
        return value

    def check(self, request):
        return self.required(self.mt5.order_check(self.broker_request(request)), "order_check")

    def send(self, request):
        # Only ExecutionEngine calls this, after independent risk validation and durable intent.
        return self.required(self.mt5.order_send(self.broker_request(request)), "order_send")
