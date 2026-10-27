import copy
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path
from unittest.mock import Mock

from trading_ai.cli import main
from trading_ai.execution import ExecutionEngine
from trading_ai.journal import Journal, process_lock
from trading_ai.manager import PositionManager
from trading_ai.models import Blocked, envelope
from trading_ai.risk import RiskManager
from trading_ai.runtime import ClockGuard, capture_boundary, configuration_hash, require_authorization, entry_blockers
from trading_ai.simulation import SimBroker, fixture


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.j = Journal(self.root)
        self.addCleanup(self.j.close)
        self.b = SimBroker()
        self.c, self.plan = fixture(self.b.now)
        self.c.update(mode='DEMO', broker_time_offset_seconds=7200)
        self.c['runtime'] = {'authorization_id':'test-window',
            'starts_at':(self.b.now-timedelta(minutes=1)).isoformat(),
            'ends_at':(self.b.now+timedelta(days=5)).isoformat()}
        self.authorize()

    def authorize(self):
        self.j.set_setting('runtime_authorization:test-window',
            {'config_hash':configuration_hash(self.c), 'allowed_offsets':[3600,7200]})
        self.j.set_setting('runtime_clock', {'at':self.b.now.isoformat(), 'offset':7200,
                                           'account':[123456,'SIMULATOR']})

    def test_authorization_valid(self):
        self.assertTrue(require_authorization(self.c,self.j,self.b.now))

    def test_health_distinguishes_running_process_from_entry_readiness(self):
        self.assertTrue(any('equity' in s for s in entry_blockers(self.c,self.b.snapshot(),self.b.now,self.j)))
        self.j.set_setting('day_start',{'date':self.b.now.date().isoformat(),'account':123456,'server':'SIMULATOR','equity':10000})
        self.assertEqual(entry_blockers(self.c,self.b.snapshot(),self.b.now,self.j),[])
        (self.root/'STOP').touch()
        self.assertIn('Emergency STOP',entry_blockers(self.c,self.b.snapshot(),self.b.now,self.j))

    def test_report_event_limit_preserves_complete_journal(self):
        for n in range(5):self.j.event('test',{'n':n})
        self.assertEqual([x['payload']['n'] for x in self.j.events(limit=2)],[3,4])
        self.assertEqual(len(self.j.events()),5)

    def test_authorization_rejects_start_and_end_boundaries(self):
        for now in [self.b.now-timedelta(minutes=2), self.b.now+timedelta(days=5)]:
            with self.assertRaisesRegex(Blocked,'window'):
                require_authorization(self.c,self.j,now)

    def test_config_mutation_requires_new_authorization(self):
        self.c['risk']['max_trade_pct'] = .1
        with self.assertRaisesRegex(Blocked,'changed'):
            require_authorization(self.c,self.j,self.b.now)

    def test_revoked_flag_and_marker(self):
        self.j.set_setting('runtime_revoked',True)
        with self.assertRaisesRegex(Blocked,'revoked'):
            require_authorization(self.c,self.j,self.b.now)
        self.j.set_setting('runtime_revoked',False)
        (self.root/'runtime').mkdir()
        (self.root/'runtime/REVOKED').touch()
        with self.assertRaisesRegex(Blocked,'revoked'):
            require_authorization(self.c,self.j,self.b.now)

    def test_live_is_never_authorized(self):
        self.c['mode'] = 'LIVE'
        with self.assertRaisesRegex(Blocked,'DEMO'):
            require_authorization(self.c,self.j,self.b.now)

    def test_only_approved_offsets_can_change(self):
        self.c['broker_time_offset_seconds'] = 3600
        proof = self.j.setting('runtime_clock'); proof['offset'] = 3600
        self.j.set_setting('runtime_clock',proof)
        require_authorization(self.c,self.j,self.b.now)
        self.c['broker_time_offset_seconds'] = 10800
        with self.assertRaisesRegex(Blocked,'offset'):
            require_authorization(self.c,self.j,self.b.now)

    def test_stale_or_wrong_account_clock_blocks(self):
        for proof in [{'at':(self.b.now-timedelta(seconds=31)).isoformat(), 'offset':7200,'account':[123456,'SIMULATOR']},
                      {'at':self.b.now.isoformat(), 'offset':7200,'account':[1,'SIMULATOR']}]:
            self.j.set_setting('runtime_clock',proof)
            with self.assertRaisesRegex(Blocked,'clock'):
                require_authorization(self.c,self.j,self.b.now)

    def test_boundary_is_actual_snapshot_and_first_writer_wins(self):
        self.b.now = self.b.now.replace(hour=0,minute=0,second=1,microsecond=0)
        self.assertTrue(capture_boundary(self.c,self.b.snapshot(),self.b.now,self.j))
        self.b.account['equity'] = 8000
        other = Journal(self.root)
        try:
            self.assertFalse(capture_boundary(self.c,self.b.snapshot(),self.b.now,other))
        finally:
            other.close()
        self.assertEqual(self.j.setting('day_start')['equity'],10000)

    def test_boundary_missed_stale_future_and_wrong_day_are_not_inferred(self):
        start = self.b.now.replace(hour=0,minute=0,second=0,microsecond=0)
        for at, now in [(start+timedelta(seconds=6),start+timedelta(seconds=6)),
                        (start+timedelta(seconds=1),start+timedelta(seconds=4)),
                        (start+timedelta(seconds=2),start+timedelta(seconds=1)),
                        (start-timedelta(seconds=1),start)]:
            self.b.now = at
            self.assertFalse(capture_boundary(self.c,self.b.snapshot(),now,self.j))
        self.assertIsNone(self.j.setting('day_start'))

    def test_boundary_rejects_wrong_account_and_real_account(self):
        self.b.now = self.b.now.replace(hour=0,minute=0,second=1,microsecond=0)
        for key,value in [('login',1),('trade_mode',2)]:
            snap = self.b.snapshot(); snap['account'][key] = value
            with self.assertRaises(Blocked):
                capture_boundary(self.c,snap,self.b.now,self.j)

    def ea(self,offset=7200,age=0):
        return {'schema_version':'1.0','read_only':True,'account_login':123456,
                'account_server':'SIMULATOR','retrieved_at_utc':self.b.now.timestamp()-age,
                'server_minus_gmt_seconds':offset}

    def raw(self,offset=7200):
        return {s:(self.b.now.timestamp()+offset)*1000 for s in ['A','B']}

    def test_clock_requires_two_distinct_exports_and_two_contracts(self):
        g = ClockGuard()
        for _ in range(2):
            with self.assertRaisesRegex(Blocked,'two distinct'):
                g.observe(self.c,self.ea(age=300),self.b.now,self.raw(),[3600,7200])
        with self.assertRaisesRegex(Blocked,'two contracts'):
            g.observe(self.c,self.ea(),self.b.now,{'A':self.raw()['A']},[3600,7200])
        self.assertEqual(g.observe(self.c,self.ea(),self.b.now,self.raw(),[3600,7200])['offset'],7200)

    def test_clock_dst_change_resets_evidence_and_checks_ticks(self):
        g = ClockGuard()
        with self.assertRaises(Blocked): g.observe(self.c,self.ea(age=300),self.b.now,self.raw(),[3600,7200])
        g.observe(self.c,self.ea(),self.b.now,self.raw(),[3600,7200])
        with self.assertRaisesRegex(Blocked,'two distinct'):
            g.observe(self.c,self.ea(3600,300),self.b.now,self.raw(3600),[3600,7200])
        with self.assertRaisesRegex(Blocked,'two contracts'):
            g.observe(self.c,self.ea(3600),self.b.now,self.raw(7200),[3600,7200])
        self.assertEqual(g.observe(self.c,self.ea(3600),self.b.now,self.raw(3600),[3600,7200])['offset'],3600)

    def test_clock_rejects_stale_forged_and_unsupported_evidence(self):
        for data in [self.ea(age=901),self.ea(10800),{**self.ea(),'account_login':1},
                     {**self.ea(),'read_only':False}]:
            with self.assertRaises(Blocked):
                ClockGuard().observe(self.c,data,self.b.now,self.raw(),[3600,7200])

    def test_expired_first_export_does_not_satisfy_second(self):
        g = ClockGuard()
        with self.assertRaises(Blocked):g.observe(self.c,self.ea(age=899),self.b.now,self.raw(),[7200])
        self.b.now += timedelta(seconds=5)
        with self.assertRaisesRegex(Blocked,'two distinct'):
            g.observe(self.c,self.ea(),self.b.now,self.raw(),[7200])

    def active_engine(self):
        self.c.pop('runtime')
        self.c['broker_time_offset_seconds'] = 0
        env = envelope(self.plan,self.plan['signals'][0])
        self.j.approve(env,123456,'SIMULATOR')
        self.j.set_setting('day_start',{'date':self.b.now.date().isoformat(),'account':123456,'server':'SIMULATOR','equity':10000})
        e = ExecutionEngine(RiskManager(self.c,self.b,self.j,'DEMO:123456',clock=lambda:self.b.now))
        return e,env

    def test_config_lot_cap_is_enforced_by_independent_risk(self):
        e,env = self.active_engine()
        self.c['symbols']['GOLD']['max_volume'] = .01
        self.assertEqual(e.execute(env)['status'],'CONFIRMED')
        self.assertEqual(self.b.positions[0]['volume'],.01)

    def test_spread_atr_filter_blocks_new_entry(self):
        e,env = self.active_engine()
        self.c['symbols']['GOLD']['max_spread_atr_ratio'] = .001
        with self.assertRaisesRegex(Blocked,'ATR'):
            e.execute(env)
        self.assertFalse(self.b.sent)

    def test_active_pending_does_not_require_order_history(self):
        self.plan['signals'][0].update(kind='BUY_LIMIT',entry=99.5,sl=98.5,tp=102)
        e,env = self.active_engine()
        self.assertEqual(e.execute(env)['status'],'CONFIRMED')
        self.b.order_history = Mock(side_effect=AssertionError('Active order is not in history'))
        self.assertTrue(PositionManager(e).run())
        self.b.order_history.assert_not_called()

    def test_revoke_works_while_runtime_holds_state_lock(self):
        with process_lock(self.root):
            self.assertEqual(main(['--state',str(self.root),'revoke-strategy']),0)
        self.assertTrue(self.j.setting('runtime_revoked'))

    def test_resume_works_while_running_without_reviving_authorization(self):
        (self.root/'STOP').touch()
        self.j.set_setting('runtime_revoked',True)
        with process_lock(self.root):
            self.assertEqual(main(['--state',str(self.root),'resume']),0)
        self.assertFalse((self.root/'STOP').exists())
        self.assertTrue(self.j.setting('runtime_revoked'))


if __name__ == '__main__':
    unittest.main()
