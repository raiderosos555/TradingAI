from __future__ import annotations

import json
import sqlite3
from collections import Counter
from datetime import timedelta
from pathlib import Path

from .models import Blocked, TIMEFRAMES, canonical, digest, timestamp, utcnow


class MarketArchive:
    """Local source data, keyed by broker/account namespace; repeat collection is idempotent."""
    def __init__(self, root, account, server, time_offset_seconds=0):
        Path(root).mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(Path(root) / "market.sqlite3")
        self.identity = [account, server]
        self.ns = digest([account, server, time_offset_seconds])
        self.db.executescript('''
          PRAGMA journal_mode=WAL;
          CREATE TABLE IF NOT EXISTS bars(ns TEXT,symbol TEXT,tf TEXT,time INTEGER,payload TEXT,PRIMARY KEY(ns,symbol,tf,time));
          CREATE TABLE IF NOT EXISTS ticks(ns TEXT,symbol TEXT,time_msc INTEGER,hash TEXT,occ INTEGER,payload TEXT,PRIMARY KEY(ns,symbol,time_msc,hash,occ));
          CREATE TABLE IF NOT EXISTS snapshots(ns TEXT,at TEXT,payload TEXT,PRIMARY KEY(ns,at));
          CREATE TABLE IF NOT EXISTS deals(ns TEXT,ticket INTEGER,payload TEXT,PRIMARY KEY(ns,ticket));
          CREATE TABLE IF NOT EXISTS orders(ns TEXT,ticket INTEGER,payload TEXT,PRIMARY KEY(ns,ticket));
        ''')

    def close(self):
        self.db.close()

    def save_bars(self, symbol, tf, bars):
        with self.db:
            self.db.executemany("INSERT OR REPLACE INTO bars VALUES(?,?,?,?,?)", [(self.ns, symbol, tf, int(b["time"]), canonical(b)) for b in bars])

    def save_ticks(self, symbol, ticks):
        occurrences, rows = Counter(), []
        for t in ticks:
            key = (t["time_msc"], digest(t))
            rows.append((self.ns, symbol, *key, occurrences[key], canonical(t)))
            occurrences[key] += 1
        with self.db:
            self.db.executemany("INSERT OR REPLACE INTO ticks VALUES(?,?,?,?,?,?)", rows)

    def save_snapshot(self, snap):
        a = snap["account"]
        if [a["login"], a["server"]] != self.identity:
            raise Blocked("Archive account mismatch")
        with self.db:
            self.db.execute("INSERT OR REPLACE INTO snapshots VALUES(?,?,?)", (self.ns, snap["as_of"], canonical(snap)))
        self.save_history({"deals": snap["deals"], "orders": snap["orders"]})

    def save_history(self, history):
        with self.db:
            for table in ("deals", "orders"):
                self.db.executemany(f"INSERT OR REPLACE INTO {table} VALUES(?,?,?)", [(self.ns, d["ticket"], canonical(d)) for d in history[table]])

    def bars(self, symbol, tf):
        return [json.loads(r[0]) for r in self.db.execute("SELECT payload FROM bars WHERE ns=? AND symbol=? AND tf=? ORDER BY time", (self.ns, symbol, tf))]

    def equity_at_start(self, now):
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        rows = self.db.execute("SELECT payload FROM snapshots WHERE ns=? AND at>=? AND at<=? ORDER BY at LIMIT 1",
                              (self.ns, start.isoformat(), (start+timedelta(seconds=5)).isoformat())).fetchall()
        return json.loads(rows[0][0]) if rows else None


class Collector:
    def __init__(self, config, broker, archive):
        self.c, self.b, self.a = config, broker, archive

    def collect(self, now=None, bars=200, tick_seconds=60):
        now = now or utcnow()
        snapshot = self.b.snapshot()
        self.a.save_snapshot(snapshot)
        status = []
        for alias, spec in self.c["symbols"].items():
            symbol = spec["broker"]
            for tf in TIMEFRAMES:
                try:
                    m = self.b.market(symbol, tf, bars)
                    self.a.save_bars(symbol, tf, m["bars"])
                    status.append({"instrument": alias, "timeframe": tf, "bars": len(m["bars"]), "status": "COLLECTED"})
                except Exception as exc:
                    status.append({"instrument": alias, "timeframe": tf, "status": "UNAVAILABLE", "reason": str(exc)})
            try:
                ticks = self.b.ticks(symbol, now-timedelta(seconds=tick_seconds), now)
                self.a.save_ticks(symbol, ticks)
                status.append({"instrument": alias, "ticks": len(ticks), "status": "COLLECTED"})
            except Exception as exc:
                status.append({"instrument": alias, "status": "UNAVAILABLE", "reason": str(exc)})
        return status

    def backfill(self, start, end):
        if start >= end or end-start > timedelta(days=366):
            raise Blocked("Backfill interval must be 0..366 days")
        stats = []
        for alias, spec in self.c["symbols"].items():
            symbol = spec["broker"]
            for tf in TIMEFRAMES:
                bars = self.b.rates(symbol, tf, start, end)
                self.a.save_bars(symbol, tf, bars)
                stats.append({"instrument": alias, "timeframe": tf, "bars": len(bars)})
            current, count = start, 0
            while current < end:
                until = min(current+timedelta(hours=1), end)
                ticks = self.b.ticks(symbol, current, until)
                self.a.save_ticks(symbol, ticks)
                count += len(ticks)
                current = until
            stats.append({"instrument": alias, "ticks": count})
        self.a.save_history(self.b.history(start, end))
        return stats


ALIASES = {"GOLD": ("GOLD", "XAUUSD"), "US500": ("US500", "SP500", "SPX500"),
           "OIL": ("OIL", "WTI", "USOIL"), "EURPLN": ("EURPLN",), "EURUSD": ("EURUSD",),
           "GBPUSD": ("GBPUSD",), "US100": ("US100", "NAS100", "USTEC")}


def discover_symbols(inventory):
    """Return candidates from actual broker inventory. Never auto-select a suffix or ambiguous contract."""
    import re
    result = {}
    for alias, tokens in ALIASES.items():
        candidates = []
        for s in inventory:
            name = s["name"].upper()
            exact = name in tokens
            descriptive = " ".join(str(s.get(k, "")) for k in ("name", "description", "path")).upper()
            if exact or any(re.search(r"(?<![A-Z0-9])"+re.escape(t)+r"(?![A-Z0-9])", descriptive) for t in tokens):
                candidates.append({**s, "exact_alias": exact})
        result[alias] = {"status": "REQUIRES_OPERATOR_MAPPING", "candidates": candidates}
    return result
