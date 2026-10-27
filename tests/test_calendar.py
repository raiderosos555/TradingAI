import copy
import json
import tempfile
import unittest
from pathlib import Path
from datetime import timedelta
from trading_ai.calendar import assessment, summary, calendar_config
from trading_ai.models import Blocked, envelope
from trading_ai.simulation import SimBroker, fixture
from trading_ai.journal import Journal
from trading_ai.risk import RiskManager
from trading_ai.execution import ExecutionEngine
from trading_ai.strategy import policy_hash
from trading_ai.reporter import report


class CalendarTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name);self.file=self.root/'calendar.json'
        self.b=SimBroker();self.c,self.brief=fixture(self.b.now)
        self.c['calendar']={'enabled':True,'path':str(self.file)}
        self.env=envelope(self.brief,self.brief['signals'][0])
        self.j=Journal(self.root/'state');self.addCleanup(self.j.close)
        self.j.set_setting('day_start',{'date':self.b.now.date().isoformat(),'equity':10000,'account':123456,'server':'SIMULATOR'})
        self.r=RiskManager(self.c,self.b,self.j,'DEMO:123456',clock=lambda:self.b.now)
        self.e=ExecutionEngine(self.r)
        t=self.b.now.timestamp()
        self.data={'schema_version':'1.0','read_only':True,'status':'OK','source':'Test calendar',
                   'retrieved_at_utc':t,'coverage_from_utc':t-86400,'coverage_until_utc':t+7*86400,
                   'account_login':123456,'account_server':'SIMULATOR','server_minus_gmt_seconds':0,
                   'currencies':['USD','EUR','PLN','GBP'],
                   'events':[{'id':'release-1','name':'US release','currency':'USD','importance':3,
                              'precision':'exact','start_utc':t+3600,'end_utc':t+3600}]}
        self.save()

    def save(self): self.file.write_text(json.dumps(self.data),encoding='utf-8')
    def assess(self,alias='GOLD',until=None): return assessment(self.c,self.b,alias,self.b.now,until)
    def move(self,seconds):
        self.data['events'][0]['start_utc']=self.b.now.timestamp()+seconds
        self.data['events'][0]['end_utc']=self.b.now.timestamp()+seconds
        self.save()

    def test_outside_event_window_clear(self): self.assertEqual(self.assess()['status'],'CLEAR')
    def test_before_boundary_blocks(self):
        self.move(1800);self.assertEqual(self.assess()['status'],'BLOCKED')
    def test_after_boundary_blocks(self):
        self.move(-900);self.assertEqual(self.assess()['status'],'BLOCKED')
    def test_after_window_clear(self):
        self.move(-901);self.assertEqual(self.assess()['status'],'CLEAR')
    def test_other_currency_does_not_block(self):
        self.move(0);self.assertEqual(self.assess('EURPLN')['status'],'CLEAR')
    def test_low_impact_does_not_block(self):
        self.move(0);self.data['events'][0]['importance']=1;self.save()
        self.assertEqual(self.assess()['status'],'CLEAR')
    def test_missing_file_fails_closed(self):
        self.file.unlink();self.assertEqual(self.assess()['status'],'UNAVAILABLE')
    def test_stale_feed_fails_closed(self):
        self.data['retrieved_at_utc']-=901;self.save();self.assertEqual(self.assess()['status'],'UNAVAILABLE')
    def test_incomplete_provider_fails_closed(self):
        self.data['status']='UNAVAILABLE';self.save();self.assertEqual(self.assess()['status'],'UNAVAILABLE')
    def test_wrong_account_fails_closed(self):
        self.data['account_login']=2;self.save();self.assertEqual(self.assess()['status'],'UNAVAILABLE')
    def test_offset_mismatch_fails_closed(self):
        self.data['server_minus_gmt_seconds']=7200;self.save();self.assertEqual(self.assess()['status'],'UNAVAILABLE')
    def test_duplicate_id_fails_closed(self):
        self.data['events']*=2;self.save();self.assertEqual(self.assess()['status'],'UNAVAILABLE')
    def test_empty_calendar_not_assumed_clear(self):
        self.data['events']=[];self.save();self.assertEqual(self.assess()['status'],'UNAVAILABLE')
    def test_unknown_time_blocks_whole_day(self):
        e=self.data['events'][0];e.update(precision='day',start_utc=self.b.now.timestamp()-3600,end_utc=self.b.now.timestamp()+23*3600)
        self.save();self.assertEqual(self.assess()['status'],'BLOCKED')
    def test_pending_expiry_cannot_cross_future_event(self):
        self.env['signal'].update(kind='BUY_LIMIT',entry=99.5,sl=98.5,tp=102)
        self.env['signal']['structure']['invalidation']=98.6
        with self.assertRaisesRegex(Blocked,'Economic calendar'):
            self.r.prepare_open(self.env)
    def test_uncovered_horizon_fails_closed(self):
        self.assertEqual(self.assess(until=self.b.now+timedelta(days=8))['status'],'UNAVAILABLE')
    def test_risk_manager_blocks_market_entry(self):
        self.move(60)
        with self.assertRaisesRegex(Blocked,'Economic calendar'): self.e.execute(self.env)
        self.assertFalse(self.b.sent)
    def test_calendar_does_not_block_protective_close(self):
        self.c['mode']='DEMO';self.j.approve(self.env,123456,'SIMULATOR')
        self.assertEqual(self.e.execute(self.env)['status'],'CONFIRMED')
        self.move(0)
        self.assertEqual(self.e.execute(self.env,'OPERATOR_CLOSE',self.b.positions[0]['ticket'])['status'],'CONFIRMED')
        self.assertFalse(self.b.positions)
    def test_existing_pending_canceled_on_calendar_failure(self):
        self.c['calendar']['enabled']=False
        self.env['signal'].update(kind='BUY_LIMIT',entry=99.5,sl=98.5,tp=102)
        self.env['signal']['structure']['invalidation']=98.6
        self.c['mode']='DEMO';self.j.approve(self.env,123456,'SIMULATOR')
        self.e.execute(self.env)
        self.c['calendar']['enabled']=True;self.file.unlink()
        result=self.e.execute(self.env,'CANCEL_PENDING',self.b.orders[0]['ticket'])
        self.assertEqual(result['status'],'CONFIRMED');self.assertFalse(self.b.orders)
    def test_calendar_settings_bound_to_strategy_authorization(self):
        before=policy_hash(self.c);self.c['calendar']['before_minutes']=60
        self.assertNotEqual(before,policy_hash(self.c))
    def test_report_has_calendar_without_trading(self):
        result,md=report(self.b,self.j,[],'DRY_RUN',self.c)
        self.assertEqual(result['economic_calendar']['status'],'READY')
        self.assertIn('US release',md);self.assertFalse(self.b.sent)
    def test_invalid_window_config_rejected(self):
        self.c['calendar']['before_minutes']=-1
        with self.assertRaises(Blocked): calendar_config(self.c)

if __name__=='__main__': unittest.main()
