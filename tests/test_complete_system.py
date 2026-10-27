import copy
import json
import math
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from trading_ai.analyzer import research
from trading_ai.backtest import replay
from trading_ai.briefings import build_briefing, scheduled_briefing
from trading_ai.broker import MT5Broker
from trading_ai.collector import Collector, MarketArchive, discover_symbols
from trading_ai.execution import ExecutionEngine
from trading_ai.indicators import ema, rsi, atr, macd
from trading_ai.journal import Journal
from trading_ai.manager import PositionManager
from trading_ai.models import Blocked, digest, envelope, validate_briefing, utcnow
from trading_ai.observer import read_observer
from trading_ai.risk import RiskManager
from trading_ai.simulation import SimBroker, fixture
from trading_ai.strategy import SignalEngine, policy_hash
from trading_ai.sync import FileTransport


def candles(now, count=260):
    rows=[]
    for k in range(count):
        close=100+math.sin(k*.7)*.5
        rows.append({"time": int(now.timestamp())-(count-k)*3600, "open": close-.03,
                     "high": close+.1, "low": close-.1, "close": close, "tick_volume": 100})
    for k in (199,229):
        if k < count:
            rows[k].update(open=100.1, high=102, low=100, close=100.2)
    return rows


class CompleteTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.b=SimBroker()
        self.c,self.brief=fixture(self.b.now)
        self.c["engine"]["enabled"] = True  # Explicitly enable only this in-memory test fixture.
        self.env=envelope(self.brief,self.brief['signals'][0])
        self.j=Journal(self.root/'state')
        self.addCleanup(self.j.close)
        self.j.set_setting('day_start',{'date':self.b.now.date().isoformat(),'equity':10000,'account':123456,'server':'SIMULATOR'})
        self.r=RiskManager(self.c,self.b,self.j,'DEMO:123456',clock=lambda:self.b.now)
        self.e=ExecutionEngine(self.r)

    def pending(self):
        s=self.env['signal'];s.update(kind='BUY_LIMIT',entry=99.5,sl=98.5,tp=102)
        s['structure']['invalidation']=98.6
        self.c['mode']='DEMO'
        self.j.approve(self.env,123456,'SIMULATOR')
        self.assertEqual(self.e.execute(self.env)['status'],'CONFIRMED')
        return self.b.orders[0]

    def amended(self):
        env=copy.deepcopy(self.env)
        env['signal'].update(id='replacement',entry=99.4,sl=98.6,tp=102.5)
        env['signal']['structure']['invalidation']=98.7
        env['signal']['valid_until']=(self.b.now+timedelta(hours=7)).isoformat()
        self.j.approve(env,123456,'SIMULATOR')
        return env

    def test_ema_seed_and_recursive_value(self):
        self.assertEqual(ema([1,2,3,4,5],3),[None,None,2,3,4])

    def test_wilder_rsi_limits_and_flat(self):
        self.assertEqual(rsi(list(range(1,31)))[-1],100)
        self.assertEqual(rsi(list(range(30,0,-1)))[-1],0)
        self.assertEqual(rsi([10]*30)[-1],50)

    def test_macd_constant_and_warmup(self):
        m=macd([10]*100)
        self.assertTrue(all(x is None for x in m['signal'][:33]))
        self.assertEqual(m['histogram'][-1],0)

    def test_atr_wilder_known_ranges(self):
        rows=[{'high':11,'low':9,'close':10}]*30
        self.assertEqual(atr(rows)[-1],2)

    def test_false_breakout_prior_level_excludes_signal_candle(self):
        rows=candles(self.b.now,200)
        market=self.b.market('TEST_GOLD','H1',200);market['bars']=rows
        f=research(market,'H1',self.b.now)
        self.assertEqual(f['false_breakout'],'UP')
        self.assertLess(f['prior_resistance'],102)
        self.assertTrue(f['consolidating'])

    def test_future_candle_is_rejected(self):
        market=self.b.market('TEST_GOLD','H1',200)
        market['bars'][-1]['time']=int(self.b.now.timestamp())
        with self.assertRaisesRegex(Blocked,'closed'):
            research(market,'H1',self.b.now)

    def setup_engine(self):
        original=self.b.market
        rows=candles(self.b.now,200)
        def market(symbol,timeframe='H1',count=20):
            m=original(symbol,timeframe,count)
            m['bars']=rows[-count:]
            return m
        self.b.market=market
        self.c['strategies'] += ['local_false_breakout_v1','local_breakout_v1']
        return SignalEngine(self.c,self.b,self.j)

    def test_engine_emits_valid_complete_plan(self):
        engine=self.setup_engine()
        item=engine.evaluate('GOLD',self.b.now)
        self.assertIsNotNone(item['signal'])
        env=item['signal']
        validate_briefing({'schema_version':'1.0','briefing_id':env['briefing_id'],'session':env['session'],
                           'generated_at':env['generated_at'],'signals':[env['signal']]})
        self.assertEqual(env['signal']['kind'],'SELL')

    def test_engine_proposal_immutable_across_quote_change(self):
        engine=self.setup_engine()
        first=engine.evaluate('GOLD',self.b.now)['signal']
        self.b.quote(100.1)
        self.assertEqual(first,engine.evaluate('GOLD',self.b.now)['signal'])

    def test_no_setup_means_no_fabricated_signal(self):
        item=SignalEngine(self.c,self.b,self.j).evaluate('GOLD',self.b.now)
        self.assertIsNone(item['signal'])

    def test_local_strategy_policy_is_required(self):
        engine=self.setup_engine()
        self.c['mode']='DEMO'
        env=engine.scan(self.b.now)[0]['signal']
        self.assertFalse(self.j.approved(env,123456,'SIMULATOR'))
        policy={'hash':policy_hash(self.c),'until':(self.b.now+timedelta(hours=1)).isoformat()}
        self.j.set_setting('strategy_policy',policy)
        env=engine.scan(self.b.now)[0]['signal']
        self.assertTrue(self.j.approved(env,123456,'SIMULATOR'))

    def test_revocation_blocks_previously_generated_entry(self):
        engine=self.setup_engine();self.c['mode']='DEMO'
        policy={'hash':policy_hash(self.c),'until':(self.b.now+timedelta(hours=1)).isoformat()}
        self.j.set_setting('strategy_policy',policy)
        env=engine.scan(self.b.now)[0]['signal']
        self.j.set_setting('strategy_policy',None)
        with self.assertRaisesRegex(Blocked,'authorization expired'):
            self.r.prepare_open(env)

    def test_archive_repeat_deduplicates_without_losing_same_ms_ticks(self):
        a=MarketArchive(self.root,123456,'SIMULATOR');self.addCleanup(a.close)
        bars=self.b.market('TEST_GOLD','H1',20)['bars']
        a.save_bars('TEST_GOLD','H1',bars);a.save_bars('TEST_GOLD','H1',bars)
        self.assertEqual(len(a.bars('TEST_GOLD','H1')),20)
        ticks=[{'time_msc':1,'bid':100,'ask':101}]*2
        a.save_ticks('TEST_GOLD',ticks);a.save_ticks('TEST_GOLD',ticks)
        self.assertEqual(a.db.execute('SELECT count(*) FROM ticks').fetchone()[0],2)

    def test_archive_account_isolation(self):
        a=MarketArchive(self.root,999,'OTHER');self.addCleanup(a.close)
        with self.assertRaisesRegex(Blocked,'mismatch'):
            a.save_snapshot(self.b.snapshot())

    def test_archive_clock_namespace_isolation(self):
        a=MarketArchive(self.root,123456,'SIMULATOR',0)
        b=MarketArchive(self.root,123456,'SIMULATOR',7200)
        self.addCleanup(a.close);self.addCleanup(b.close)
        a.save_bars('X','H1',[{'time':1}])
        self.assertFalse(b.bars('X','H1'))

    def test_collector_records_missing_ticks_not_fake_success(self):
        a=MarketArchive(self.root,123456,'SIMULATOR');self.addCleanup(a.close)
        results=Collector(self.c,self.b,a).collect(self.b.now)
        self.assertEqual(sum(x.get('bars',0) for x in results),1400)
        self.assertTrue(any(x['status']=='UNAVAILABLE' for x in results))

    def test_symbol_candidates_are_actual_inventory_names(self):
        result=discover_symbols([{'name':'US500.actual','description':'US500','path':'Index','trade_mode':4}])
        self.assertEqual(result['US500']['candidates'][0]['name'],'US500.actual')
        self.assertFalse(result['OIL']['candidates'])

    def test_full_pending_amendment_adopts_new_plan(self):
        target=self.pending();env=self.amended()
        result=self.e.execute(env,'AMEND_PENDING',target['ticket'],old_env=self.env)
        self.assertEqual(result['status'],'CONFIRMED')
        self.assertEqual(target['price_open'],99.4)
        self.assertEqual(target['sl'],98.6)
        effective=self.j.effective_operation(self.j.operation('open:'+self.env['signal']['id']))
        self.assertEqual(effective['payload']['envelope'],env)
        self.assertEqual(self.j.root_id(env),self.env['signal']['id'])
        with self.assertRaisesRegex(Blocked,'already used'):
            self.e.execute(env)

    def test_amendment_cannot_reuse_original_id(self):
        target=self.pending()
        with self.assertRaisesRegex(Blocked,'new independently'):
            self.e.execute(self.env,'AMEND_PENDING',target['ticket'],old_env=self.env)

    def test_amendment_requires_new_approval(self):
        target=self.pending();env=copy.deepcopy(self.env);env['signal']['id']='not-approved'
        with self.assertRaisesRegex(Blocked,'approval'):
            self.e.execute(env,'AMEND_PENDING',target['ticket'],old_env=self.env)

    def test_amendment_cannot_increase_risk_beyond_budget(self):
        target=self.pending();env=self.amended()
        env['signal'].update(id='more-risk',sl=80,tp=150)
        self.j.approve(env,123456,'SIMULATOR')
        with self.assertRaisesRegex(Blocked,'risk budget'):
            self.e.execute(env,'AMEND_PENDING',target['ticket'],old_env=self.env)

    def test_amendment_cannot_change_side(self):
        target=self.pending();env=self.amended()
        s=env['signal'];s.update(id='changed-side',kind='SELL_LIMIT',entry=101,sl=102,tp=98)
        s['structure']['invalidation']=101.5;s['management']['tp1']=100
        self.j.approve(env,123456,'SIMULATOR')
        with self.assertRaisesRegex(Blocked,'cannot change'):
            self.e.execute(env,'AMEND_PENDING',target['ticket'],old_env=self.env)

    def test_operator_cancel_valid_pending(self):
        p=self.pending()
        self.assertEqual(self.e.execute(self.env,'OPERATOR_CANCEL',p['ticket'],operation_id='cancel-1')['status'],'CONFIRMED')
        self.assertFalse(self.b.orders)

    def test_operator_partial_close_preserves_lot_step(self):
        self.c['mode']='DEMO';self.j.approve(self.env,123456,'SIMULATOR');self.e.execute(self.env)
        p=self.b.positions[0]
        with self.assertRaisesRegex(Blocked,'volume invalid'):
            self.e.execute(self.env,'OPERATOR_CLOSE',p['ticket'],close_volume=.015,operation_id='bad')
        self.assertEqual(self.e.execute(self.env,'OPERATOR_CLOSE',p['ticket'],close_volume=.1,operation_id='good')['status'],'CONFIRMED')
        self.assertAlmostEqual(p['volume'],.13)

    def test_observer_rejects_path_escape(self):
        folder=self.root/'MQL5'/'Files'/'TradingAI';folder.mkdir(parents=True)
        data={'schema_version':'1.0','read_only':True,'account_login':123456,'account_server':'SIMULATOR',
              'utc_time':self.b.now.timestamp(),'screenshot':'../../../outside.png'}
        (folder/'observer_1.json').write_text(json.dumps(data))
        result=read_observer(self.root,123456,'SIMULATOR',now=self.b.now)
        self.assertIn('escapes',result[0]['reason'])

    def test_observer_rejects_stale(self):
        folder=self.root/'MQL5'/'Files'/'TradingAI';folder.mkdir(parents=True)
        data={'schema_version':'1.0','read_only':True,'account_login':123456,'account_server':'SIMULATOR','utc_time':0}
        (folder/'observer_1.json').write_text(json.dumps(data))
        self.assertIn('stale',read_observer(self.root,123456,'SIMULATOR',now=self.b.now)[0]['reason'])

    def test_broker_clock_conversion_and_expiry_are_symmetric(self):
        broker=object.__new__(MT5Broker);broker.time_offset=7200
        d=broker.normalize({'time':10000,'time_msc':10000000,'time_expiration':11000,'sl':20})
        self.assertEqual(d['time'],2800);self.assertEqual(d['time_msc'],2800000)
        self.assertEqual(d['broker_raw_time'],10000)
        self.assertEqual(broker.broker_request({'expiration':3800})['expiration'],11000)
        self.assertEqual(broker.normalize({'time_expiration':0})['time_expiration'],0)

    def test_morning_report_includes_indicators_and_proposals(self):
        engine=self.setup_engine();scan=engine.scan(self.b.now)
        r,md=build_briefing(self.c,self.b,self.j,scan,'morning')
        self.assertTrue(r['proposals']);self.assertIn('MACD',md);self.assertIn('R:R',md)

    def test_scheduled_briefing_once_per_local_session(self):
        now=self.b.now.replace(hour=19,minute=0)
        transport=FileTransport(self.root/'exchange')
        first=scheduled_briefing(self.c,self.b,self.j,transport,[],now)
        self.assertIsNotNone(first)
        self.assertIsNone(scheduled_briefing(self.c,self.b,self.j,transport,[],now))
        self.assertTrue((transport.root/'outbox'/'latest-evening.json').exists())

    def test_backtest_explicit_costs_and_trade_generation(self):
        self.c['strategies'] += ['local_false_breakout_v1','local_breakout_v1']
        rows=candles(self.b.now,260)
        contract={**self.b.info,'cash_per_price_unit_per_lot':100}
        costs={'spread_points':2,'slippage_points':1,'commission_per_lot_roundtrip':2,'swap_per_lot_per_day':-1}
        result=replay(self.c,'GOLD',rows,contract,costs)
        self.assertTrue(result['simulation']);self.assertTrue(result['trades'])
        self.assertEqual(result['costs'],costs)
        self.assertAlmostEqual(result['net'],sum(t['net'] for t in result['trades']))

    def test_backtest_requires_historical_contract_and_costs(self):
        with self.assertRaises(Blocked):
            replay(self.c,'GOLD',candles(self.b.now),{}, {})

    def test_backtest_market_gap_skips_stale_setup_without_aborting(self):
        self.c['engine']={'enable_breakout':False,'enable_false_breakout':False}
        rows=candles(self.b.now,260)
        for row in rows[210:]: row['time']+=2*86400
        costs={'spread_points':2,'slippage_points':1,'commission_per_lot_roundtrip':2,'swap_per_lot_per_day':-1}
        result=replay(self.c,'GOLD',rows,{**self.b.info,'cash_per_price_unit_per_lot':100},costs)
        self.assertTrue(any('Stale' in x['reason'] for x in result['skipped_setups']))

    def test_explicit_partial_adoption_uses_actual_volume(self):
        self.c['mode']='DEMO';self.j.approve(self.env,123456,'SIMULATOR')
        self.b.send_code=10010
        self.assertEqual(self.e.execute(self.env)['status'],'UNCERTAIN')
        self.b.positions[0]['volume']=.1;self.b.deals[0]['volume']=.1
        result=self.e.accept_partial('open:'+self.env['signal']['id'],'Confirmed broker residual order absent')
        self.assertEqual(result['accepted_volume'],.1)
        op=self.j.effective_operation(self.j.operation('open:'+self.env['signal']['id']))
        self.assertEqual(op['payload']['request']['volume'],.1)
        self.assertFalse(self.j.uncertain());self.assertEqual(len(self.b.sent),1)

    def test_partial_adoption_rejects_residual_order(self):
        self.c['mode']='DEMO';self.j.approve(self.env,123456,'SIMULATOR');self.b.send_code=10010
        self.e.execute(self.env)
        self.b.orders.append({'ticket':self.b.next_ticket})
        with self.assertRaisesRegex(Blocked,'Residual'):
            self.e.accept_partial('open:'+self.env['signal']['id'],'test')

    def test_lost_send_response_recovered_by_unique_broker_evidence(self):
        self.c['mode']='DEMO';self.j.approve(self.env,123456,'SIMULATOR')
        real_send=self.b.send
        history_rows=self.b.history
        def send(request):
            result=real_send(request)
            history_rows[-1].update(magic=request['magic'],symbol=request['symbol'],comment=request['comment'],type=request['type'])
            raise TimeoutError('Response lost AFTER broker execution')
        self.b.send=send
        with self.assertRaises(Blocked): self.e.execute(self.env)
        self.b.history=lambda start,end:{'orders':history_rows,'deals':self.b.deals}
        self.b.order_history=lambda ticket:[o for o in history_rows if o['ticket']==ticket]
        self.assertEqual(self.e.reconcile()[0]['status'],'CONFIRMED')
        self.assertEqual(len(self.b.sent),1)

    def activate_pending(self, bad_fill=False):
        order=self.pending()
        self.b.orders.clear()
        pid=order['ticket']
        price=order['price_open']+(1 if bad_fill else 0)
        self.b.history.append({**order,'position_id':pid,'state':4})
        self.b.positions.append({**order,'identifier':pid,'type':0,'volume':order['volume_current'],
                                 'price_open':price,'profit':0,'swap':0})
        self.b.deals.append({'ticket':pid+10000,'order':pid,'position_id':pid,'entry':0,'type':0,
                            'magic':order['magic'],'symbol':order['symbol'],'volume':order['volume_current'],'price':price})

    def test_pending_gap_quarantined_before_management(self):
        self.activate_pending(bad_fill=True)
        self.assertEqual(self.e.reconcile()[0]['status'],'UNCERTAIN')
        PositionManager(self.e).run()
        self.assertEqual(len(self.b.sent),1)
        self.assertTrue(self.j.uncertain())

    def test_pending_fill_audited_once_before_later_sl_changes(self):
        self.activate_pending()
        self.assertEqual(self.e.reconcile()[0]['status'],'CONFIRMED')
        self.b.positions[0]['sl']=99.6
        self.assertEqual(self.e.reconcile(),[])
        self.assertFalse(self.j.uncertain())

    def test_pending_partial_with_residual_quarantines(self):
        self.pending()
        self.b.orders[0]['volume_current']/=2
        self.assertEqual(self.e.reconcile()[0]['status'],'UNCERTAIN')
        self.assertTrue(self.j.uncertain())

    def test_briefing_carries_persisted_management_reason(self):
        self.j.event('management_decision', {'signal_id':'previous','rule':'TRAILING','status':'HELD','reason':'Verified audit reason'})
        result,md=build_briefing(self.c,self.b,self.j,[],'evening')
        self.assertIn('Verified audit reason',md)
        self.assertTrue(result['decisions'])


if __name__=='__main__': unittest.main()
