import copy
import unittest
from unittest.mock import patch
from trading_ai.models import Blocked
from trading_ai.portfolio_research import replay_portfolio,features,proposal
from trading_ai.simulation import fixture,SimBroker
from test_complete_system import candles

class PortfolioTests(unittest.TestCase):
 def setUp(self):
  self.b=SimBroker();self.c,_=fixture(self.b.now)
  spec=self.c['symbols']['GOLD'];spec.update(max_volume=.01,max_spread_points=100,max_spread_atr_ratio=1)
  self.c['symbols']={a:copy.deepcopy(spec) for a in ['A','B','C']}
  bars=candles(self.b.now,300)
  self.data={a:{'bars':copy.deepcopy(bars),'contract':{**self.b.info,'cash_per_price_unit_per_lot':100}} for a in self.c['symbols']}
  self.start=bars[201]['time'];self.end=bars[-1]['time']+3600
 def run_replay(self,data=None):return replay_portfolio(self.c,data or self.data,'trend_breakout',self.start,self.end,10000)
 def test_shared_slots_risk_and_cash_accounting(self):
  with patch('trading_ai.portfolio_research.proposal',return_value={'side':1,'atr':.3}):r=self.run_replay()
  self.assertEqual(r['max_positions_observed'],2)
  self.assertGreater(r['rejected']['slots'],0)
  self.assertLessEqual(r['max_reserved_pct'],self.c['risk']['max_total_pct'])
  self.assertAlmostEqual(r['net'],sum(t['net'] for t in r['trades']))
 def test_risk_cannot_force_minimum_lot(self):
  self.c['risk']['max_trade_pct']=.000001
  with patch('trading_ai.portfolio_research.proposal',return_value={'side':1,'atr':10}):r=self.run_replay()
  self.assertFalse(r['trades'])
 def test_future_candle_values_do_not_change_current_signal(self):
  bars=self.data['A']['bars'];a=proposal(bars,features(bars),230,'trend_pullback')
  changed=copy.deepcopy(bars)
  for b in changed[230:]:
   for k in ('open','high','low','close'):b[k]*=2
  self.assertEqual(a,proposal(changed,features(changed),230,'trend_pullback'))
 def test_sl_before_tp_same_bar(self):
  self.c['symbols']={'A':self.c['symbols']['A']}
  data={'A':self.data['A']}
  data['A']['bars'][201].update(open=100,high=105,low=95,close=100)
  with patch('trading_ai.portfolio_research.proposal',return_value={'side':1,'atr':.3}):r=self.run_replay(data)
  self.assertEqual(r['trades'][0]['reason'],'SL')
  self.assertLess(r['trades'][0]['net'],0)
 def test_invalid_data_and_unknown_variant_rejected(self):
  with self.assertRaises(Blocked):replay_portfolio(self.c,self.data,'unknown',self.start,self.end)
  self.data['A']['bars'][220]['high']=0
  with self.assertRaises(Blocked):self.run_replay()
