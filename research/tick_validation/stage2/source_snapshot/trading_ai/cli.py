from __future__ import annotations

import argparse
import json
import os
import sys
import time
from contextlib import ExitStack
from pathlib import Path

from .broker import MT5Broker
from .execution import ExecutionEngine
from .journal import Journal, atomic_write, process_lock
from .manager import PositionManager
from .models import Blocked, canonical, digest, envelope, load_config, number, read_json, timestamp, utcnow, validate_briefing
from .reporter import report
from .risk import RiskManager
from .sync import FileTransport
from .collector import Collector, MarketArchive, discover_symbols
from .strategy import SignalEngine, policy_hash
from .briefings import build_briefing, scheduled_briefing


def cycle(config, broker, journal, transport, activation=None, config_loader=None, publish=True):
    engine = ExecutionEngine(RiskManager(config, broker, journal, activation, config_loader=config_loader))
    decisions, scan, collection = [], [], []
    try:
        snap = broker.snapshot()
        if snap["account"]["login"] != config["account_login"] or snap["account"]["server"] != config["account_server"]:
            raise Blocked("Account/server mismatch")
        journal.bind_account(snap["account"]["login"], snap["account"]["server"])
        decisions.extend(engine.reconcile())
        decisions.extend(PositionManager(engine).run())
        now = utcnow()
        settings = config.get("collection", {"enabled": False, "interval_seconds": 60})
        last = journal.setting("last_collection")
        if settings["enabled"] and (not last or (now-timestamp(last)).total_seconds() >= settings["interval_seconds"]):
            archive = MarketArchive(journal.root, config["account_login"], config["account_server"], config.get("broker_time_offset_seconds", 0))
            try:
                collection = Collector(config, broker, archive).collect(now)
                baseline = journal.setting("day_start")
                boundary = archive.equity_at_start(now)
                if boundary and (not baseline or baseline["date"] != now.date().isoformat()):
                    journal.record_day_start({"date": now.date().isoformat(), "equity": boundary["account"]["equity"],
                        "account": config["account_login"], "server": config["account_server"], "source": "Broker snapshot within first 5 seconds of UTC day", "as_of": boundary["as_of"]})
                journal.set_setting("last_collection", now.isoformat())
            finally:
                archive.close()
        scan = SignalEngine(config, broker, journal).scan(now)
        from .news import record_signal_context
        record_signal_context(journal,scan,utcnow())
        # Validate the complete batch before execution: ambiguous IDs or opposing plans block all contenders.
        candidates, seen_ids, by_symbol = [], {}, {}
        for path in transport.incoming():
            try:
                b = transport.read(path)
                for s in b["signals"]:
                    env = envelope(b, s)
                    candidates.append(env)
                    seen_ids.setdefault(s["id"], set()).add(canonical(env))
                    if timestamp(s["valid_from"]) <= utcnow() < timestamp(s["valid_until"]):
                        by_symbol.setdefault(config["symbols"].get(s["instrument"], {}).get("broker", s["instrument"]), set()).add(s["id"])
            except Exception as exc:
                decisions.append({"file": path.name, "status": "REJECTED", "reason": str(exc)})
        for item in scan:
            env = item.get("signal")
            if env:
                s = env["signal"]
                candidates.append(env)
                seen_ids.setdefault(s["id"], set()).add(canonical(env))
                by_symbol.setdefault(config["symbols"][s["instrument"]]["broker"], set()).add(s["id"])
        processed = set()
        for env in candidates:
            s = env["signal"]
            if canonical(env) in processed:
                continue
            processed.add(canonical(env))
            try:
                symbol = config["symbols"].get(s["instrument"], {}).get("broker", s["instrument"])
                if len(seen_ids[s["id"]]) != 1 or len(by_symbol.get(symbol, set())) > 1:
                    raise Blocked("Ambiguous batch: competing plans for the same instrument or signal ID")
                result = engine.execute(env)
                decisions.append({"signal_id": s["id"], "reason": s["reason"], **result})
            except Blocked as exc:
                decisions.append({"signal_id": s["id"], "status": "REJECTED", "reason": str(exc)})
    except Exception as exc:
        decisions.append({"status": "BLOCKED", "reason": str(exc)})
    for d in decisions:
        journal.event("decision", d)
    result, markdown = report(broker, journal, decisions, config["mode"], config)
    result.update(market_analysis=scan, collection=collection)
    if publish:
        transport.publish(result, markdown)
    if result["broker_snapshot"] is not None:
        scheduled_briefing(config, broker, journal, transport, scan)
    return result


def parser():
    p = argparse.ArgumentParser(description="Trading AI: local MT5 strategies, risk, execution and briefings")
    p.add_argument("--config", type=Path, default=Path("config.json"))
    p.add_argument("--state", type=Path, default=Path("state"))
    p.add_argument("--exchange", type=Path, default=Path("exchange"))
    sub = p.add_subparsers(dest="command", required=True)
    v = sub.add_parser("validate", help="Validate a briefing without connecting to MT5")
    v.add_argument("file", type=Path)
    a = sub.add_parser("approve", help="Approve exact signal content for configured account")
    a.add_argument("file", type=Path)
    a.add_argument("--signal", required=True)
    sub.add_parser("inventory", help="Read broker symbol names; does not send orders")
    sub.add_parser("snapshot", help="Export actual broker positions/history")
    reconcile = sub.add_parser("reconcile", help="Read broker evidence for uncertain operations; never send")
    reconcile.add_argument("--accept-partial-id")
    reconcile.add_argument("--note")
    sub.add_parser("probe", help="Read-only environment/account discovery without configured account")
    sub.add_parser("collect", help="Archive all seven timeframes, recent ticks and account state")
    backfill = sub.add_parser("backfill", help="Archive broker OHLCV/ticks/history in bounded chunks")
    backfill.add_argument("--from", dest="start", required=True)
    backfill.add_argument("--to", dest="end", required=True)
    sub.add_parser("analyze", help="Analyze instruments and export deterministic strategy proposals")
    briefing = sub.add_parser("briefing")
    briefing.add_argument("--session", choices=("morning", "evening"), required=True)
    sub.add_parser("observer", help="Read chart objects, screenshots and indicator buffers exported by MQL5 observer")
    sub.add_parser("calendar", help="Read MT5 economic calendar export and show entry-blocking windows")
    policy = sub.add_parser("authorize-strategy", help="Explicit local authorization for current strategy/configuration hash, at most 24h")
    policy.add_argument("--until", required=True)
    sub.add_parser("revoke-strategy")
    pending = sub.add_parser("amend-pending", help="Apply a separately approved replacement plan to an owned pending order")
    pending.add_argument("file", type=Path)
    pending.add_argument("--signal", required=True)
    pending.add_argument("--original-signal", required=True)
    pending.add_argument("--ticket", required=True, type=int)
    pending.add_argument("--activate")
    cancel = sub.add_parser("cancel", help="Explicit cancellation of an owned pending order")
    close = sub.add_parser("close", help="Explicit full/partial close of an owned position")
    close.add_argument("--volume", type=float)
    for parser_ in (cancel, close):
        parser_.add_argument("--signal", required=True)
        parser_.add_argument("--ticket", required=True, type=int)
        parser_.add_argument("--request-id", required=True)
        parser_.add_argument("--activate")
    amend = sub.add_parser("tighten-pending", help="Explicitly tighten an owned pending order's SL, preserving entry, TP and expiry")
    amend.add_argument("--signal", required=True)
    amend.add_argument("--ticket", required=True, type=int)
    amend.add_argument("--sl", required=True, type=float)
    amend.add_argument("--activate")
    run = sub.add_parser("run")
    run.add_argument("--activate", help="Manual process activation: DEMO:<login> or LIVE:<login>")
    run.add_argument("--watch", action="store_true")
    run.add_argument("--interval", type=int, default=10)
    sub.add_parser("stop", help="Create STOP marker; policy comes from local config")
    sub.add_parser("resume", help="Remove STOP; does not clear uncertain operations")
    day = sub.add_parser("day-start", help="Record operator-verified equity at 00:00 UTC; never infer intraday baseline")
    day.add_argument("--date", required=True)
    day.add_argument("--equity", required=True, type=float)
    day.add_argument("--source", required=True, help="Source of verified 00:00 UTC equity")
    sub.add_parser("simulate", help="Offline DRY_RUN fixture; no MT5 connection")
    bt = sub.add_parser("backtest", help="Offline chronological replay of archived broker OHLC; no order execution")
    bt.add_argument("--instrument", required=True)
    bt.add_argument("--contract", type=Path, required=True)
    bt.add_argument("--costs", type=Path, required=True)
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    broker = journal = None
    try:
        if args.command == "validate":
            b = validate_briefing(read_json(args.file))
            print(f'OK: {b["briefing_id"]}; {len(b["signals"])} signals (format only, not approval)')
            return 0
        if args.command == "stop":
            atomic_write(args.state / "STOP", utcnow().isoformat())
            print("STOP set. The running engine applies configured policy before its next operation.")
            return 0
        if args.command == 'revoke-strategy':
            # This marker must remain usable while the continuous engine owns its lock.
            atomic_write(args.state / 'runtime' / 'REVOKED', utcnow().isoformat())
            journal = Journal(args.state)
            journal.set_setting('strategy_policy', None)
            journal.set_setting('runtime_revoked', True)
            journal.event('operator_strategy_policy', {'policy':None, 'runtime_revoked':True})
            print('Strategy authorization revoked. Existing protective management remains active.')
            return 0
        if args.command == 'resume':
            (args.state / 'STOP').unlink(missing_ok=True)
            journal = Journal(args.state)
            journal.event('operator_resume', {})
            print('STOP cleared; authorization, quarantine and risk gates still apply.')
            return 0
        if args.command == "simulate":
            from .simulation import simulate
            print(json.dumps(simulate(args.state, args.exchange), indent=2))
            return 0
        config = load_config(args.config)
        with ExitStack() as stack:
            stack.enter_context(process_lock(args.state))
            journal = Journal(args.state)
            if args.command == "backtest":
                from .backtest import replay
                from .strategy import engine_config
                if args.instrument not in config["symbols"]:
                    raise Blocked("Instrument not configured")
                archive = MarketArchive(args.state, config["account_login"], config["account_server"], config.get("broker_time_offset_seconds", 0))
                try:
                    bars = archive.bars(config["symbols"][args.instrument]["broker"], engine_config(config)["timeframe"])
                    result = replay(config, args.instrument, bars, read_json(args.contract), read_json(args.costs))
                    path = args.exchange / "backtests" / (args.instrument+"-"+utcnow().strftime("%Y%m%dT%H%M%S")+".json")
                    atomic_write(path, canonical(result))
                    print(path.resolve())
                finally:
                    archive.close()
                return 0
            if args.command == "probe":
                broker = MT5Broker(config["terminal_path"], config.get("broker_time_offset_seconds", 0))
                t = broker.required(broker.mt5.terminal_info(), "terminal_info")
                a = broker.required(broker.mt5.account_info(), "account_info")
                info = {"read_only": True, "connected": t["connected"], "account": {k: a[k] for k in ("login", "server", "trade_mode", "currency")}, "paths": broker.paths()}
                atomic_write(args.state / "probe.json", canonical(info))
                print(json.dumps(info, indent=2))
                return 0
            if args.command == 'authorize-strategy':
                remaining = (timestamp(args.until)-utcnow()).total_seconds()
                if not 0 < remaining <= 86400 or not config["account_login"] or not config["account_server"] or config["mode"] == "DRY_RUN":
                    raise Blocked("Strategy policy needs exact account, active configured mode and expiry within 24h")
                journal.set_setting("strategy_policy", {"hash": policy_hash(config), "until": args.until})
                journal.event("operator_strategy_policy", {"policy": journal.setting("strategy_policy")})
                print("Strategy policy updated. No order sent. Process activation remains required.")
                return 0
            if args.command == "approve":
                b = validate_briefing(read_json(args.file))
                signals = [s for s in b["signals"] if s["id"] == args.signal]
                if len(signals) != 1:
                    raise Blocked("Signal not found")
                s = signals[0]
                if timestamp(s["valid_until"]) <= utcnow():
                    raise Blocked("Cannot approve an expired signal")
                journal.approve(envelope(b, s), config["account_login"], config["account_server"])
                print("Approved exact signal content locally; no order sent")
                return 0
            if args.command == "day-start":
                number(args.equity, "equity")
                if args.date != utcnow().date().isoformat() or not args.source.strip() or not config["account_login"] or not config["account_server"]:
                    raise Blocked("Today's UTC date, source, exact account and server are required")
                journal.bind_account(config["account_login"], config["account_server"])
                old = journal.setting("day_start")
                if old and old["date"] == args.date:
                    raise Blocked("Current day baseline is immutable; do not reset a daily loss limit")
                journal.set_setting("day_start", {"date": args.date, "equity": args.equity,
                    "account": config["account_login"], "server": config["account_server"], "source": args.source})
                journal.event("operator_day_start", journal.setting("day_start"))
                print("Recorded verified equity at 00:00 UTC")
                return 0
            if not config["account_login"] or not config["account_server"]:
                raise Blocked("Configure account_login/account_server before connecting to MT5")
            account_lock = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "TradingAI" / "locks" / digest([config["account_login"], config["account_server"]])
            stack.enter_context(process_lock(account_lock))
            broker = MT5Broker(config["terminal_path"], config.get("broker_time_offset_seconds", 0))
            snap = broker.snapshot()
            if snap["account"]["login"] != config["account_login"] or snap["account"]["server"] != config["account_server"]:
                raise Blocked("Account/server mismatch")
            journal.bind_account(config["account_login"], config["account_server"])
            transport = FileTransport(args.exchange)
            if args.command == "inventory":
                target = args.exchange / "broker-symbols.json"
                atomic_write(target, json.dumps(broker.inventory(), indent=2))
                atomic_write(args.exchange / "symbol-candidates.json", json.dumps(discover_symbols(broker.inventory()), indent=2))
                print(target.resolve())
            elif args.command in {"collect", "backfill"}:
                archive = MarketArchive(args.state, config["account_login"], config["account_server"], config.get("broker_time_offset_seconds", 0))
                try:
                    collector = Collector(config, broker, archive)
                    result = collector.collect() if args.command == "collect" else collector.backfill(timestamp(args.start), timestamp(args.end))
                    atomic_write(args.state / "last-collection.json", canonical(result))
                    print(json.dumps(result, indent=2))
                finally:
                    archive.close()
            elif args.command in {"analyze", "briefing"}:
                scan = SignalEngine(config, broker, journal).scan(utcnow())
                if args.command == "analyze":
                    atomic_write(args.exchange / "analysis.json", json.dumps(scan, indent=2))
                    for item in scan:
                        if item["signal"]:
                            env = item["signal"]
                            b = {"schema_version": "1.0", "briefing_id": env["briefing_id"], "session": env["session"], "generated_at": env["generated_at"], "signals": [env["signal"]]}
                            atomic_write(args.exchange / "proposals" / (env["signal"]["id"]+".json"), json.dumps(b, indent=2))
                    print(args.exchange.resolve() / "analysis.json")
                else:
                    result, md = build_briefing(config, broker, journal, scan, args.session)
                    transport.publish(result, md)
                    print(args.exchange.resolve() / "outbox" / (result["report_id"]+".md"))
            elif args.command == "calendar":
                from .calendar import summary
                data=summary(config,broker,utcnow())
                atomic_write(args.exchange / "economic-calendar.json", json.dumps(data,indent=2))
                print(json.dumps(data,indent=2))
            elif args.command == "observer":
                from .observer import read_observer
                data = read_observer(broker.paths()["data_path"], config["account_login"], config["account_server"])
                atomic_write(args.exchange / "chart-observer.json", json.dumps(data, indent=2))
                print(json.dumps(data, indent=2))
            elif args.command in {"amend-pending", "close", "cancel"}:
                signal_id = args.original_signal if args.command == "amend-pending" else args.signal
                row = journal.db.execute("SELECT payload FROM signals WHERE id=?", (signal_id,)).fetchone()
                if not row:
                    raise Blocked("Unknown original signal")
                old = json.loads(row[0])
                engine = ExecutionEngine(RiskManager(config, broker, journal, args.activate, config_loader=lambda: load_config(args.config)))
                if args.command == "amend-pending":
                    b = validate_briefing(read_json(args.file))
                    found = [s for s in b["signals"] if s["id"] == args.signal]
                    if len(found) != 1:
                        raise Blocked("Replacement signal not found")
                    decision = engine.execute(envelope(b, found[0]), "AMEND_PENDING", args.ticket, old_env=old)
                else:
                    rule = "OPERATOR_CLOSE" if args.command == "close" else "OPERATOR_CANCEL"
                    journal.event("operator_request", {"rule": rule, "ticket": args.ticket, "request_id": args.request_id})
                    decision = engine.execute(old, rule, args.ticket, close_volume=getattr(args, "volume", None), operation_id=args.request_id)
                result, md = report(broker, journal, [decision], config["mode"], config)
                transport.publish(result, md)
                print(json.dumps(decision))
            elif args.command == "tighten-pending":
                row = journal.db.execute("SELECT payload FROM signals WHERE id=?", (args.signal,)).fetchone()
                if not row:
                    raise Blocked("Unknown approved signal")
                env = json.loads(row[0])
                engine = ExecutionEngine(RiskManager(config, broker, journal, args.activate, config_loader=lambda: load_config(args.config)))
                journal.event("operator_tighten_pending", {"signal_id": args.signal, "ticket": args.ticket, "sl": args.sl})
                decision = engine.execute(env, "TIGHTEN_PENDING", args.ticket, args.sl)
                result, markdown = report(broker, journal, [decision], config["mode"], config)
                transport.publish(result, markdown)
                print(json.dumps(decision))
            elif args.command in {"snapshot", "reconcile"}:
                executor = ExecutionEngine(RiskManager(config, broker, journal))
                decisions = executor.reconcile() if args.command == "reconcile" else []
                if args.command == "reconcile" and args.accept_partial_id:
                    decisions.append(executor.accept_partial(args.accept_partial_id,args.note))
                result, markdown = report(broker, journal, decisions, config["mode"], config)
                transport.publish(result, markdown)
                print(args.exchange.resolve() / "outbox" / (result["report_id"] + ".md"))
            else:
                if args.interval < 1:
                    raise Blocked("Interval must be >= 1 second")
                while True:
                    config = load_config(args.config)  # mode and STOP policy re-read every cycle
                    result = cycle(config, broker, journal, transport, args.activate, lambda: load_config(args.config))
                    print(json.dumps({"report_id": result["report_id"], "quarantined": result["execution_quarantined"],
                                      "decisions": [{k: d[k] for k in ("signal_id", "status", "reason") if k in d} for d in result["decisions"]]}))
                    if not args.watch:
                        break
                    if result["broker_error"]:
                        try:
                            broker.reconnect()
                        except Blocked as exc:
                            journal.event("reconnect_blocked", {"reason": str(exc)})
                    time.sleep(args.interval)
        return 0
    except (Blocked, OSError, ValueError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("Stopped; broker-side protective SL/TP remain active.")
        return 130
    finally:
        if broker:
            broker.close()
        if journal:
            journal.close()
