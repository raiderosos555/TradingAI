from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from .models import Blocked, canonical, digest, utcnow


def atomic_write(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".{os.getpid()}.tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as f:
        f.write(content)
        f.flush()
        os.fsync(f.fileno())
    os.replace(temporary, path)


@contextmanager
def process_lock(root):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    with (root / "engine.lock").open("a+b") as f:
        if f.seek(0, os.SEEK_END) == 0:
            f.write(b"0")
            f.flush()
        f.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise Blocked("Another engine owns this state directory") from exc
        try:
            yield
        finally:
            f.seek(0)
            if os.name == "nt":
                msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(f, fcntl.LOCK_UN)


class Journal:
    def __init__(self, root):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.root / "journal.sqlite3")
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
            PRAGMA journal_mode=WAL; PRAGMA synchronous=FULL;
            CREATE TABLE IF NOT EXISTS signals(id TEXT PRIMARY KEY, hash TEXT, payload TEXT);
            CREATE TABLE IF NOT EXISTS approvals(hash TEXT PRIMARY KEY, account INTEGER, server TEXT, at TEXT);
            CREATE TABLE IF NOT EXISTS operations(id TEXT PRIMARY KEY, status TEXT, payload TEXT, result TEXT, at TEXT);
            CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY AUTOINCREMENT, at TEXT, kind TEXT, payload TEXT);
            CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT);
        """)

    def close(self):
        self.db.close()

    def event(self, kind, payload):
        with self.db:
            self.db.execute("INSERT INTO events(at,kind,payload) VALUES(?,?,?)", (utcnow().isoformat(), kind, canonical(payload)))

    def bind_account(self, login, server):
        value = [login, server]
        old = self.setting("account")
        if old is not None and old != value:
            raise Blocked("Journal belongs to a different account/server")
        self.set_setting("account", value)

    def register(self, env):
        key, sha = env["signal"]["id"], digest(env)
        old = self.db.execute("SELECT hash FROM signals WHERE id=?", (key,)).fetchone()
        if old and old[0] != sha:
            raise Blocked("Signal ID reused with different content/session; use a new ID")
        with self.db:
            self.db.execute("INSERT OR IGNORE INTO signals VALUES(?,?,?)", (key, sha, canonical(env)))
        return sha

    def approve(self, env, login, server, policy=None):
        if not login or not server:
            raise Blocked("Configure exact account and server before approval")
        sha = self.register(env)
        with self.db:
            self.db.execute("INSERT OR REPLACE INTO approvals VALUES(?,?,?,?)", (sha, login, server, utcnow().isoformat()))
        self.event("operator_approval", {"signal_id": env["signal"]["id"], "sha256": sha, "account": login})
        self.set_setting("approval_policy:"+sha, policy)

    def approved(self, env, login, server):
        return self.db.execute("SELECT 1 FROM approvals WHERE hash=? AND account=? AND server=?",
                               (digest(env), login, server)).fetchone() is not None

    def operation(self, key):
        row = self.db.execute("SELECT * FROM operations WHERE id=?", (key,)).fetchone()
        return self.decode(row) if row else None

    @staticmethod
    def decode(row):
        row = dict(row)
        for k in ("payload", "result"):
            if row.get(k):
                row[k] = json.loads(row[k])
        return row

    def operations(self):
        return [self.decode(x) for x in self.db.execute("SELECT * FROM operations ORDER BY at")]

    def intent(self, key, payload):
        with self.db:
            self.db.execute("INSERT INTO operations VALUES(?,?,?,?,?)", (key, "INTENT", canonical(payload), None, utcnow().isoformat()))

    def finish(self, key, status, result):
        with self.db:
            self.db.execute("UPDATE operations SET status=?, result=? WHERE id=?", (status, canonical(result), key))

    def uncertain(self):
        return any(x["status"] in {"INTENT", "UNCERTAIN"} for x in self.operations())

    def set_setting(self, key, value):
        with self.db:
            self.db.execute("INSERT OR REPLACE INTO settings VALUES(?,?)", (key, canonical(value)))

    def setting(self, key):
        row = self.db.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return json.loads(row[0]) if row else None

    def record_day_start(self, baseline):
        """Atomic first-writer wins: the independent UTC recorder never resets a day."""
        try:
            self.db.execute('BEGIN IMMEDIATE')
            old = self.setting('day_start')
            if old and old['date'] >= baseline['date']:
                self.db.rollback()
                return False
            self.db.execute('INSERT OR REPLACE INTO settings VALUES(?,?)', ('day_start', canonical(baseline)))
            self.db.commit()
            self.event('automatic_day_start', baseline)
            return True
        except Exception:
            self.db.rollback()
            raise

    def events(self, limit=None):
        if limit is None:
            return [self.decode(x) for x in self.db.execute("SELECT * FROM events ORDER BY seq")]
        if type(limit) is not int or limit <= 0:
            raise ValueError('Positive event limit required')
        rows = self.db.execute('SELECT * FROM events ORDER BY seq DESC LIMIT ?', (limit,)).fetchall()
        return [self.decode(x) for x in reversed(rows)]

    def root_id(self, env):
        return self.setting("root_signal:"+env["signal"]["id"]) or env["signal"]["id"]

    def effective_operation(self, op):
        """Keep immutable original audit data; overlay only a confirmed approved amendment."""
        import copy
        accepted = (op.get("result") or {}).get("accepted_volume")
        if accepted is not None:
            op = copy.deepcopy(op)
            requested = op["payload"]["request"]["volume"]
            op["payload"]["request"]["volume"] = accepted
            op["payload"]["metadata"]["volume"] = accepted
            op["payload"]["metadata"]["risk_cash"] *= accepted/requested
        amendment = self.setting("effective:"+op["payload"]["envelope"]["signal"]["id"])
        if not amendment:
            return op
        updated = self.operation(amendment)
        if not updated or updated["status"] != "CONFIRMED":
            raise Blocked("Amendment state is not confirmed")
        result = copy.deepcopy(op)
        result["payload"]["envelope"] = updated["payload"]["envelope"]
        result["payload"]["request"].update({k: v for k, v in updated["payload"]["request"].items() if k in {"sl", "tp", "price", "expiration"}})
        result["payload"]["metadata"].update({k: v for k, v in updated["payload"]["metadata"].items() if k in {"risk_cash", "entry_reference", "volume", "margin", "fill_deviation_price"}})
        return result
