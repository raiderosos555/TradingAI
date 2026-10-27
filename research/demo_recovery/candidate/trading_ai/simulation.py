"""Deterministic in-memory broker. Never imports or connects to MetaTrader5."""
from __future__ import annotations

import copy
import json
from datetime import timedelta
from pathlib import Path

from .journal import Journal, atomic_write, process_lock
from .models import Blocked, envelope, utcnow
from .sync import FileTransport


def fixture(now=None):
    now = now or utcnow()
    c = json.loads((Path(__file__).parents[1] / "config.json").read_text())
    c.update(account_login=123456, account_server="SIMULATOR", mode="DRY_RUN")
    c["symbols"] = {"GOLD": {"broker": "TEST_GOLD", "max_spread_points": 5,
        "max_entry_deviation_points": 300, "deviation_points": 2, "cost_buffer_per_lot": 2}}
    signal = {"id": "example-gold-001", "instrument": "GOLD", "strategy": "chatgpt_briefing_v1", "kind": "BUY",
              "entry": 100.02, "sl": 99.0, "tp": 102.0, "risk_pct": .25,
              "valid_from": now.isoformat(), "valid_until": (now + timedelta(hours=8)).isoformat(),
              "reason": "Synthetic test only: higher highs and higher lows",
              "structure": {"timeframe": "H1", "trend": "UP", "lookback": 18, "invalidation": 99.1},
              "management": {"break_even_r": 1.0, "trailing_distance": .5, "tp1": 101.5,
                             "tp1_fraction": .5, "close_on_invalidation": True}}
    b = {"schema_version": "1.0", "briefing_id": "simulation-morning", "session": "morning",
         "generated_at": now.isoformat(), "signals": [signal]}
    return c, b


class SimBroker:
    source = "SIMULATOR — synthetic data, no MT5 connection"

    def __init__(self, now=None):
        self.now = now or utcnow()
        self.account = {"login": 123456, "server": "SIMULATOR", "trade_mode": 0, "margin_mode": 2,
                        "currency": "USD", "balance": 10000., "equity": 10000., "margin_free": 9000.,
                        "profit": 0., "trade_allowed": True, "trade_expert": True}
        self.terminal = {"connected": True, "trade_allowed": True, "tradeapi_disabled": False}
        self.positions, self.orders, self.deals, self.history, self.sent = [], [], [], [], []
        self.next_ticket = 1000
        self.info = {"name": "TEST_GOLD", "point": .01, "trade_tick_size": .01, "digits": 2,
                     "volume_min": .01, "volume_max": 100., "volume_step": .01, "trade_stops_level": 5,
                     "trade_freeze_level": 2, "trade_mode": 4, "trade_exemode": 2, "order_mode": 63,
                     "filling_mode": 3, "expiration_mode": 7}
        self.tick = {"bid": 100., "ask": 100.02, "time": int(self.now.timestamp()), "time_msc": int(self.now.timestamp()*1000)}
        self.check_code, self.send_code = 0, 10009
        self.send_error, self.snapshot_error = None, False

    def snapshot(self):
        if self.snapshot_error or not self.terminal["connected"]:
            raise Blocked("Simulator disconnected")
        return copy.deepcopy({"as_of": self.now.isoformat(), "account": self.account, "terminal": self.terminal,
                              "positions": self.positions, "orders": self.orders, "deals": self.deals})

    def market(self, symbol, timeframe="H1", count=20):
        from .models import TIMEFRAMES
        if symbol != self.info["name"]:
            raise Blocked("Unknown simulator symbol")
        bars = []
        for index in range(count):
            price = 97 + index * .1
            bars.append({"time": int(self.now.timestamp()) - TIMEFRAMES[timeframe] * (count-index),
                         "open": price, "high": price+.15, "low": price-.05, "close": price+.1, "tick_volume": 100})
        return copy.deepcopy({"symbol": symbol, "info": self.info, "tick": self.tick, "bars": bars})

    def profit(self, side, symbol, volume, start, end):
        return (end-start) * (1 if side == 0 else -1) * 100 * volume

    def margin(self, side, symbol, volume, price):
        return volume * 100

    def check(self, request):
        return {"retcode": self.check_code, "comment": "simulated"}

    def position_deals(self, identifier):
        return copy.deepcopy([d for d in self.deals if d["position_id"] == identifier])

    def order_history(self, ticket):
        return copy.deepcopy([o for o in self.history if o["ticket"] == ticket])

    def quote(self, bid, ask=None):
        self.tick.update(bid=bid, ask=round(bid+.02, 2) if ask is None else ask)
        for p in self.positions:
            p["price_current"] = bid if p["type"] == 0 else self.tick["ask"]
            p["profit"] = self.profit(p["type"], p["symbol"], p["volume"], p["price_open"], p["price_current"])

    def send(self, r):
        self.sent.append(copy.deepcopy(r))
        if self.send_error:
            raise self.send_error
        self.next_ticket += 1
        ticket = self.next_ticket
        result = {"retcode": self.send_code, "order": ticket, "deal": ticket+10000, "comment": "SIMULATED"}
        if self.send_code not in {10008, 10009, 10010}:
            return result
        if r["action"] == 5:
            self.orders.append({"ticket": ticket, "symbol": r["symbol"], "type": r["type"], "magic": r["magic"],
                                "comment": r["comment"], "price_open": r["price"], "price_current": self.tick["ask"],
                                "sl": r["sl"], "tp": r["tp"], "volume_current": r["volume"], "volume_initial": r["volume"],
                                "time_expiration": r["expiration"]})
        elif r["action"] == 8:
            old = next(o for o in self.orders if o["ticket"] == r["order"])
            self.orders.remove(old)
            self.history.append({**old, "state": 2, "position_id": 0})
        elif r["action"] == 7:
            p = next(p for p in self.orders if p["ticket"] == r["order"])
            p.update(sl=r["sl"], tp=r["tp"], price_open=r["price"], time_expiration=r["expiration"])
        elif r["action"] == 6:
            p = next(p for p in self.positions if p["ticket"] == r["position"])
            p.update(sl=r["sl"], tp=r["tp"])
        elif r["action"] == 1:
            if "position" in r:
                p = next(p for p in self.positions if p["ticket"] == r["position"])
                pid, entry = p["identifier"], 1
                price = self.tick["ask"] if r["type"] == 0 else self.tick["bid"]
                profit = self.profit(p["type"], p["symbol"], r["volume"], p["price_open"], price)
                p["volume"] = round(p["volume"]-r["volume"], 8)
                if not p["volume"]:
                    self.positions.remove(p)
            else:
                pid, entry, profit = ticket, 0, 0
                price = self.tick["ask"] if r["type"] == 0 else self.tick["bid"]
                self.positions.append({"ticket": ticket, "identifier": pid, "symbol": r["symbol"], "type": r["type"],
                                       "magic": r["magic"], "comment": r["comment"], "volume": r["volume"], "price_open": price,
                                       "price_current": price, "sl": r["sl"], "tp": r["tp"], "profit": 0., "swap": 0.})
            self.history.append({"ticket": ticket, "position_id": pid, "state": 4})
            self.deals.append({"ticket": ticket+10000, "order": ticket, "position_id": pid, "entry": entry,
                               "type": r["type"], "magic": r["magic"], "symbol": r["symbol"], "comment": r["comment"],
                               "volume": r["volume"], "price": price, "profit": profit, "commission": 0., "swap": 0., "fee": 0.,
                               "time": int(self.now.timestamp())})
        return result


def simulate(state, exchange):
    from .cli import cycle
    # Isolate fake account data from the real journal and inbox, even if defaults are used.
    state, exchange = Path(state) / "simulation", Path(exchange) / "simulation"
    c, b = fixture()
    transport = FileTransport(exchange)
    broker = SimBroker()
    with process_lock(state):
        j = Journal(state)
        try:
            j.set_setting("day_start", {"date": broker.now.date().isoformat(), "equity": 10000,
                                       "account": 123456, "server": "SIMULATOR", "source": "synthetic fixture"})
            # IDs change per offline run; each immutable run has its own inbox.
            run_id = str(int(broker.now.timestamp()*1000000))
            b["briefing_id"] += "-" + run_id
            b["signals"][0]["id"] += "-" + run_id
            atomic_write(transport.root / "inbox" / "morning.json", json.dumps(b, indent=2))
            r = cycle(c, broker, j, transport)
            return {"simulation": True, "orders_sent": len(broker.sent), "report": str((transport.root / "outbox" / (r["report_id"] + ".md")).resolve()),
                    "decisions": [{"signal_id": x.get("signal_id"), "status": x.get("status"), "reason": x.get("reason")} for x in r["decisions"]]}
        finally:
            j.close()
