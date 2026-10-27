import copy
import unittest
from datetime import datetime, timezone

from trading_ai.backtest import replay
from trading_ai.models import Blocked
from trading_ai.research_validation import segments, win_interval
from trading_ai.simulation import SimBroker, fixture
from test_complete_system import candles


class ResearchTests(unittest.TestCase):
    def setUp(self):
        self.b = SimBroker(datetime(2026,10,23,tzinfo=timezone.utc))
        self.c,_ = fixture(self.b.now)
        self.c['strategies'] += ['local_breakout_v1','local_false_breakout_v1']
        self.bars = candles(self.b.now,320)
        self.contract = {**self.b.info,'cash_per_price_unit_per_lot':100}
        self.costs = {'spread_points':2,'slippage_points':1,'commission_per_lot_roundtrip':2,'swap_per_lot_per_day':-1}

    def test_validation_warmup_never_becomes_trading_period(self):
        split = self.bars[210]['time']
        dev,val = segments(self.bars,split,200)
        self.assertLess(dev[1][-1]['time'],split)
        self.assertEqual(val[1][200]['time'],split)

    def test_wilson_interval_handles_zero_and_all_wins(self):
        self.assertIsNone(win_interval(0,0))
        self.assertLess(win_interval(0,10)[1],.3)
        self.assertGreater(win_interval(10,10)[0],.7)

    def test_replay_honors_minimum_lot_cap_and_configured_equity(self):
        self.c['symbols']['GOLD']['max_volume'] = .01
        r = replay(self.c,'GOLD',self.bars,self.contract,self.costs,50000)
        self.assertTrue(r['trades'])
        self.assertTrue(all(t['volume']==.01 for t in r['trades']))
        self.assertEqual(r['initial_equity'],50000)
        self.assertAlmostEqual(r['net'],sum(t['net'] for t in r['trades']))

    def test_spread_and_atr_gates_are_applied_to_replay(self):
        r = replay(self.c,'GOLD',self.bars,self.contract,{**self.costs,'spread_points':100})
        self.assertFalse(r['trades'])
        self.assertTrue(any('Spread' in x['reason'] for x in r['skipped_setups']))
        self.c['symbols']['GOLD']['max_spread_atr_ratio'] = .0001
        r = replay(self.c,'GOLD',self.bars,self.contract,self.costs)
        self.assertFalse(r['trades'])

    def test_future_price_changes_do_not_change_preceding_closed_trades(self):
        a = replay(self.c,'GOLD',self.bars,self.contract,self.costs)
        changed = copy.deepcopy(self.bars)
        for row in changed[285:]:
            for key in ('open','high','low','close'):row[key] *= 1.5
        b = replay(self.c,'GOLD',changed,self.contract,self.costs)
        cut = datetime.fromtimestamp(self.bars[285]['time'],timezone.utc).isoformat()
        self.assertEqual([t for t in a['trades'] if t['closed']<cut], [t for t in b['trades'] if t['closed']<cut])


if __name__ == '__main__':
    unittest.main()
