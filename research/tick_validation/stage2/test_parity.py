"""Independent hand-calculated assertions around frozen production decision code."""
import unittest
from datetime import timedelta
from harness import Scenario, Blocked

TRACES = {}

class Parity(unittest.TestCase):
    def scenario(self, **kwargs):
        s = Scenario(**kwargs)
        def finish():
            TRACES.setdefault(self.id(), []).append(s.trace())
            s.close()
        self.addCleanup(finish)
        return s

    def confirmed(self, results):
        return [x['rule'] for x in results if x['status'] == 'CONFIRMED']

    def test_buy_entry_ask_equity_includes_spread_and_commission(self):
        s=self.scenario(); p=s.open()
        self.assertEqual((p['price_open'], p['volume']), (100.02,.08))
        self.assertAlmostEqual(s.b.account['balance'],9999.84)
        self.assertAlmostEqual(s.b.account['equity'],9999.68)

    def test_sell_entry_bid_and_operator_exit_ask(self):
        s=self.scenario(side='SELL'); p=s.open()
        s.step(10,99.5,99.54,cycle=False)
        self.assertEqual(s.e.execute(s.env,'OPERATOR_CLOSE',p['ticket'])['status'],'CONFIRMED')
        self.assertEqual(s.b.ledger[-1]['price'],99.54)
        self.assertAlmostEqual(s.b.account['balance'],10003.36)

    def test_buy_tp1_then_be_then_trailing_one_action_per_cycle(self):
        s=self.scenario(); s.open()
        self.assertEqual(self.confirmed(s.step(10,101.6)),['TP1'])
        self.assertEqual((s.b.positions[0]['volume'],s.b.positions[0]['sl']),(.04,99.))
        self.assertEqual(self.confirmed(s.step(20,101.6)),['BREAK_EVEN'])
        self.assertEqual(s.b.positions[0]['sl'],100.02)
        self.assertEqual(self.confirmed(s.step(30,101.6)),['TRAILING'])
        self.assertEqual(s.b.positions[0]['sl'],101.1)
        self.assertEqual(self.confirmed(s.step(40,101.6)),[])
        self.assertEqual(len([d for d in s.b.ledger if d['entry']==1]),1)

    def test_sell_tp1_then_be_then_trailing(self):
        s=self.scenario(side='SELL'); s.open()
        self.assertEqual(self.confirmed(s.step(10,98.38,98.4)),['TP1'])
        self.assertEqual(self.confirmed(s.step(20,98.38,98.4)),['BREAK_EVEN'])
        self.assertEqual(s.b.positions[0]['sl'],100.)
        self.assertEqual(self.confirmed(s.step(30,98.38,98.4)),['TRAILING'])
        self.assertEqual(s.b.positions[0]['sl'],98.9)

    def test_buy_gap_stop_fills_first_bid_not_stop_level(self):
        s=self.scenario(); s.open(); s.step(10,98.7,98.74)
        self.assertEqual(s.b.ledger[-1]['price'],98.7)
        self.assertEqual(s.b.ledger[-1]['source'],'SERVER_SL')
        self.assertAlmostEqual(s.b.account['balance'],9989.12)
        self.assertFalse(s.b.positions)

    def test_sell_stop_uses_ask_even_if_bid_has_not_crossed(self):
        s=self.scenario(side='SELL'); s.open(); s.step(10,100.9,101.1)
        self.assertEqual(s.b.ledger[-1]['price'],101.1)
        self.assertEqual(s.b.server_events[0]['trigger'],'SL')
        self.assertAlmostEqual(s.b.account['balance'],9990.88)

    def test_jump_over_tp1_tp2_full_server_exit_before_application(self):
        s=self.scenario(); s.open(); results=s.step(10,104.)
        self.assertEqual(results,[])
        self.assertEqual(s.b.ledger[-1]['source'],'SERVER_TP')
        self.assertEqual(s.b.ledger[-1]['volume'],.08)
        self.assertAlmostEqual(s.b.account['balance'],10031.52)

    def test_sell_tp2_requires_ask_to_cross(self):
        s=self.scenario(side='SELL'); s.open()
        s.step(10,96.99,97.03,cycle=False)
        self.assertTrue(s.b.positions)
        s.step(20,96.95,96.99)
        self.assertFalse(s.b.positions)
        self.assertEqual(s.b.ledger[-1]['price'],96.99)

    def test_partial_then_final_cash_ledger_no_double_spread(self):
        s=self.scenario(); s.open(); s.step(10,101.6); s.step(20,103.02)
        self.assertEqual([d['volume'] for d in s.b.ledger],[.08,.04,.04])
        self.assertAlmostEqual(sum(d['profit'] for d in s.b.ledger),18.32)
        self.assertAlmostEqual(sum(d['commission'] for d in s.b.ledger),-.32)
        self.assertAlmostEqual(s.b.account['balance'],10018.)

    def test_tp1_minimum_lot_rejected_keep_server_protection(self):
        s=self.scenario(volume=.01,management={'break_even_r':None,'trailing_distance':None}); s.open()
        results=s.step(10,101.6)
        self.assertTrue(any('invalid minimum' in x.get('reason','') for x in results))
        self.assertEqual((s.b.positions[0]['volume'],s.b.positions[0]['sl']),(.01,99.))

    def test_below_minimum_lot_blocks_open(self):
        s=self.scenario(volume=.009)
        with self.assertRaises(Blocked):s.e.execute(s.env)
        self.assertFalse(s.b.sent)

    def test_wide_spread_blocks_application_be(self):
        s=self.scenario(management={'tp1':None}); s.open()
        results=s.step(10,101.2,101.3)
        self.assertFalse(self.confirmed(results))
        self.assertTrue(any('Spread exceeds' in x.get('reason','') for x in results))
        self.assertEqual(s.b.positions[0]['sl'],99.)

    def test_wide_spread_does_not_disable_server_sl(self):
        s=self.scenario(); s.open(); s.step(10,98.9,100.)
        self.assertFalse(s.b.positions)
        self.assertEqual(s.b.ledger[-1]['source'],'SERVER_SL')

    def test_be_is_price_break_even_not_cash_break_even(self):
        s=self.scenario(management={'tp1':None}); s.open()
        self.assertEqual(self.confirmed(s.step(10,101.2)),['BREAK_EVEN'])
        s.step(20,100.02,100.04)
        self.assertEqual(s.b.ledger[-1]['profit'],0.)
        self.assertAlmostEqual(s.b.account['balance'],9999.68)

    def test_trailing_buy_rounds_down_sell_rounds_up(self):
        for side,bid,ask,expected in [('BUY',101.2,101.22,100.69),('SELL',98.78,98.8,99.31)]:
            with self.subTest(side=side):
                s=self.scenario(side=side,management={'tp1':None,'break_even_r':None,'trailing_distance':.505})
                s.open(); self.assertEqual(self.confirmed(s.step(10,bid,ask)),['TRAILING'])
                self.assertEqual(s.b.positions[0]['sl'],expected)

    def test_invalidated_structure_exits_before_server_sl(self):
        s=self.scenario(); s.open()
        self.assertEqual(self.confirmed(s.step(10,99.05,99.07)),['INVALIDATION'])
        self.assertEqual(s.b.ledger[-1]['source'],'APPLICATION')
        self.assertFalse(s.b.server_events)

    def test_disconnect_server_stop_and_reconnect_no_duplicate(self):
        s=self.scenario(); s.open(); s.step(10,98.8,connected=False)
        self.assertFalse(s.b.positions)
        s.step(20,98.9,connected=True)
        self.assertEqual(len(s.b.ledger),2)
        self.assertEqual(s.b.ledger[-1]['source'],'SERVER_SL')

    def test_disconnect_delays_be_until_reconnect(self):
        s=self.scenario(management={'tp1':None}); s.open()
        s.step(10,101.2,connected=False)
        self.assertEqual(s.b.positions[0]['sl'],99.)
        self.assertEqual(self.confirmed(s.step(20,101.2)),['BREAK_EVEN'])

    def test_subcycle_tick_server_sl_still_active(self):
        s=self.scenario(); s.open(); s.step(1,98.8)
        self.assertFalse(s.b.positions)
        self.assertFalse(s.decisions)

    def test_missing_ticks_no_interpolation_known_fill_only_next_tick(self):
        s=self.scenario(); s.open(); s.step(3600,98.6)
        self.assertEqual(len(s.b.quotes),1)
        self.assertEqual(s.b.ledger[-1]['time_msc'],s.b.quotes[0]['time_msc'])
        self.assertEqual(s.b.ledger[-1]['price'],98.6)

    def test_daily_limit_includes_unrealized_and_commission(self):
        s=self.scenario(); s.open()
        self.assertAlmostEqual(s.r.daily_budget(s.b.snapshot(),s.b.now),49.68)
        # Separate explicit boundary fixture; no fabricated broker tick/history.
        snap=s.b.snapshot(); snap['account']['equity']=9950.
        with self.assertRaisesRegex(Blocked,'Daily equity'):s.r.daily_budget(snap,s.b.now)

    def test_new_utc_day_requires_new_baseline(self):
        s=self.scenario()
        with self.assertRaisesRegex(Blocked,'start of current UTC day'):
            s.r.daily_budget(s.b.snapshot(),s.b.now+timedelta(days=1))

    def test_cash_adjustment_blocks_daily_budget(self):
        s=self.scenario(); snap=s.b.snapshot(); snap['deals']=[{'type':2}]
        with self.assertRaisesRegex(Blocked,'cash adjustment'):s.r.daily_budget(snap,s.b.now)

    def test_send_failure_quarantines_and_never_retries(self):
        s=self.scenario(); s.b.send_error=TimeoutError('synthetic send interruption')
        with self.assertRaisesRegex(Blocked,'durable intent'):s.e.execute(s.env)
        s.b.send_error=None
        with self.assertRaisesRegex(Blocked,'Uncertain prior'):s.e.execute(s.env)
        self.assertEqual(len(s.b.sent),1)
        self.assertFalse(s.b.ledger)

    def test_stale_quote_blocks_entry(self):
        s=self.scenario(); s.b.now+=timedelta(seconds=11)
        with self.assertRaisesRegex(Blocked,'Stale'):s.e.execute(s.env)
        self.assertFalse(s.b.sent)

    def test_insufficient_margin_blocks_entry(self):
        s=self.scenario(); s.b.account['margin_free']=1
        with self.assertRaisesRegex(Blocked,'[Mm]argin'):s.e.execute(s.env)
        self.assertFalse(s.b.sent)

    def test_input_order_is_preserved_and_regression_rejected(self):
        s=self.scenario(); s.step(10,100.,cycle=False); s.step(10,100.01,cycle=False)
        self.assertEqual([x['bid'] for x in s.b.quotes],[100.,100.01])
        with self.assertRaisesRegex(ValueError,'Chronology'):s.step(9,100.)

    def test_wide_spread_blocks_entry_without_waiting_for_better_price(self):
        s=self.scenario(); s.b.quote(100.,100.1)
        with self.assertRaisesRegex(Blocked,'[Ss]pread'):s.e.execute(s.env)
        self.assertFalse(s.b.sent)

    def test_tp1_rounds_original_volume_down_to_step(self):
        s=self.scenario(volume=.03); s.open(); s.step(10,101.6)
        self.assertEqual(s.b.ledger[-1]['volume'],.01)
        self.assertEqual(s.b.positions[0]['volume'],.02)

    def test_existing_tp_freeze_blocks_application_modification(self):
        s=self.scenario(management={'tp1':None}); s.open()
        results=s.step(10,103.01,103.03)
        self.assertFalse(self.confirmed(results))
        self.assertTrue(any('frozen' in x.get('reason','') for x in results))
        self.assertEqual(s.b.positions[0]['sl'],99.)

    def test_trailing_rejects_new_stop_inside_stop_distance(self):
        s=self.scenario(management={'tp1':None,'break_even_r':None,'trailing_distance':.01}); s.open()
        results=s.step(10,101.2)
        self.assertFalse(self.confirmed(results))
        self.assertTrue(any('stop/freeze' in x.get('reason','') for x in results))

    def test_stop_flatten_has_priority_over_tp1(self):
        s=self.scenario(); s.open(); s.c['stop_policy']='flatten'
        (s.j.root/'STOP').write_text('synthetic fixture only')
        self.assertEqual(self.confirmed(s.step(10,101.6)),['STOP_CLOSE'])
        self.assertFalse(s.b.positions)
        self.assertEqual(s.b.ledger[-1]['volume'],.08)

    def test_application_tp2_unit_rule_when_server_fill_not_observed(self):
        # Direct policy test only, not TickBroker.feed: deliberately absent server event.
        s=self.scenario(); p=s.open(); s.b.quote(103.1,103.12)
        self.assertEqual(s.e.execute(s.env,'TP2',p['ticket'])['status'],'CONFIRMED')
        self.assertEqual(s.b.ledger[-1]['price'],103.1)
        self.assertFalse(s.b.positions)

    def test_no_baseline_blocks_new_entry(self):
        s=self.scenario(); s.j.set_setting('day_start',None)
        with self.assertRaisesRegex(Blocked,'start of current UTC day'):s.e.execute(s.env)
        self.assertFalse(s.b.sent)

    def test_daily_loss_limit_blocks_new_entry(self):
        s=self.scenario(); s.b.account['equity']=9950.
        with self.assertRaisesRegex(Blocked,'Daily equity'):s.e.execute(s.env)
        self.assertFalse(s.b.sent)

if __name__=='__main__':unittest.main()
