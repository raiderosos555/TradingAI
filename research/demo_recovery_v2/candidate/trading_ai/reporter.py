import uuid

from .models import utcnow


def pnl(deals):
    return sum(sum(d.get(k, 0) for k in ("profit", "commission", "swap", "fee")) for d in deals)


def report(broker, journal, decisions, mode, config=None):
    now = utcnow()
    error, snapshot = None, None
    try:
        snapshot = broker.snapshot()
        bound = journal.setting("account")
        if bound is not None and bound != [snapshot["account"]["login"], snapshot["account"]["server"]]:
            snapshot = None
            raise ValueError("Broker account differs from journal: refusing to mix account reports")
    except Exception as exc:
        error = str(exc)
    results = []
    if snapshot:
        for op in journal.operations():
            if op["status"] != "CONFIRMED" or op["payload"]["rule"] != "OPEN":
                continue
            try:
                op = journal.effective_operation(op)
                if any(o['ticket']==op['result']['order'] for o in snapshot['orders']):
                    continue  # Active pending orders are listed directly from the broker snapshot.
                orders = broker.order_history(op["result"]["order"])
                ids = {o.get("position_id") for o in orders if o.get("position_id")}
                for pid in ids:
                    deals = broker.position_deals(pid)
                    risk_cash = op["payload"]["metadata"]["risk_cash"]
                    daily = [d for d in snapshot["deals"] if d.get("position_id") == pid]
                    results.append({"signal_id": op["payload"]["envelope"]["signal"]["id"], "position_id": pid,
                                    "closed": not any(p["identifier"] == pid for p in snapshot["positions"]),
                                    "realized_net_lifetime": pnl(deals), "realized_net_today": pnl(daily),
                                    "initial_budget_R": risk_cash, "daily_R": pnl(daily) / risk_cash,
                                    "lifetime_R": pnl(deals) / risk_cash})
            except Exception as exc:
                results.append({"operation_id": op["id"], "error": str(exc)})
    baseline = journal.setting("day_start")
    same_day = snapshot and baseline and baseline["date"] == now.date().isoformat()
    flows = snapshot and any(d["type"] not in {0, 1} for d in snapshot["deals"])
    summary = None if not snapshot else {
        "currency": snapshot["account"]["currency"],
        "realized_net_today_account": pnl([d for d in snapshot["deals"] if d["type"] in {0, 1}]),
        "unrealized_account": sum(p["profit"] + p.get("swap", 0) for p in snapshot["positions"]),
        "equity_change_from_UTC_start": snapshot["account"]["equity"] - baseline["equity"] if same_day and not flows else None,
        "daily_realized_R_managed": sum(x.get("daily_R", 0) for x in results),
        "R_definition": "Net booked deal P&L / initial approved cash risk including configured cost buffer; unrealized P&L excluded from realized R",
        "cash_adjustments_need_review": bool(flows)}
    source = getattr(broker, "source", "MT5 broker")
    charts, chart_error = [], None
    if snapshot and callable(getattr(broker, "paths", None)):
        try:
            from .observer import read_observer
            charts = read_observer(broker.paths()["data_path"], snapshot["account"]["login"], snapshot["account"]["server"])
        except Exception as exc:
            chart_error = str(exc)
    result = {"schema_version": "1.0", "report_id": now.strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:8],
              "generated_at": now.isoformat(), "source_of_truth": source, "mode": mode,
              "broker_snapshot": snapshot, "broker_error": error, "day_start": baseline,
              "summary": summary, "position_results": results, "decisions": decisions,
              "operations": journal.operations(), "audit_events": journal.events(limit=2000),
              'audit_log': {'total_events':journal.db.execute('SELECT COUNT(*) FROM events').fetchone()[0],
                            'report_event_limit':2000, 'full_history':str((journal.root/'journal.sqlite3').resolve())},
              "execution_quarantined": journal.uncertain(), "stop_active": (journal.root / "STOP").exists(),
              "chart_observer": charts, "chart_observer_error": chart_error}
    if config:
        from .calendar import summary as calendar_summary
        result["economic_calendar"] = calendar_summary(config,broker,now)
    from .news import summary as news_summary, markdown as news_markdown
    result['news_context'] = news_summary(journal.root/'news',now)
    def safe(x):
        return str(x).replace("|", "\\|").replace("\n", " ").replace("\r", " ").replace("<", "&lt;").replace(">", "&gt;")
    lines = ["# Raport Trading AI", "", f"Czas UTC: {now.isoformat()}", f"Tryb: {mode}",
             f"Źródło cen, pozycji i wykonania: {source}.", ""]
    if error:
        lines += [f"**Brak aktualnego stanu brokera:** {safe(error)}", ""]
    lines += [news_markdown(result['news_context']), '']
    if config:
        cal=result["economic_calendar"]
        lines += ["## Kalendarz ekonomiczny", "", f'Status: {safe(cal["status"])}. {safe(cal.get("reason", ""))}', "",
                  "| Czas Warszawa | Wydarzenie | Waluta | Waga | Actual | Forecast | Previous |", "|---|---|---|---|---|---|---|"]
        for e in cal["events"]:
            vals=[e["time_warsaw"]+(" (godzina nieznana)" if e["precision"]!="exact" else ""),e["name"],e["currency"],e["importance"],e.get("actual"),e.get("forecast"),e.get("previous")]
            lines.append("| "+" | ".join(safe(x) for x in vals)+" |")
        lines += ["", "Waga publikacji nie określa kierunku ruchu. Nieplanowane wiadomości mogą nie występować w kalendarzu.", ""]
    if charts or chart_error:
        lines += [f'Obserwator wykresów: {sum(c.get("read_only") is True for c in charts)} aktualnych eksportów; '
                  f'{sum(bool(c.get("screenshot")) for c in charts)} plików PNG. Szczegóły obiektów/buforów w JSON.', ""]
        if chart_error:
            lines += [f'Błąd obserwatora: {safe(chart_error)}', ""]
    if summary:
        lines += [f'Waluta: {summary["currency"]}; wynik zaksięgowany dzisiaj: {summary["realized_net_today_account"]:.2f}; '
                  f'wynik otwartych pozycji: {summary["unrealized_account"]:.2f}.',
                  f'Zmiana equity od początku doby UTC: {summary["equity_change_from_UTC_start"]}.',
                  f'Wynik dzienny zarządzanych transakcji: {summary["daily_realized_R_managed"]:.3f} R.',
                  "R = wynik netto z transakcji / początkowy budżet ryzyka (z buforem kosztów).", ""]
        for title, items in (("Otwarte pozycje", snapshot["positions"]), ("Zlecenia oczekujące", snapshot["orders"])):
            lines += ["## " + title, "", "| Ticket | Symbol | Typ MT5 | Wolumen | Cena brokera | SL | TP | Wynik |", "|---|---|---|---|---|---|---|---|"]
            for p in items:
                vals = [p["ticket"], p["symbol"], p["type"], p.get("volume", p.get("volume_current")),
                        p.get("price_current", p.get("price_open")), p["sl"], p["tp"], p.get("profit", "—")]
                lines.append("| " + " | ".join(safe(v) for v in vals) + " |")
            lines.append("")
        lines += ["## Wykonane operacje i wyniki", ""]
        for op in result["operations"]:
            lines.append(f'- {safe(op["id"])}: {op["status"]}; reguła {safe(op["payload"]["rule"])}; odpowiedź {safe(op["result"])}')
        for p in results:
            lines.append("- " + safe(p))
        lines.append("")
    lines += ["## Decyzje i uzasadnienia", ""]
    for d in decisions:
        lines.append(f'- {safe(d.get("signal_id", d.get("file", "system")))}: {safe(d.get("status", ""))}; '
                     f'{safe(d.get("reason", d.get("rule", "")))}')
    lines += ["", "Operacje, transakcje brokera i ostatnie 2000 zdarzeń audytu znajdują się w towarzyszącym JSON; pełny audyt pozostaje w lokalnym journal.sqlite3.",
              "Raport zawiera dane rachunku. Przekazuj go do ChatGPT wyłącznie świadomie.", ""]
    return result, "\n".join(lines)
