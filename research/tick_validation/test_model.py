import unittest,math
from datetime import datetime,timezone
from model import *

def tick(t=1000,bid=99,ask=101,last=100):return {'time_msc':t,'bid':bid,'ask':ask,'last':last,'flags':8}

class Prices(unittest.TestCase):
 def test_four_execution_sides(self):
  t=tick();self.assertEqual([execution_price(s,a,t) for s,a in [('BUY','OPEN'),('BUY','CLOSE'),('SELL','OPEN'),('SELL','CLOSE')]],[101,99,99,101])
 def test_last_never_execution_price(self):self.assertEqual(execution_price('BUY','OPEN',tick(last=10000)),101)
 def test_dynamic_spread(self):self.assertEqual(execution_price('SELL','CLOSE',tick(2000,99,104)),104)
 def test_crossed_and_nonfinite_rejected(self):
  for t in (tick(bid=102),tick(ask=float('nan')),tick(bid=0)):
   with self.assertRaises(Unverified):validate_quote(t)
 def test_provider_tie_order_preserved(self):self.assertEqual([t['last'] for _,t in validate_stream([tick(last=2),tick(last=1)])],[2,1])
 def test_unsorted_rejected(self):
  with self.assertRaises(Unverified):list(validate_stream([tick(2),tick(1)]))
 def test_decision_before_quote(self):self.assertEqual(first_executable_quote([tick(1000),tick(1001,98,103)],1000)[1]['ask'],103)
 def test_no_synthetic_quote(self):
  with self.assertRaises(Unverified):first_executable_quote([],1000)
 def test_gap_blocks_fill(self):
  with self.assertRaises(Unverified):first_executable_quote([tick(20000)],1000,max_wait_ms=1000)
 def test_spread_reject_does_not_cherry_pick_later_quote(self):
  with self.assertRaises(Unverified):first_executable_quote([tick(1001,90,110),tick(1002,99,100)],1000,max_spread=2)
 def test_buy_sl_gap_uses_available_bid(self):
  t=tick(bid=94,ask=96);self.assertEqual(protective_trigger('BUY',95,110,t),'SL');self.assertEqual(execution_price('BUY','CLOSE',t),94)
 def test_sell_sl_uses_ask(self):self.assertEqual(protective_trigger('SELL',105,90,tick(bid=104,ask=106)),'SL')
 def test_buy_tp_uses_bid_not_last(self):self.assertIsNone(protective_trigger('BUY',95,105,tick(last=110)))
 def test_sell_tp_uses_ask(self):self.assertEqual(protective_trigger('SELL',105,95,tick(bid=92,ask=94)),'TP')
 def test_spread_is_actual_cost_not_twice_charged(self):self.assertEqual(cash_result('BUY',101,99,1,10,3,0),-23)
 def test_missing_cash_inputs_block_pnl(self):
  with self.assertRaises(Unverified):cash_result('BUY',101,99,1,None,0,0)
 def test_contract_volume_and_price(self):
  c={'valid_from_raw_ms':0,'valid_until_raw_ms':2000,'evidence_id':'TEST_ONLY','volume_min':.01,'volume_max':1,'volume_step':.01,'tick_size':.1}
  validate_contract(.02,[100.1],c,1000)
  for vol,levels,at in [(.015,[100.1],1000),(.001,[100.1],1000),(.02,[100.15],1000),(.02,[100.1],2000)]:
   with self.assertRaises(Unverified):validate_contract(vol,levels,c,at)
 def test_ohlc_half_open_and_last_flags(self):
  ts=[tick(0,last=100),tick(1,last=105),tick(2,last=1000)];self.assertEqual(ohlc(ts,'last',0,2)['high'],105)
  ts[1]['flags']=2;self.assertEqual(ohlc(ts,'last',0,2)['high'],100)
 def test_missing_last_not_replaced_by_bid(self):self.assertIsNone(ohlc([tick(last=0)],'last',0,2000))

class Time(unittest.TestCase):
 def test_unknown_or_unverified_time_blocks(self):
  for segments in ([],[ClockSegment(0,10000,0,'TEST',False)]):
   with self.assertRaises(Unverified):to_utc(1000,segments)
 def test_bounded_mapping_no_extrapolation(self):
  s=[ClockSegment(0,10000,7200000,'TEST_ONLY',True)];self.assertEqual(to_utc(7201000,s),1000)
  with self.assertRaises(Unverified):to_utc(7210000,s)
 def test_fall_back_raw_time_ambiguous(self):
  s=[ClockSegment(0,10000,20000,'TEST',True),ClockSegment(10000,20000,10000,'TEST',True)]
  with self.assertRaises(Unverified):to_utc(25000,s)
 def test_d1_spring_23_hours(self):
  a,b=bar_interval(datetime(2026,3,29),'D1','Europe/Warsaw');self.assertEqual((b-a)/3600000,23)
 def test_d1_autumn_25_hours(self):
  a,b=bar_interval(datetime(2025,10,26),'D1','Europe/Warsaw');self.assertEqual((b-a)/3600000,25)
 def test_h4_spring_3_hours(self):
  a,b=bar_interval(datetime(2026,3,29),'H4','Europe/Warsaw');self.assertEqual((b-a)/3600000,3)
 def test_h4_autumn_5_hours(self):
  a,b=bar_interval(datetime(2025,10,26),'H4','Europe/Warsaw');self.assertEqual((b-a)/3600000,5)
 def test_nonexistent_h1_rejected(self):
  with self.assertRaises(Unverified):bar_interval(datetime(2026,3,29,2),'H1','Europe/Warsaw')
 def test_ambiguous_h1_requires_fold(self):
  with self.assertRaises(Unverified):local_boundary(datetime(2025,10,26,2),'Europe/Warsaw')
  a=local_boundary(datetime(2025,10,26,2),'Europe/Warsaw',0);b=local_boundary(datetime(2025,10,26,2),'Europe/Warsaw',1);self.assertEqual((b-a).total_seconds(),3600)
 def test_missing_broker_session_policy(self):
  with self.assertRaises(Unverified):bar_interval(datetime(2026,10,22),'D1',None)
 def test_ordinary_h1_and_midnight(self):
  a,b=bar_interval(datetime(2026,10,22,23),'H1','Europe/Warsaw');self.assertEqual(b-a,3600000)
  self.assertEqual(datetime.fromtimestamp(b/1000,timezone.utc).hour,22)

if __name__=='__main__':unittest.main()
