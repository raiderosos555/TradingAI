import unittest
from timeline import Timeline,QuoteQueue,Unverified
from model import ClockSegment

def tick(ms,last=100,bid=99.9,ask=100.1,flags=14):return dict(time_msc=ms,last=last,bid=bid,ask=ask,flags=flags)

class TimelineTests(unittest.TestCase):
    def test_forming_bar_hidden_and_boundary_tick_in_next_bar(self):
        t=Timeline({'H1':[(0,100),(100,200)]});t.feed(tick(1,last=100));t.feed(tick(99,last=101))
        self.assertEqual(t.snapshot('H1'),[])
        event=t.feed(tick(100,last=999))[0]
        self.assertEqual(event['ohlc']['high'],101);self.assertEqual(len(t.snapshot('H1')),1)
        self.assertEqual(t.current['H1']['open'],999)
    def test_future_changes_cannot_mutate_saved_snapshot(self):
        t=Timeline({'H1':[(0,100),(100,200)]});t.feed(tick(1));t.feed(tick(100));past=t.snapshot('H1')
        t.feed(tick(199,last=999));t.advance(200)
        self.assertEqual(len(past),1);self.assertEqual(past[0]['ohlc']['high'],100)
        past[0]['ohlc']['high']=1;self.assertEqual(t.snapshot('H1')[0]['ohlc']['high'],100)
    def test_missing_bar_not_filled_with_previous_price(self):
        t=Timeline({'H1':[(0,100),(100,200)]});t.feed(tick(1));t.advance(200)
        self.assertEqual(t.snapshot('H1')[1]['status'],'MISSING_LAST')
    def test_last_only_updates_technical_bar(self):
        t=Timeline({'H1':[(0,100)]});t.feed(tick(1));t.feed(tick(2,last=999,flags=6));t.advance(100)
        self.assertEqual(t.snapshot('H1')[0]['ohlc']['tick_volume'],1)
    def test_equal_timestamp_last_updates_preserved(self):
        t=Timeline({'H1':[(0,100)]});t.feed(tick(1,last=101));t.feed(tick(1,last=102));t.advance(100)
        self.assertEqual(t.snapshot('H1')[0]['ohlc']['close'],102)
    def test_clock_regression_rejected(self):
        t=Timeline({'H1':[(0,100)]});t.feed(tick(2))
        with self.assertRaises(ValueError):t.feed(tick(1))
    def test_utc_adapter_rejects_unverified_mapping(self):
        t=Timeline({'H1':[(0,100)]});t.feed(tick(1));t.advance(100)
        with self.assertRaises(Unverified):t.utc_market('TEST',{},'H1',1,[],1000)
    def test_utc_adapter_rejects_stale_quote_after_timer_close(self):
        t=Timeline({'H1':[(0,100)]});t.feed(tick(1));t.advance(100)
        mapping=[ClockSegment(0,1000,0,'SYNTHETIC',True)]
        with self.assertRaisesRegex(Unverified,'Stale'):t.utc_market('TEST',{},'H1',1,mapping,10)
    def test_utc_adapter_closed_bars_only_with_explicit_test_clock(self):
        t=Timeline({'H1':[(0,3600000),(3600000,7200000)]});t.feed(tick(1));t.feed(tick(3600000,last=999))
        m=t.utc_market('TEST',{},'H1',1,[ClockSegment(0,9000000,0,'SYNTHETIC',True)],10)
        self.assertEqual(m['bars'][0]['high'],100);self.assertEqual(m['tick']['last'],999)
    def test_dst_duration_cannot_silently_enter_fixed_duration_analyzer(self):
        t=Timeline({'D1':[(0,86400000)]});t.feed(tick(1));t.feed(tick(86400000))
        mapping=[ClockSegment(0,43200000,0,'SYNTHETIC',True),ClockSegment(43200000,90000000,3600000,'SYNTHETIC',True)]
        with self.assertRaisesRegex(Unverified,'duration incompatible'):t.utc_market('TEST',{},'D1',1,mapping,10)
    def test_same_decision_tick_never_candidate(self):
        q=QuoteQueue();q.feed(tick(100));q.submit('a','BUY','OPEN',100,1,100,.5)
        self.assertEqual(q.feed(tick(100)),[])
        self.assertEqual(q.feed(tick(101))[0]['price'],100.1)
    def test_delay_uses_later_price_not_decision_price(self):
        q=QuoteQueue();q.submit('a','SELL','CLOSE',100,20,100,1)
        self.assertEqual(q.feed(tick(119,ask=100.2)),[])
        r=q.feed(tick(120,bid=101,ask=101.2))[0]
        self.assertEqual(r['price'],101.2);self.assertFalse(r['orders_authorized'])
    def test_spread_failure_not_deferred_until_better_quote(self):
        q=QuoteQueue();q.submit('a','BUY','OPEN',100,1,100,.1)
        self.assertEqual(q.feed(tick(101))[0]['status'],'REJECTED_SPREAD')
        self.assertEqual(q.feed(tick(102,ask=99.95)),[])
    def test_missing_quote_expires_without_fill(self):
        q=QuoteQueue();q.submit('a','SELL','OPEN',100,1,10,1)
        self.assertEqual(q.advance(111)[0]['status'],'EXPIRED_NO_QUOTE')
        self.assertEqual(q.feed(tick(112)),[])
    def test_duplicate_intent_and_backdating_rejected(self):
        q=QuoteQueue();q.submit('a','BUY','OPEN',100,1,10,1);q.feed(tick(101))
        with self.assertRaises(ValueError):q.submit('a','BUY','OPEN',101,1,10,1)
        with self.assertRaises(ValueError):q.submit('b','BUY','OPEN',100,1,10,1)
    def test_positive_delay_required(self):
        with self.assertRaises(ValueError):QuoteQueue().submit('a','BUY','OPEN',100,0,10,1)
    def test_nonfinite_timeout_cannot_create_never_expiring_intent(self):
        with self.assertRaises(ValueError):QuoteQueue().submit('a','BUY','OPEN',100,1,float('nan'),1)
        with self.assertRaises(ValueError):QuoteQueue().advance(float('nan'))

    def test_frozen_signal_engine_does_not_read_forming_last_extreme(self):
        import sys
        from pathlib import Path
        from datetime import datetime,timezone
        snapshot=Path(__file__).resolve().parent.parent/'stage2/source_snapshot'
        sys.path.insert(0,str(snapshot))
        from trading_ai.strategy import SignalEngine
        from trading_ai.simulation import fixture,SimBroker
        start=1767225600000;hour=3600000
        timeline=Timeline({'H1':[(start+i*hour,start+(i+1)*hour) for i in range(202)]})
        for i in range(200):
            timeline.feed(tick(start+i*hour,last=100+i*.1))
            timeline.feed(tick(start+(i+1)*hour-1,last=100+i*.1+.05))
        now_ms=start+200*hour;timeline.feed(tick(now_ms,last=120,bid=120,ask=120.02))
        mapping=[ClockSegment(start,start+203*hour,0,'SYNTHETIC_TEST_ONLY',True)]
        now=datetime.fromtimestamp(now_ms/1000,timezone.utc);config,_=fixture(now)
        info=SimBroker(now).info
        class Adapter:
            def market(self,symbol,timeframe,count):return timeline.utc_market(symbol,info,timeframe,count,mapping,10000)
        engine=SignalEngine(config,Adapter());before=engine.evaluate('GOLD',now)
        timeline.feed(tick(now_ms+1000,last=999999,bid=120,ask=120.02))
        after=engine.evaluate('GOLD',datetime.fromtimestamp((now_ms+1000)/1000,timezone.utc))
        self.assertEqual(before['analysis'],after['analysis'])
        self.assertLess(after['analysis']['signal_bar']['high'],121)

if __name__=='__main__':unittest.main()
