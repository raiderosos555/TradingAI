from datetime import datetime
from zoneinfo import ZoneInfo

from .journal import atomic_write
from .models import Blocked, canonical, utcnow
from .reporter import report
from .risk import RiskManager


def build_briefing(config, broker, journal, scan, session, now=None):
    now = now or utcnow()
    # Carry today's persisted reasons into scheduled Markdown as well as JSON.
    latest = {}
    for event in journal.events():
        if event["at"][:10] == now.date().isoformat() and event["kind"] in {"decision", "management_decision"}:
            d = event["payload"]
            latest[(d.get("signal_id"), d.get("rule"), d.get("file"))] = d
    decisions = list(latest.values())
    preview = RiskManager({**config, "mode": "DRY_RUN"}, broker, journal)
    snapshot = broker.snapshot()
    for order in snapshot["orders"]:
        roots = [op for op in journal.operations() if op["status"] == "CONFIRMED"
                 and op["payload"]["rule"] == "OPEN" and (op["result"] or {}).get("order") == order["ticket"]]
        decision = {"ticket": order["ticket"], "rule":"PENDING_REVIEW", "signal_id":str(order["ticket"])}
        if len(roots) != 1:
            decision.update(status="UNMANAGED", reason="Zlecenie nie należy do potwierdzonego planu systemu")
        else:
            env = journal.effective_operation(roots[0])["payload"]["envelope"]
            decision["signal_id"] = env["signal"]["id"]
            try:
                preview.prepare_managed(env, "CANCEL_PENDING", order["ticket"])
                decision.update(status="CANCEL_REQUIRED", reason="Reguła anulowania spełniona; raport nie wysyła dyspozycji")
            except Blocked as exc:
                decision.update(status="HELD_OR_BLOCKED", reason=str(exc))
        decisions.append(decision)
    result, operational = report(broker, journal, decisions, config["mode"], config)
    result["report_id"] = session+"-"+result["report_id"]
    result["briefing_session"] = session
    result["market_analysis"] = scan
    proposals = []
    for item in scan:
        if not item.get("signal"):
            continue
        env = item["signal"]
        s = env["signal"]
        proposal = {"signal": s, "rr": abs(s["tp"]-s["entry"])/abs(s["entry"]-s["sl"]), "risk_check": "BLOCKED"}
        try:
            request, metadata = preview.prepare_open(env)
            proposal.update(volume=request["volume"], risk_cash=metadata["risk_cash"], risk_check="PASSED_PREVIEW")
        except Blocked as exc:
            proposal["risk_reason"] = str(exc)
        proposals.append(proposal)
    result["proposals"] = proposals
    lines = [f'# Briefing {"poranny" if session == "morning" else "wieczorny"}', "", f'Czas: {now.isoformat()}',
             f'Tryb: {config["mode"]}. Propozycje wymagają przejścia pełnej kontroli przed wykonaniem.', "",
             "## Obserwowane instrumenty", "", "| Instrument | Trend | RSI14 | MACD | ATR14 | Sytuacja |", "|---|---|---|---|---|---|"]
    for item in scan:
        f = item.get("analysis")
        if f:
            lines.append(f'| {item["instrument"]} | {f["trend"]} | {f["rsi14"]:.2f} | {f["macd"]:.5f} | {f["atr14"]:.5f} | wybicie={f["breakout"]}; fałszywe={f["false_breakout"]}; konsolidacja={f["consolidating"]} |')
        else:
            lines.append(f'| {item["instrument"]} | brak danych | — | — | — | {item["reason"].replace(chr(10), " ").replace("|", "/")} |')
    lines += ["", "## Plany i ryzyko", "", "| ID | Kierunek | Wejście | SL | TP2 | R:R | Ryzyko % | Loty | Kontrola |", "|---|---|---|---|---|---|---|---|---|"]
    for p in proposals:
        s = p["signal"]
        lines.append(f'| {s["id"]} | {s["kind"]} | {s["entry"]} | {s["sl"]} | {s["tp"]} | {p["rr"]:.2f} | {s["risk_pct"]} | {p.get("volume", "—")} | {p.get("risk_reason", p["risk_check"])} |')
    if not proposals:
        lines += ["", "Brak kompletnego setupu — bez nowej propozycji transakcji."]
    # Operational report includes positions, executions, P&L and management reasons from persistent journal.
    lines += ["", operational]
    return result, "\n".join(lines)


def scheduled_briefing(config, broker, journal, transport, scan, now=None):
    now = now or utcnow()
    settings = config.get("briefings", {"timezone": "Europe/Warsaw", "morning": "09:00", "evening": "18:00"})
    local = now.astimezone(ZoneInfo(settings["timezone"]))
    available = [s for s in ("morning", "evening") if local.strftime("%H:%M") >= settings[s]]
    if not available:
        return None
    session = max(available, key=lambda s: settings[s])
    key = "briefing:"+local.date().isoformat()+":"+session
    if journal.setting(key):
        return None
    result, md = build_briefing(config, broker, journal, scan, session, now)
    transport.publish(result, md)
    atomic_write(transport.root / "outbox" / ("latest-"+session+".json"), canonical({"report_id": result["report_id"], "json": result["report_id"]+".json", "markdown": result["report_id"]+".md"}))
    journal.set_setting(key, result["report_id"])
    return result["report_id"]
