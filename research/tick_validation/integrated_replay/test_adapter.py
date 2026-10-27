import copy
import json
import tempfile
import unittest
from pathlib import Path
from adapter import Tape,LastBars,Replay,Blocked
from controls import setup,ticks,run_control,calendar_event,START,END


class AdapterTests(unittest.TestCase):
    def case(self,aliases=('GOLD','US500'),side='SELL',**pricing):
        folder=tempfile.TemporaryDirectory();self.addCleanup(folder.cleanup)
        c,b,j=setup(folder.name,aliases,side,**pricing);self.addCleanup(j.close)
        return c,b,j

    def test_two_symbols_share_account_and_all_four_engines(self):
        result=run_control()
        self.assertEqual(len(result['metrics']['closed_trades']),2)
        self.assertAlmostEqual(result['ending_equity'],10025.12)
        self.assertAlmostEqual(result['metrics']['commission_and_fees'],.32)
        self.assertAlmostEqual(result['metrics']['max_drawdown_cash'],.32)
        self.assertEqual({d['symbol'] for d in result['ledger']},{'TEST_GOLD','TEST_US500'})
        self.assertFalse(result['positions']);self.assertFalse(result['uncertain'])
        rules=[o['payload']['rule'] for o in result['application_operations']]
        self.assertEqual(rules.count('TP1'),2);self.assertEqual(rules.count('BREAK_EVEN'),2);self.assertEqual(rules.count('TRAILING'),2)

    def test_buy_prices_and_full_output_reproducible(self):
        first=run_control(side='BUY');second=run_control(side='BUY')
        self.assertEqual(first,second)
        self.assertEqual(first['ledger'][0]['price'],100.02)
        self.assertEqual(first['ledger'][2]['price'],102.2)

    def test_latency_uses_later_event_and_durable_intent(self):
        r=run_control()
        self.assertEqual(r['ledger'][0]['time_msc'],START+50)
        self.assertEqual(r['ledger'][1]['time_msc'],START+100)
        self.assertTrue(all(x['ready_ms']>x['submitted_ms'] for x in r['requests']))

    def test_zero_quote_preserved_no_fill_at_zero_timestamp(self):
        r=run_control(events=ticks(invalid_at=(50,100)))
        self.assertEqual(len(r['invalid_quotes']),4)
        self.assertTrue(all(d['time_msc'] not in [START+50,START+100] for d in r['ledger']))
        self.assertGreaterEqual(r['ledger'][0]['time_msc'],START+150)

    def test_global_slot_limit_blocks_third_symbol(self):
        aliases=('GOLD','US500','OIL')
        r=run_control(aliases=aliases)
        self.assertEqual(len([d for d in r['ledger'] if d['entry']==0]),2)
        self.assertTrue(any('slot limit' in d.get('reason','') for d in r['decisions']))

    def test_shared_risk_budget_can_block_before_slot_limit(self):
        c,b,j=self.case();c['risk']['max_total_pct']=.1
        r=Replay(c,b,ticks(),j,START,END,10000,10000).run()
        self.assertEqual(len([d for d in r['ledger'] if d['entry']==0]),1)
        self.assertTrue(any('Total account risk' in d.get('reason','') for d in r['decisions']))

    def test_last_update_does_not_refresh_bid_ask_time(self):
        c,b,j=self.case(aliases=('GOLD',))
        b.feed(dict(kind='tick',utc_ms=START,provider_index=0,symbol='TEST_GOLD',tick=dict(bid=100,ask=100.02,last=100,flags=14)))
        b.feed(dict(kind='tick',utc_ms=START+11000,provider_index=1,symbol='TEST_GOLD',tick=dict(bid=100,ask=100.02,last=101,flags=24)))
        self.assertEqual(b.quotes['TEST_GOLD']['event_time_msc'],START+11000)
        self.assertEqual(b.quotes['TEST_GOLD']['time_msc'],START)
        with self.assertRaisesRegex(Blocked,'Stale'):b.quote_for('TEST_GOLD')

    def test_unavailable_fx_is_not_zero_cost_or_current_fx(self):
        c,b,j=self.case(aliases=('GOLD',),fx_symbol='USDPLN')
        r=Replay(c,b,ticks(('GOLD',)),j,START,END,10000,10000).run()
        self.assertFalse(r['ledger'])
        self.assertTrue(any('USDPLN' in d.get('reason','') for d in r['decisions']))

    def test_future_calendar_rejected(self):
        c,b,j=self.case();event=calendar_event();event['data']['retrieved_at_utc']+=1
        with self.assertRaisesRegex(ValueError,'future'):b.feed(event)

    def test_cross_symbol_equal_time_without_source_sequence_rejected(self):
        events=list(ticks())[:3]
        for e in events:e.pop('global_sequence',None)
        with self.assertRaisesRegex(ValueError,'Ambiguous'):
            tape=Tape(events)
            while tape.pending:tape.pop()

    def test_same_symbol_same_millisecond_keeps_invalid_before_valid(self):
        events=[dict(kind='tick',utc_ms=START,symbol='TEST_GOLD',provider_index=i,tick=dict(bid=b,ask=a,flags=6)) for i,(b,a) in enumerate([(0,0),(100,100.02)])]
        tape=Tape(events)
        self.assertEqual(tape.pop()['tick']['bid'],0)
        self.assertEqual(tape.pop()['tick']['bid'],100)

    def test_provider_sequence_gap_rejected(self):
        event=next(e for e in ticks() if e['kind']=='tick');event['provider_index']=2
        with self.assertRaisesRegex(ValueError,'provider index'):Tape([event])

    def test_last_bar_published_only_after_close_even_on_invalid_quote(self):
        c,b,j=self.case(aliases=('GOLD',));bars=b.bars['TEST_GOLD'];before=len(bars.closed)
        bars.feed(START,dict(flags=24,last=123,bid=0,ask=0))
        bars.advance(START+3599999);self.assertEqual(len(bars.closed),before)
        bars.advance(START+3600000);self.assertEqual(bars.closed[-1]['close'],123)

    def test_no_end_sample_forced_liquidation(self):
        r=run_control(events=ticks(flat=True))
        self.assertEqual(len(r['positions']),2)
        self.assertEqual(len(r['ledger']),2)
        self.assertTrue(r['no_end_of_sample_forced_fill'])

    def test_rollover_while_exposed_stops_instead_of_zero_swap(self):
        c,b,j=self.case(rollover_ms=[START+5000])
        with self.assertRaisesRegex(Blocked,'rollover'):
            Replay(c,b,ticks(),j,START,END,10000,10000).run()

    def test_missing_latency_window_causes_quarantine_not_invented_fill(self):
        c,b,j=self.case(aliases=('GOLD',))
        events=list(ticks(('GOLD',)))[:2]
        r=Replay(c,b,events,j,START,END,10000,10000).run()
        self.assertFalse(r['ledger']);self.assertTrue(r['uncertain'])

    def test_server_sl_executes_while_application_disconnected(self):
        c,b,j=self.case(aliases=('GOLD',))
        events=list(ticks(('GOLD',),flat=True))
        events.append(dict(kind='connection',utc_ms=START+5001,connected=False))
        for e in events:
            if e['kind']=='tick' and e['utc_ms']>=START+6000:e['tick'].update(bid=103.,ask=103.02,last=103.)
        events.sort(key=lambda e:e['utc_ms']) # Explicit synthetic construction only.
        r=Replay(c,b,events,j,START,END,10000,10000).run()
        self.assertEqual(r['ledger'][-1]['source'],'SERVER_SL')
        self.assertEqual(r['ledger'][-1]['price'],103.02)
        self.assertFalse(r['positions'])

    def test_unpriced_exposure_makes_drawdown_unknown(self):
        r=run_control(events=ticks(invalid_at=(5000,)))
        self.assertGreater(r['metrics']['unpriced_marks'],0)
        self.assertIsNone(r['metrics']['max_drawdown_cash'])
        self.assertIsNone(r['metrics']['net_marked'])

    def test_fx_conversion_uses_side_and_independent_quote_freshness(self):
        c,b,j=self.case(aliases=('GOLD',),fx_symbol='USDPLN')
        b.feed(dict(kind='tick',utc_ms=START,provider_index=0,symbol='USDPLN',tick=dict(bid=4.,ask=4.01,flags=6)))
        self.assertEqual(b.profit(0,'TEST_GOLD',.01,100,101),4.)
        self.assertEqual(b.profit(0,'TEST_GOLD',.01,100,99),-4.01)
        b.now=b.now.replace(second=11)
        with self.assertRaisesRegex(Blocked,'Stale'):b.profit(0,'TEST_GOLD',.01,100,101)

    def test_missing_fee_policy_blocks_without_zero_default(self):
        c,b,j=self.case(aliases=('GOLD',));del b.policies['TEST_GOLD']['commission_per_lot_side']
        r=Replay(c,b,ticks(('GOLD',)),j,START,END,10000,10000).run()
        self.assertFalse(r['ledger'])
        self.assertTrue(any('Missing explicit pricing policy' in d.get('reason','') for d in r['decisions']))

    def test_adverse_arrival_gap_is_quarantined_by_frozen_execution(self):
        aliases=('GOLD',);events=list(ticks(aliases,flat=True))
        for e in events:
            if e['kind']=='tick' and e['utc_ms']>=START+50:e['tick'].update(bid=99.,ask=99.02,last=99.)
        r=run_control(aliases=aliases,events=events)
        self.assertTrue(r['uncertain'])
        self.assertEqual(len(r['ledger']),1)
        self.assertEqual(r['ledger'][0]['price'],99.)

    def test_invalid_bar_window_and_overlapping_warmup_rejected(self):
        c,b,j=self.case(aliases=('GOLD',));warm=b.bars['TEST_GOLD'].closed
        with self.assertRaises(ValueError):LastBars(warm,[(START,START+7200000)])
        with self.assertRaises(ValueError):LastBars(warm,[(START-3600000,START)])

    def test_incomplete_report_keeps_fills_but_not_performance(self):
        c,b,j=self.case(rollover_ms=[START+5000])
        result=Replay(c,b,ticks(),j,START,END,10000,10000).run_report()
        self.assertEqual(result['status'],'INCOMPLETE')
        self.assertTrue(result['ledger'])
        self.assertTrue(all(value is None for value in result['metrics'].values()))
