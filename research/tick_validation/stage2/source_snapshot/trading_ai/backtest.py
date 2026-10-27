"""Chronological, pessimistic OHLC replay; costs are explicit inputs, not assumed broker terms."""
from __future__ import annotations

from datetime import datetime, timezone
from .models import Blocked, TIMEFRAMES, number
from .strategy import SignalEngine, engine_config
from .risk import floor_volume


def replay(config, alias, bars, contract, costs, initial_equity=10000.0):
    """Entry uses next bar open. Same-bar SL/TP ambiguity resolves to SL. No future indicators."""
    fields = ("point", "trade_tick_size", "digits", "volume_min", "volume_max", "volume_step", "cash_per_price_unit_per_lot")
    if any(k not in contract for k in fields):
        raise Blocked("Backtest requires explicit contract parameters and historical cash conversion")
    for k in fields:
        number(contract[k], k, minimum=-1 if k == "digits" else 0)
    for k in ("spread_points", "slippage_points", "commission_per_lot_roundtrip", "swap_per_lot_per_day"):
        if k not in costs:
            raise Blocked("All four backtest cost inputs are required")
        number(costs[k], k, minimum=-float("inf") if k.startswith("swap") else 0, strict=False)
    e = engine_config(config)
    number(initial_equity, 'initial_equity')
    if len(bars) <= e["bars"] or any(a["time"] >= b["time"] for a,b in zip(bars,bars[1:])):
        raise Blocked("Insufficient or unordered bars for chronological replay")
    spec = config['symbols'][alias]
    symbol = spec['broker']
    spread = costs["spread_points"]*contract["point"]
    slip = costs["slippage_points"]*contract["point"]
    multiplier = contract["cash_per_price_unit_per_lot"]
    class ReplayMarket:
        def market(self, name, timeframe, count):
            return {"symbol": symbol, "info": {**contract, "name": symbol, "trade_stops_level": 0, "trade_freeze_level": 0},
                    "tick": {"bid": current["open"], "ask": current["open"]+spread, "time": current["time"], "time_msc": current["time"]*1000},
                    "bars": bars[max(0,index-count):index]}
    broker = ReplayMarket()
    engine = SignalEngine(config, broker)
    equity = initial_equity
    high_water = equity
    drawdown = 0.
    drawdown_pct = 0.
    position = None
    trades, curve, skipped = [], [], []
    day, baseline = None, equity
    for index in range(e["bars"], len(bars)):
        current = bars[index]
        now = datetime.fromtimestamp(current["time"], timezone.utc)
        if day != now.date():
            day, baseline = now.date(), equity
        if position is None and equity > 0 and baseline-equity < baseline*config["risk"]["max_daily_loss_pct"]/100:
            try:
                item = engine.evaluate(alias, now)
            except Blocked as exc:
                # Closed-market gaps cannot authorize a new setup from stale candles.
                skipped.append({"time":current["time"], "reason":str(exc)})
                item = {"signal":None}
            if item["signal"]:
                s = item["signal"]["signal"]
                if (costs['spread_points'] > spec['max_spread_points'] + 1e-6
                        or spec.get('max_spread_atr_ratio') is not None
                        and spread > item['analysis']['atr'] * spec['max_spread_atr_ratio']):
                    skipped.append({'time':current['time'], 'reason':'Spread exceeds configured absolute or ATR limit'})
                    continue
                buy = s["kind"] == "BUY"
                entry = current["open"] + (spread+slip if buy else -slip)
                reserve_entry = entry+(1 if buy else -1)*spec['deviation_points']*contract['point']
                if (not (s['sl'] < reserve_entry < s['tp'] if buy else s['tp'] < reserve_entry < s['sl'])
                        or abs(s['tp']-reserve_entry)/abs(reserve_entry-s['sl']) < config['risk']['min_rr']):
                    skipped.append({'time':current['time'], 'reason':'Reward/risk after cost and deviation reserve is below limit'})
                    continue
                per_lot = abs(reserve_entry-s["sl"])*multiplier + max(spec['cost_buffer_per_lot'],costs["commission_per_lot_roundtrip"])
                budget = min(equity*min(s["risk_pct"], config["risk"]["max_trade_pct"])/100,
                             baseline*config["risk"]["max_daily_loss_pct"]/100-max(0,baseline-equity))
                volume = floor_volume(min(budget/per_lot, contract["volume_max"], spec.get('max_volume',contract['volume_max'])), contract["volume_step"])
                if volume >= contract["volume_min"]:
                    position = {"signal": s, "buy": buy, "entry": entry, "sl": s["sl"], "volume": volume,
                                "initial_volume": volume, "risk": per_lot*volume, "opened": now,
                                "realized": -costs["commission_per_lot_roundtrip"]*volume,
                                "tp1_done": False, "fills": []}
                    equity -= costs["commission_per_lot_roundtrip"]*volume
                else:
                    skipped.append({'time':current['time'], 'reason':'Risk budget cannot fund minimum lot'})
        if position:
            p = position
            buy = p["buy"]
            sign = 1 if buy else -1
            # OHLC supplied as Bid; short exits use Ask.
            hi, lo, op = [current[k]+(0 if buy else spread) for k in ("high", "low", "open")]
            stop_hit = lo <= p["sl"] if buy else hi >= p["sl"]
            tp_hit = hi >= p["signal"]["tp"] if buy else lo <= p["signal"]["tp"]
            exit_reason, exit_price = None, None
            if stop_hit:
                exit_price = min(op,p["sl"])-slip if buy else max(op,p["sl"])+slip
                exit_reason = "SL (pessimistic if TP also touched)"
            elif tp_hit:
                exit_price = p["signal"]["tp"] - sign*slip
                exit_reason = "TP2"
            else:
                tp1 = p["signal"]["management"]["tp1"]
                if not p["tp1_done"] and tp1 is not None and (hi >= tp1 if buy else lo <= tp1):
                    partial = floor_volume(p["initial_volume"]*p["signal"]["management"]["tp1_fraction"], contract["volume_step"])
                    if partial >= contract["volume_min"] and p["volume"]-partial >= contract["volume_min"]-1e-9:
                        gain = (tp1-sign*slip-p["entry"])*sign*partial*multiplier
                        p["realized"] += gain
                        equity += gain
                        p["volume"] -= partial
                        p["tp1_done"] = True
                        p["fills"].append({"rule": "TP1", "volume": partial, "at": now.isoformat()})
                closing = current["close"]+(0 if buy else spread)
                invalid = p["signal"]["structure"]["invalidation"]
                if p["signal"]["management"]["close_on_invalidation"] and (closing <= invalid if buy else closing >= invalid):
                    exit_price, exit_reason = closing-sign*slip, "INVALIDATION"
                else:
                    r = abs(p["signal"]["entry"]-p["signal"]["sl"])
                    gained = (closing-p["entry"])*sign
                    m = p["signal"]["management"]
                    candidates = [p["sl"]]
                    if m["break_even_r"] is not None and gained >= r*m["break_even_r"]:
                        candidates.append(p["entry"])
                    if m["trailing_distance"] is not None and gained >= max(r,m["trailing_distance"]):
                        candidates.append(closing-sign*m["trailing_distance"])
                    p["sl"] = max(candidates) if buy else min(candidates)  # applies starting next candle
            if exit_price is None and index == len(bars)-1:
                exit_price, exit_reason = current["close"]+(0 if buy else spread)-sign*slip, "END_OF_SAMPLE"
            if exit_price is not None:
                closed_at = datetime.fromtimestamp(current['time']+TIMEFRAMES[e['timeframe']], timezone.utc)
                holding_days = (closed_at-p["opened"]).total_seconds()/86400
                # A deliberately explicit constant swap approximation, reported as such.
                swap = costs["swap_per_lot_per_day"]*p["initial_volume"]*holding_days
                gain = (exit_price-p["entry"])*sign*p["volume"]*multiplier + swap
                equity += gain
                net = p["realized"]+gain
                trades.append({"signal_id": p["signal"]["id"], 'strategy':p['signal']['strategy'], "opened": p["opened"].isoformat(), "closed": closed_at.isoformat(),
                               "entry": p["entry"], "exit": exit_price, "reason": exit_reason, "net": net,
                               "R": net/p["risk"], "initial_risk": p["risk"], "volume": p["initial_volume"], "fills": p["fills"]})
                position = None
        marked = equity
        if position:
            exit_mark = current["close"]+(0 if position["buy"] else spread)
            marked += (exit_mark-position["entry"])*(1 if position["buy"] else -1)*position["volume"]*multiplier
        high_water = max(high_water,marked)
        drawdown = max(drawdown,high_water-marked)
        drawdown_pct = max(drawdown_pct,100*(high_water-marked)/high_water)
        curve.append({"time": current["time"], "equity": marked})
    wins, losses = sum(max(0,t["net"]) for t in trades), -sum(min(0,t["net"]) for t in trades)
    return {"schema_version": "1.0", "simulation": True, "instrument": alias, "trades": trades,
            "initial_equity":initial_equity, "net": equity-initial_equity, "max_drawdown_cash": drawdown,
            'max_drawdown_pct':drawdown_pct, "profit_factor": wins/losses if losses else None,
            "win_rate": sum(t["net"]>0 for t in trades)/len(trades) if trades else None,
            "sum_R": sum(t["R"] for t in trades), "equity_curve": curve, "costs": costs, "contract": contract,
            "skipped_setups": skipped,
            "limitations": ["OHLC replay is distinct from execution testing", "Signal on closed candles; next-open entry; SL first if ambiguous",
                            "Fixed spread/slippage and constant historical cash conversion; swap is a constant daily approximation",
                            "Independent instrument replay; no shared portfolio slots, historical calendar, margin or order_check simulation",
                            "Hourly management and constant costs differ from the running tick-based engine",
                            "No profitability claim; use out-of-sample broker history and realistic historical FX/costs"]}
