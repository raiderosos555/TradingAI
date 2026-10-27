import json
import unittest
from pathlib import Path
from integrated_control import make,generate,run,Blocked


class FrozenIntegrationTests(unittest.TestCase):
    def scenario(self,side='SELL'):
        s=make(side);self.addCleanup(s.close);return s

    def test_buy_pipeline_uses_ask_and_bid_and_all_management_rules(self):
        result=run('BUY');ledger=result['ledger']
        self.assertEqual(ledger[0]['price'],100.02)
        self.assertEqual(ledger[1]['price'],102.07)
        self.assertEqual([o['payload']['rule'] for o in result['operations']],['OPEN','TP1','BREAK_EVEN','TRAILING'])
        self.assertEqual([d['volume'] for d in ledger],[.04,.02,.02])
        self.assertEqual(ledger[-1]['source'],'SERVER_TP')

    def test_sell_pipeline_uses_bid_and_ask(self):
        result=run('SELL')
        self.assertEqual(result['ledger'][0]['price'],100.)
        self.assertEqual(result['ledger'][1]['price'],97.99)
        self.assertEqual(result['ledger'][-1]['source'],'SERVER_TP')

    def test_calendar_is_not_bypassed_by_generated_signal(self):
        s=self.scenario();env=generate(s)
        p=Path(s.c['calendar']['path']);d=json.loads(p.read_text())
        d['events'][0]['start_utc']=d['events'][0]['end_utc']=s.start.timestamp()+300
        p.write_text(json.dumps(d))
        with self.assertRaisesRegex(Blocked,'Economic calendar'):s.e.execute(env)
        self.assertFalse(s.b.sent)

    def test_missing_calendar_does_not_become_empty_calendar(self):
        s=self.scenario();env=generate(s);Path(s.c['calendar']['path']).unlink()
        with self.assertRaisesRegex(Blocked,'Economic calendar'):s.e.execute(env)
        self.assertFalse(s.b.sent)

    def test_no_policy_authorization_no_order(self):
        s=self.scenario();s.j.set_setting('strategy_policy',None);env=generate(s)
        with self.assertRaises(Blocked):s.e.execute(env)
        self.assertFalse(s.b.sent)

    def test_zero_quote_cannot_execute_existing_signal(self):
        s=self.scenario();env=generate(s);s.b.tick.update(bid=0.,ask=0.,flags=24)
        with self.assertRaises(Blocked):s.e.execute(env)
        self.assertFalse(s.b.sent)

    def test_no_day_baseline_no_order(self):
        s=self.scenario();env=generate(s);s.j.set_setting('day_start',None)
        with self.assertRaisesRegex(Blocked,'start of current UTC day'):s.e.execute(env)
        self.assertFalse(s.b.sent)

    def test_disconnect_no_order(self):
        s=self.scenario();env=generate(s);s.b.terminal['connected']=False
        with self.assertRaises(Blocked):s.e.execute(env)
        self.assertFalse(s.b.sent)
