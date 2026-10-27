import unittest
from delayed import scenario,tick,Blocked

TRACES={}
class DelayedTests(unittest.TestCase):
    def case(self,**kwargs):
        s=scenario(**kwargs)
        def finish():
            trace=s.trace()
            trace.update(latency_model='Explicit synthetic tick delay inside synchronous ExecutionEngine send',
                         application_requests=s.b.application_requests,outcomes=s.b.outcomes,
                         operations=[dict(id=o['id'],status=o['status'],rule=o['payload']['rule']) for o in s.j.operations()])
            TRACES[self.id()]=trace
            s.close()
        self.addCleanup(finish);return s
    def open(self,s):
        s.b.arm([tick(s,50,100.)]);return s.open()
    def test_risk_blocks_wide_spread_before_any_request_or_tape_consumption(self):
        s=self.case();s.b.quote(100,100.2);s.b.arm([tick(s,50,100.)])
        with self.assertRaisesRegex(Blocked,'[Ss]pread'):s.e.execute(s.env)
        self.assertEqual(s.b.cursor,0);self.assertFalse(s.b.application_requests)
    def test_missing_daily_baseline_blocks_delayed_open(self):
        s=self.case();s.j.set_setting('day_start',None);s.b.arm([tick(s,50,100.)])
        with self.assertRaisesRegex(Blocked,'start of current UTC day'):s.e.execute(s.env)
        self.assertFalse(s.b.application_requests)
    def test_buy_fill_at_later_ask_and_cash_revalued(self):
        s=self.case();s.b.arm([tick(s,0,100.),tick(s,49,100.),tick(s,50,100.01)])
        p=s.open();self.assertEqual(p['price_open'],100.03)
        self.assertEqual(s.b.ledger[-1]['time_msc'],tick(s,50,0)['time_msc'])
        self.assertAlmostEqual(s.b.account['equity'],9999.68)
        self.assertEqual(s.b.cursor,3)
    def test_sell_fill_at_later_bid(self):
        s=self.case(side='SELL');s.b.arm([tick(s,50,99.99)])
        self.assertEqual(s.open()['price_open'],99.99)
    def test_excessive_adverse_fill_exists_but_engine_quarantines(self):
        s=self.case();s.b.arm([tick(s,50,100.1)])
        self.assertEqual(s.e.execute(s.env)['status'],'UNCERTAIN')
        self.assertEqual(s.b.positions[0]['price_open'],100.12)
        self.assertTrue(s.j.uncertain())
        with self.assertRaisesRegex(Blocked,'Uncertain prior'):s.e.execute(s.env)
        self.assertEqual(len(s.b.application_requests),1)
    def test_spread_widens_in_flight_not_retroactively_removed(self):
        s=self.case();s.b.arm([tick(s,50,100.,100.2)])
        self.assertEqual(s.e.execute(s.env)['status'],'UNCERTAIN')
        self.assertEqual(s.b.ledger[-1]['price'],100.2)
        self.assertAlmostEqual(s.b.account['equity'],9998.24)
    def test_partial_close_delayed_bid_volume_and_fee(self):
        s=self.case();p=self.open(s);s.b.feed(tick(s,100,101.6))
        s.b.arm([tick(s,150,101.59)])
        self.assertEqual(s.e.execute(s.env,'TP1',p['ticket'])['status'],'CONFIRMED')
        self.assertEqual(s.b.positions[0]['volume'],.04)
        self.assertEqual(s.b.ledger[-1]['price'],101.59)
        self.assertAlmostEqual(s.b.account['balance'],10006.04)
    def test_server_stop_during_close_latency_cannot_double_close(self):
        s=self.case();p=self.open(s)
        s.b.arm([tick(s,75,98.8),tick(s,100,98.9)])
        self.assertEqual(s.e.execute(s.env,'OPERATOR_CLOSE',p['ticket'])['status'],'UNCERTAIN')
        self.assertFalse(s.b.positions);self.assertEqual(len(s.b.ledger),2)
        self.assertEqual(s.b.ledger[-1]['source'],'SERVER_SL')
        self.assertEqual(s.b.outcomes[-1]['retcode'],10036)
    def test_no_quote_timeout_no_fill_and_no_retry(self):
        s=self.case();s.b.arm([tick(s,1100,100.)],max_wait_ms=1000)
        self.assertEqual(s.e.execute(s.env)['status'],'UNCERTAIN')
        self.assertFalse(s.b.positions);self.assertFalse(s.b.ledger);self.assertEqual(s.b.cursor,0)
        with self.assertRaisesRegex(Blocked,'Uncertain prior'):s.e.execute(s.env)
    def test_invalid_sl_after_gap_rejected_by_server_fixture(self):
        s=self.case();s.b.arm([tick(s,50,98.8)])
        self.assertEqual(s.e.execute(s.env)['status'],'UNCERTAIN')
        self.assertFalse(s.b.positions);self.assertEqual(s.b.outcomes[-1]['retcode'],10016)
    def test_be_change_uses_delayed_quote_for_server_stop_distance(self):
        s=self.case(management={'tp1':None});p=self.open(s);s.b.feed(tick(s,100,101.2))
        s.b.arm([tick(s,150,100.04)])
        self.assertEqual(s.e.execute(s.env,'BREAK_EVEN',p['ticket'])['status'],'UNCERTAIN')
        self.assertEqual(s.b.positions[0]['sl'],99.)
        self.assertEqual(s.b.outcomes[-1]['retcode'],10016)
    def test_direct_sender_without_durable_risk_checked_intent_blocked(self):
        s=self.case()
        with self.assertRaisesRegex(Blocked,'durable'):s.b.send({'action':1})
        self.assertFalse(s.b.application_requests)

if __name__=='__main__':unittest.main()
