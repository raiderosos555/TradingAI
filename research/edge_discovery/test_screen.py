import unittest
import numpy as np
from screen import features, direction, events, quote, tick_markout, stats
from protocol import FAMILIES

def bars(n=220):
    return [dict(broker_raw_time=1790035200+i*3600,open=100+i*.1,high=101+i*.1,
                 low=99+i*.1,close=100.5+i*.1) for i in range(n)]

class ScreeningTests(unittest.TestCase):
    def test_no_future_in_signal_or_atr(self):
        b=bars();f=features(b);all_f={s:f for s in ['GOLD','US100','US500','EURUSD','GBPUSD']}
        expected=[direction(f,150,k,'US500',all_f) for k in FAMILIES]
        for v in b[151:]:
            for k in ['open','high','low','close']:v[k]+=1000
        g=features(b);all_g={s:g for s in all_f}
        self.assertEqual(expected,[direction(g,150,k,'US500',all_g) for k in FAMILIES])
        self.assertEqual(f['atr'][150],g['atr'][150])

    def test_missing_bars_and_day_boundary_no_fake_fill(self):
        b=bars();b.pop(170);f=features(b)
        rows,_=events('GOLD',f,{'GOLD':f},.2)
        for r in rows:
            self.assertEqual(r['raw_exit']-r['raw_entry'],14400)
            self.assertEqual(r['raw_entry']//86400,r['raw_exit']//86400)
        for family in FAMILIES:
            rr=[r for r in rows if r['family']==family]
            for a,z in zip(rr,rr[1:]):self.assertGreaterEqual(z['raw_entry'],a['raw_exit'])

    def test_first_executable_snapshot_after_delay(self):
        a=np.array([[1000,100,101,100,6],[1250,0,0,100,8],[1500,101,102,101,6]],float)
        self.assertEqual(quote(a,np.array([True,False,True]),1000),2)
        self.assertIsNone(quote(a,np.array([True,False,False]),1000))

    def test_buy_ask_to_bid_sell_bid_to_ask(self):
        a=np.array([[1250,100,102,101,6],[2250,110,112,111,6]],float)
        row=dict(direction=1,raw_entry=1,raw_exit=2,atr=2,gross=999,after_hurdle=999,spread_hurdle=999,stress=999)
        buy=tick_markout(a,np.ones(2,bool),row,.01)
        sell=tick_markout(a,np.ones(2,bool),dict(row,direction=-1),.01)
        self.assertEqual(buy['after_hurdle'],4)
        self.assertEqual(sell['after_hurdle'],-6)
        self.assertEqual(buy['spread_hurdle'],1)
        self.assertIsNone(buy['net_cash_verified'])

    def test_ordered_source_required(self):
        b=bars();b[21],b[22]=b[22],b[21]
        with self.assertRaises(ValueError):features(b)

    def test_drawdown_includes_initial_zero(self):
        rr=[dict(raw_exit=i,alias='X',day='x',after_hurdle=v,gross=v,stress=v,spread_hurdle=0) for i,v in enumerate([-1,-2,1])]
        self.assertEqual(stats(rr)['dd'],3)

if __name__=='__main__':unittest.main()
