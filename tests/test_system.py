import copy
import json
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path

from trading_ai.cli import cycle
from trading_ai.execution import ExecutionEngine
from trading_ai.journal import Journal, process_lock
from trading_ai.manager import PositionManager
from trading_ai.models import Blocked, envelope, read_json, validate_briefing
from trading_ai.reporter import report
from trading_ai.risk import RiskManager
from trading_ai.simulation import SimBroker, fixture
from trading_ai.sync import FileTransport


class SystemTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.b = SimBroker()
        self.c, self.plan = fixture(self.b.now)
        self.env = envelope(self.plan, self.plan["signals"][0])
        self.j = Journal(self.root / "state")
        self.addCleanup(lambda: self.j.close())
        self.j.set_setting("day_start", {"date": self.b.now.date().isoformat(), "equity": 10000,
                                        "account": 123456, "server": "SIMULATOR"})
        self.r = RiskManager(self.c, self.b, self.j, clock=lambda: self.b.now)
        self.e = ExecutionEngine(self.r)

    def active(self):
        self.c["mode"] = "DEMO"
        self.r.activation = "DEMO:123456"
        self.j.approve(self.env, 123456, "SIMULATOR")

    def open(self):
        self.active()
        self.assertEqual(self.e.execute(self.env)["status"], "CONFIRMED")
        return self.b.positions[0]

    def blocked(self, fragment):
        with self.assertRaisesRegex(Blocked, fragment):
            self.e.execute(self.env)
        self.assertFalse(self.b.sent)

    def test_dry_run_does_not_send_or_consume_signal(self):
        self.assertEqual(self.e.execute(self.env)["status"], "DRY_RUN")
        self.assertFalse(self.b.sent)
        self.assertFalse(self.j.operations())
        self.active()
        self.assertEqual(self.e.execute(self.env)["status"], "CONFIRMED")

    def test_schema_unknown_fields_duplicate_keys_nonfinite(self):
        for change in (lambda s: s.update(authorized=True), lambda s: s.update(risk_pct=float("nan")),
                       lambda s: s.update(sl=None), lambda s: s.update(kind="UNKNOWN"),
                       lambda s: s.update(valid_until="2026-10-23T00:00:00")):
            with self.subTest(change=change):
                b = copy.deepcopy(self.plan)
                change(b["signals"][0])
                with self.assertRaises(Blocked):
                    validate_briefing(b)
        path = self.root / "bad.json"
        path.write_text('{"a":1,"a":2}')
        with self.assertRaisesRegex(Blocked, "Duplicate"):
            read_json(path)

    def test_missing_local_approval(self):
        self.c["mode"], self.r.activation = "DEMO", "DEMO:123456"
        self.blocked("approval")

    def test_missing_activation(self):
        self.active()
        self.r.activation = None
        self.blocked("activation")

    def test_demo_rejects_real_account(self):
        self.active()
        self.b.account["trade_mode"] = 2
        self.blocked("demo account")

    def test_live_locked(self):
        self.active()
        self.c["mode"], self.r.activation, self.b.account["trade_mode"] = "LIVE", "LIVE:123456", 2
        self.blocked("LIVE is locked")

    def test_account_server_mismatch(self):
        self.b.account["server"] = "WRONG"
        self.blocked("Account")

    def test_journal_account_binding(self):
        self.j.bind_account(999, "OTHER")
        self.blocked("different account")

    def test_changed_content_cannot_reuse_id(self):
        self.j.register(self.env)
        self.env["signal"]["reason"] = "changed"
        self.blocked("reused")

    def test_expired_future_signals(self):
        self.env["signal"]["valid_until"] = (self.b.now-timedelta(seconds=1)).isoformat()
        self.env["signal"]["valid_from"] = (self.b.now-timedelta(hours=1)).isoformat()
        self.blocked("expired")

    def test_stale_ticks(self):
        self.b.tick["time_msc"] -= 61000
        self.blocked("Stale")

    def test_future_ticks(self):
        self.b.tick["time_msc"] += 61000
        self.blocked("future")

    def test_spread(self):
        self.b.tick["ask"] = 101
        self.blocked("Spread")

    def test_price_divergence(self):
        self.c["symbols"]["GOLD"]["max_entry_deviation_points"] = 1
        self.b.quote(100.10)
        self.blocked("too far")

    def test_structure_divergence(self):
        self.env["signal"]["structure"]["trend"] = "DOWN"
        self.blocked("structure disagrees")

    def test_setup_invalidated(self):
        self.b.quote(99)
        self.blocked("invalidated")

    def test_missing_symbol_mapping(self):
        self.c["symbols"] = {}
        self.blocked("mapping")

    def test_missing_baseline(self):
        self.j.set_setting("day_start", None)
        self.blocked("Missing verified")

    def test_daily_loss_realized_and_unrealized(self):
        self.b.account["equity"] = 9899
        self.blocked("Daily equity")

    def test_daily_remaining_budget(self):
        self.b.account["equity"] = 9910
        self.blocked("Remaining daily")

    def test_cash_adjustment_blocks(self):
        self.b.deals.append({"type": 2})
        self.blocked("cash adjustment")

    def test_size_actual_contract_volume_grid(self):
        req, metadata = self.r.prepare_open(self.env)
        self.assertAlmostEqual(req["volume"], .23)
        self.assertLessEqual(metadata["risk_cash"], 25)
        self.assertNotIn("price", req)  # market execution request

    def test_min_lot_no_up_rounding(self):
        self.b.info["volume_min"] = 1
        self.blocked("minimum lot")

    def test_margin_limit(self):
        self.b.account["margin_free"] = 1
        self.blocked("margin reserve")

    def test_missing_sl_existing_account(self):
        self.b.positions.append({"symbol": "OTHER", "sl": 0})
        self.blocked("no protective SL")

    def test_same_symbol_manual_netting_blocked(self):
        self.b.account["margin_mode"] = 0
        self.b.positions.append({"symbol": "TEST_GOLD", "magic": 0})
        self.blocked("Existing symbol")

    def test_pending_expiration_and_reservation(self):
        s = self.env["signal"]
        s.update(kind="BUY_LIMIT", entry=99.5, sl=98.5, tp=102)
        s["structure"]["invalidation"] = 98.6
        self.active()
        self.assertEqual(self.e.execute(self.env)["status"], "CONFIRMED")
        self.assertEqual(self.b.sent[0]["type_time"], 2)
        self.assertEqual(self.b.sent[0]["type_filling"], 2)
        self.b.now += timedelta(hours=9)
        self.b.tick["time_msc"] = int(self.b.now.timestamp()*1000)
        outcome = self.e.execute(self.env, "CANCEL_PENDING", self.b.orders[0]["ticket"])
        self.assertEqual(outcome["status"], "CONFIRMED")
        self.assertFalse(self.b.orders)

    def test_pending_server_expiration_required(self):
        self.env["signal"].update(kind="BUY_STOP", entry=100.5, tp=103)
        self.b.info["expiration_mode"] = 1
        self.blocked("server-side")

    def test_pending_wrong_side(self):
        self.env["signal"].update(kind="BUY_LIMIT", entry=100.5, tp=103)
        self.blocked("wrong side")

    def test_tick_grid(self):
        self.env["signal"]["sl"] = 99.001
        self.blocked("tick size")

    def test_stops_and_freeze(self):
        self.b.info["trade_freeze_level"] = 200
        self.blocked("stops/freeze")

    def test_broker_check_rejection(self):
        self.b.check_code = 10016
        self.blocked("order_check")

    def test_idempotent_restart_no_second_order(self):
        self.open()
        self.j.close()
        self.j = Journal(self.root / "state")
        self.r.j, self.e.j = self.j, self.j
        with self.assertRaises(Blocked):
            self.e.execute(self.env)
        self.assertEqual(len(self.b.sent), 1)

    def test_timeout_quarantines_no_retry(self):
        self.active()
        self.b.send_error = TimeoutError("lost response")
        with self.assertRaisesRegex(Blocked, "interrupted"):
            self.e.execute(self.env)
        self.assertTrue(self.j.uncertain())
        with self.assertRaisesRegex(Blocked, "Uncertain"):
            self.e.execute(self.env)
        self.assertEqual(len(self.b.sent), 1)
        self.assertEqual(self.e.reconcile()[0]["status"], "UNCERTAIN")

    def test_partial_fill_quarantines(self):
        self.active()
        self.b.send_code = 10010
        self.assertEqual(self.e.execute(self.env)["status"], "UNCERTAIN")
        self.assertTrue(self.j.uncertain())
        self.assertEqual(self.e.reconcile()[0]["status"], "UNCERTAIN")

    def test_post_send_disconnect_reconcile(self):
        self.active()
        original = self.b.send
        def send(req):
            result = original(req)
            self.b.snapshot_error = True
            return result
        self.b.send = send
        with self.assertRaises(Blocked):
            self.e.execute(self.env)
        self.assertTrue(self.j.uncertain())
        self.b.snapshot_error = False
        self.assertEqual(self.e.reconcile()[0]["status"], "CONFIRMED")
        self.assertFalse(self.j.uncertain())
        self.assertEqual(len(self.b.sent), 1)

    def test_stop_blocks_new_entries(self):
        (self.j.root / "STOP").touch()
        self.blocked("STOP")

    def test_break_even_then_trailing(self):
        p = self.open()
        self.b.quote(101.2)
        self.assertEqual(self.e.execute(self.env, "BREAK_EVEN", p["ticket"])["status"], "CONFIRMED")
        self.assertEqual(p["sl"], p["price_open"])
        self.assertEqual(self.e.execute(self.env, "TRAILING", p["ticket"])["status"], "CONFIRMED")
        self.assertGreater(p["sl"], p["price_open"])

    def test_partial_close_once_and_tp2(self):
        p = self.open()
        before = p["volume"]
        self.b.quote(101.6)
        self.assertEqual(self.e.execute(self.env, "TP1", p["ticket"])["status"], "CONFIRMED")
        self.assertGreater(p["volume"], 0)
        self.assertLess(p["volume"], before)
        with self.assertRaises(Blocked):
            self.e.execute(self.env, "TP1", p["ticket"])
        self.b.quote(102.1)
        self.assertEqual(self.e.execute(self.env, "TP2", p["ticket"])["status"], "CONFIRMED")
        self.assertFalse(self.b.positions)

    def test_invalidation_close(self):
        p = self.open()
        self.b.quote(99.05)
        self.assertEqual(self.e.execute(self.env, "INVALIDATION", p["ticket"])["status"], "CONFIRMED")

    def test_foreign_magic_management_blocked(self):
        p = self.open()
        p["magic"] = 0
        self.b.quote(101.2)
        with self.assertRaisesRegex(Blocked, "provenance"):
            self.e.execute(self.env, "BREAK_EVEN", p["ticket"])
        self.assertEqual(len(self.b.sent), 1)

    def test_mixed_netting_ownership_blocked(self):
        p = self.open()
        self.b.account["margin_mode"] = 0
        self.b.deals.append({**self.b.deals[0], "magic": 0, "order": 77})
        self.b.quote(101.2)
        with self.assertRaisesRegex(Blocked, "Mixed"):
            self.e.execute(self.env, "BREAK_EVEN", p["ticket"])

    def test_stop_manage_and_freeze(self):
        p = self.open()
        (self.j.root / "STOP").touch()
        self.b.quote(101.2)
        self.c["stop_policy"] = "freeze"
        with self.assertRaisesRegex(Blocked, "STOP"):
            self.e.execute(self.env, "BREAK_EVEN", p["ticket"])
        self.c["stop_policy"] = "manage"
        self.assertEqual(self.e.execute(self.env, "BREAK_EVEN", p["ticket"])["status"], "CONFIRMED")

    def test_stop_flatten(self):
        self.open()
        self.c["stop_policy"] = "flatten"
        (self.j.root / "STOP").touch()
        results = PositionManager(self.e).run()
        self.assertTrue(any(r["status"] == "CONFIRMED" for r in results))
        self.assertFalse(self.b.positions)

    def test_conflicting_morning_evening_no_trade(self):
        self.active()
        transport = FileTransport(self.root / "exchange")
        (transport.root / "inbox" / "morning.json").write_text(json.dumps(self.plan))
        other = copy.deepcopy(self.plan)
        other.update(session="evening", briefing_id="evening")
        other["signals"][0]["id"] = "different-plan"
        (transport.root / "inbox" / "evening.json").write_text(json.dumps(other))
        result = cycle(self.c, self.b, self.j, transport, "DEMO:123456")
        self.assertFalse(self.b.sent)
        self.assertEqual(len(result["decisions"]), 2)
        self.assertTrue(all("Ambiguous" in d["reason"] for d in result["decisions"]))
        self.assertTrue((transport.root / "outbox" / "latest.json").is_file())

    def test_report_actual_positions_costs_and_R(self):
        p = self.open()
        self.b.quote(101.6)
        self.e.execute(self.env, "TP1", p["ticket"])
        self.b.deals[-1]["commission"] = -1
        r, md = report(self.b, self.j, [], "DEMO")
        self.assertEqual(r["broker_snapshot"]["positions"][0]["volume"], p["volume"])
        self.assertGreater(r["position_results"][0]["daily_R"], 0)
        self.assertIn("Otwarte pozycje", md)

    def test_disconnected_report_not_empty_broker_state(self):
        self.b.snapshot_error = True
        r, md = report(self.b, self.j, [], "DRY_RUN")
        self.assertIsNone(r["broker_snapshot"])
        self.assertIsNotNone(r["broker_error"])

    def test_concurrent_process_lock(self):
        with process_lock(self.root):
            with self.assertRaises(Blocked):
                with process_lock(self.root):
                    pass

    def pending(self):
        s = self.env["signal"]
        s.update(kind="BUY_LIMIT", entry=99.5, sl=98.5, tp=102)
        s["structure"]["invalidation"] = 98.6
        self.active()
        self.assertEqual(self.e.execute(self.env)["status"], "CONFIRMED")
        return self.b.orders[0]

    def test_pending_amendment_tightens_only(self):
        p = self.pending()
        with self.assertRaisesRegex(Blocked, "strictly reduce"):
            self.e.execute(self.env, "TIGHTEN_PENDING", p["ticket"], 98)
        self.assertEqual(self.e.execute(self.env, "TIGHTEN_PENDING", p["ticket"], 98.7)["status"], "CONFIRMED")
        self.assertEqual(p["sl"], 98.7)
        self.assertEqual(p["price_open"], 99.5)
        self.assertEqual(p["tp"], 102)

    def test_stop_manage_cancels_pending(self):
        self.pending()
        (self.j.root / "STOP").touch()
        results = PositionManager(self.e).run()
        self.assertTrue(any(x["status"] == "CONFIRMED" for x in results))
        self.assertFalse(self.b.orders)

    def test_daily_loss_cancels_pending(self):
        self.pending()
        self.b.account["equity"] = 9800
        PositionManager(self.e).run()
        self.assertFalse(self.b.orders)

    def test_negative_margin_still_allows_reduction(self):
        p = self.open()
        self.b.account["margin_free"] = -100
        self.b.quote(99.05)
        self.assertEqual(self.e.execute(self.env, "INVALIDATION", p["ticket"])["status"], "CONFIRMED")

    def test_account_mode_checked_again_before_send(self):
        self.active()
        original = self.b.check
        def changed(req):
            result = original(req)
            self.b.account["trade_mode"] = 2
            return result
        self.b.check = changed
        self.blocked("demo account")

    def test_stop_arriving_during_check_prevents_send(self):
        self.active()
        def check(req):
            (self.j.root / "STOP").touch()
            return {"retcode": 0}
        self.b.check = check
        self.blocked("STOP")

    def test_all_six_order_types(self):
        cases = [("BUY", 100.02, 99, 102, 101.5, 99.1),
                 ("SELL", 100, 101, 98, 99, 100.9),
                 ("BUY_LIMIT", 99.5, 98.5, 102, 101, 98.6),
                 ("SELL_LIMIT", 100.5, 101.5, 98, 99, 101.4),
                 ("BUY_STOP", 100.5, 99, 103, 102, 99.1),
                 ("SELL_STOP", 99.5, 101, 97, 98, 100.9)]
        for index, (kind, entry, sl, tp, tp1, invalidation) in enumerate(cases):
            with self.subTest(kind=kind):
                env = copy.deepcopy(self.env)
                env["signal"].update(id=kind, kind=kind, entry=entry, sl=sl, tp=tp)
                env["signal"]["management"]["tp1"] = tp1
                env["signal"]["structure"]["invalidation"] = invalidation
                request, meta = self.r.prepare_open(env)
                self.assertEqual(request["type"], index)
                self.assertLessEqual(meta["risk_cash"], 25)

    def test_missing_broker_sl_after_fill_quarantines(self):
        self.active()
        original = self.b.send
        def broken(req):
            result = original(req)
            self.b.positions[0]["sl"] = 0
            return result
        self.b.send = broken
        self.assertEqual(self.e.execute(self.env)["status"], "UNCERTAIN")
        self.assertTrue(self.j.uncertain())

    def test_excessive_fill_slippage_quarantines(self):
        self.active()
        original = self.b.send
        def slipped(req):
            result = original(req)
            self.b.deals[0]["price"] += 1
            return result
        self.b.send = slipped
        self.assertEqual(self.e.execute(self.env)["status"], "UNCERTAIN")

    def test_pending_broker_minute_truncation_is_confirmed(self):
        self.env['signal'].update(kind='BUY_LIMIT', entry=99.8)
        self.active()
        original = self.b.send
        def truncated(req):
            result = original(req)
            self.b.orders[0]['time_expiration'] = req['expiration'] // 60 * 60
            return result
        self.b.send = truncated
        self.assertEqual(self.e.execute(self.env)['status'], 'CONFIRMED')

    def test_pending_broker_expiry_extension_quarantines(self):
        self.env['signal'].update(kind='BUY_LIMIT', entry=99.8)
        self.active()
        original = self.b.send
        def extended(req):
            result = original(req)
            self.b.orders[0]['time_expiration'] = req['expiration'] + 1
            return result
        self.b.send = extended
        self.assertEqual(self.e.execute(self.env)['status'], 'UNCERTAIN')

    def test_expiration_match_does_not_accept_arbitrary_change(self):
        from trading_ai.execution import expiration_matches
        requested = 1792784829
        self.assertTrue(expiration_matches(1792784820, requested))
        for actual in (0, requested + 1, requested - 1, 1792784760):
            self.assertFalse(expiration_matches(actual, requested))

    def slipped_close(self, side, slippage, partial=False):
        if side == "SELL":
            s = self.env["signal"]
            s.update(kind="SELL", entry=100, sl=101, tp=98)
            s["management"]["tp1"] = 99
            s["structure"]["invalidation"] = 100.9
        p = self.open()
        original = self.b.send
        def fill(req):
            result = original(req)
            self.b.deals[-1]["price"] += slippage * (1 if req["type"] == 0 else -1)
            return result
        self.b.send = fill
        return self.e.execute(self.env, "OPERATOR_CLOSE", p["ticket"],
                              close_volume=.01 if partial else None)

    def test_buy_close_excessive_slippage_quarantines_without_resend(self):
        self.assertEqual(self.slipped_close("BUY", .03)["status"], "UNCERTAIN")
        self.assertFalse(self.b.positions)  # Closure happened; quarantine must not retry it.
        self.c["symbols"]["GOLD"]["deviation_points"] = 100
        self.assertEqual(self.e.reconcile()[0]["status"], "UNCERTAIN")
        self.assertEqual(len(self.b.sent), 2)
        self.assertTrue(self.j.uncertain())

    def test_sell_close_excessive_slippage_quarantines(self):
        self.assertEqual(self.slipped_close("SELL", .03)["status"], "UNCERTAIN")
        self.assertFalse(self.b.positions)

    def test_partial_close_excessive_slippage_quarantines(self):
        self.assertEqual(self.slipped_close("BUY", .03, partial=True)["status"], "UNCERTAIN")
        self.assertEqual(len(self.b.positions), 1)
        self.assertTrue(self.j.uncertain())

    def test_close_slippage_boundary_is_accepted(self):
        self.assertEqual(self.slipped_close("BUY", .02)["status"], "CONFIRMED")
        op = self.j.operations()[-1]
        self.assertNotIn("price", op["payload"]["request"])
        self.assertEqual(op["payload"]["metadata"]["entry_reference"], 100)
        self.assertEqual(op["payload"]["metadata"]["fill_deviation_price"], .02)

    def test_favorable_close_price_is_accepted(self):
        self.assertEqual(self.slipped_close("SELL", -1)["status"], "CONFIRMED")

    def test_close_history_direction_mismatch_is_not_confirmed(self):
        p = self.open()
        original = self.b.send
        def wrong_side(req):
            result = original(req)
            self.b.deals[-1]["type"] = 1 - req["type"]
            return result
        self.b.send = wrong_side
        self.assertEqual(self.e.execute(self.env, "OPERATOR_CLOSE", p["ticket"])["status"], "UNCERTAIN")

    def test_reconciliation_cannot_widen_entry_slippage_limit(self):
        self.active()
        original = self.b.send
        def fill(req):
            result = original(req)
            self.b.deals[-1]["price"] += .03
            return result
        self.b.send = fill
        self.assertEqual(self.e.execute(self.env)["status"], "UNCERTAIN")
        self.c["symbols"]["GOLD"]["deviation_points"] = 100
        self.assertEqual(self.e.reconcile()[0]["status"], "UNCERTAIN")
        self.assertEqual(len(self.b.sent), 1)

    def test_position_slot_includes_pending(self):
        self.b.orders = [{"symbol": "OTHER1"}, {"symbol": "OTHER2"}]
        self.blocked("slot limit")

    def test_disabled_terminal(self):
        self.active()
        self.b.terminal["tradeapi_disabled"] = True
        self.blocked("disables automated")

    def test_future_briefing(self):
        self.env["generated_at"] = (self.b.now + timedelta(seconds=10)).isoformat()
        self.blocked("generated in the future")

    def test_unknown_broker_retcode_never_resends(self):
        self.active()
        self.b.send_code = 12345678
        self.assertEqual(self.e.execute(self.env)["status"], "UNCERTAIN")
        with self.assertRaisesRegex(Blocked, "Uncertain"):
            self.e.execute(self.env)
        self.assertEqual(len(self.b.sent), 1)

    def test_signal_changes_do_not_inherit_approval(self):
        self.active()
        self.env["signal"]["id"] = "a-new-plan"
        self.env["signal"]["reason"] = "new plan"
        self.blocked("approval")

    def test_configuration_reloaded_before_each_operation(self):
        self.active()
        locked = copy.deepcopy(self.c)
        locked["mode"] = "LIVE"
        self.r.config_loader = lambda: locked
        self.blocked("activation")

    def test_switch_to_dry_run_during_preflight_never_sends(self):
        self.active()
        dry = copy.deepcopy(self.c)
        dry["mode"] = "DRY_RUN"
        self.r.config_loader = lambda: self.c
        def check(req):
            self.r.config_loader = lambda: dry
            return {"retcode": 0}
        self.b.check = check
        self.assertEqual(self.e.execute(self.env)["status"], "DRY_RUN")
        self.assertFalse(self.b.sent)
        self.assertFalse(self.j.operations())

    def test_report_does_not_mix_accounts(self):
        self.j.bind_account(123456, "SIMULATOR")
        self.b.account["login"] = 222222
        result, md = report(self.b, self.j, [], "DRY_RUN")
        self.assertIsNone(result["broker_snapshot"])
        self.assertIn("differs", result["broker_error"])

    def test_sell_position_break_even_and_full_close(self):
        s = self.env["signal"]
        s.update(kind="SELL", entry=100, sl=101, tp=98)
        s["management"]["tp1"] = 99
        s["structure"]["invalidation"] = 100.9
        p = self.open()
        self.b.quote(98.8)
        self.assertEqual(self.e.execute(self.env, "BREAK_EVEN", p["ticket"])["status"], "CONFIRMED")
        self.assertEqual(p["sl"], 100)
        self.b.quote(97.9)
        self.assertEqual(self.e.execute(self.env, "TP2", p["ticket"])["status"], "CONFIRMED")
        self.assertEqual(self.b.sent[-1]["type"], 0)
        self.assertFalse(self.b.positions)

    def test_spread_gate_on_position_operation(self):
        p = self.open()
        self.b.quote(101.2, 102)
        with self.assertRaisesRegex(Blocked, "Spread"):
            self.e.execute(self.env, "BREAK_EVEN", p["ticket"])
        self.assertEqual(len(self.b.sent), 1)


if __name__ == "__main__":
    unittest.main()
