import unittest
import numpy as np
import alternative_experiments as A

class Checks(unittest.TestCase):
    def test_clock_lag_and_no_future(self):
        t=np.arange(100)*86400.;v=np.arange(100)+10.
        ix={'VIX':np.column_stack([t,v])}
        # +3h is an explicit uncertainty margin; boundary inclusive.
        g=A.feature_at(ix,'VIX','V',t[90]+3*86400+3*3600,3)
        self.assertEqual(g[1],t[90])
        ix['VIX'][91:,1]=99999
        self.assertEqual(g,A.feature_at(ix,'VIX','V',t[90]+3*86400+3*3600,3))
    def test_stale_not_cash(self):
        ix={'VIX':np.column_stack([np.arange(80)*86400.,np.ones(80)])}
        self.assertIsNone(A.feature_at(ix,'VIX','V',100*86400,3))
    def test_term_dates_must_match(self):
        a=np.column_stack([np.arange(80)*86400.,np.ones(80)])
        ix={'VIX9D':a,'VIX':a[a[:,0]!=70*86400]}
        self.assertIsNone(A.feature_at(ix,'VIX9D','T',73*86400+3*3600,3))
    def test_filter_arithmetic(self):
        n=400;c=100+np.arange(n)*.1
        a=dict(t=A.E.epoch('2026-01-01')+np.arange(n)*86400,open=c,close=c,high=c+1,low=c-1)
        f=A.E.features(a)
        ix={'VIX':np.column_stack([a['t'],np.arange(n)+10.])}
        rows,_=A.rows_for(a,f,ix,'V','VIX',.1,3)
        self.assertTrue(rows)
        for r in rows:
            self.assertEqual(r['net'],0);self.assertEqual(r['stress'],0)
            self.assertAlmostEqual(r['delta'],-r['base'])
            self.assertGreaterEqual(r['index_age'],3.125)
    def test_trial_count(self):self.assertEqual(len(A.DEFS),6)
if __name__=='__main__':unittest.main()
