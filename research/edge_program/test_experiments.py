"""Synthetic fixtures ONLY for implementation checks, never research P&L."""
import unittest
from unittest.mock import patch
import numpy as np
import experiments as E
import protocol as P

def bars(n=400):
    c=100+np.arange(n)*.03+np.sin(np.arange(n)/3)
    return dict(t=E.epoch('2026-02-01')+np.arange(n)*86400,open=c-.1,close=c,high=c+.4,low=c-.4)

class Checks(unittest.TestCase):
    def test_rsi_limits_and_wilder(self):
        a=bars();a['close']=np.arange(1,401,dtype=float)
        f=E.features(a);np.testing.assert_allclose(f['rsi_value'][80:],100)
        a['close']=np.arange(400,0,-1,dtype=float)
        np.testing.assert_allclose(E.features(a)['rsi_value'][80:],0)
        np.testing.assert_allclose(E.ewma(np.array([1.,2.,3.,7.]),3,1/3)[2:],[2,11/3])

    def test_causal_prefix(self):
        a=bars();f=E.features(a);g=E.features({k:v[:230] for k,v in a.items()})
        for k in f:np.testing.assert_allclose(f[k][:230],g[k],equal_nan=True)

    def test_bollinger_identity(self):
        c=bars()['close'];f=E.features(bars())
        for i in range(20,len(c)):
            past=c[i-20:i];mu=past.mean();sd=past.std(ddof=1)
            self.assertEqual(f['z_value'][i]>2,c[i]>mu+2*sd)
            self.assertEqual(f['z_value'][i]<-2,c[i]<mu-2*sd)

    def test_flat_cash_cost_and_split(self):
        a=bars();f=E.features(a);f['RSI'][:]=0;f['Z'][:]=0
        a['t']=E.epoch('2026-05-01')+np.arange(400)*14400
        rows,_=E.windows(a,f,'R','RSI',.1)
        self.assertTrue(rows)
        for r in rows:
            self.assertEqual(r['net'],0);self.assertEqual(r['stress'],0)
            self.assertLess(r['signal_raw'],r['entry_raw']);self.assertLess(r['entry_raw'],r['exit_raw'])
        a['t']=E.epoch('2026-07-01')+np.arange(400)*14400
        rows,_=E.windows(a,f,'R','RSI',.1)
        self.assertTrue(rows)
        for r in rows:self.assertFalse(r['signal_raw']<E.epoch(P.SPLIT)<=r['exit_raw'])

    def test_gap_excluded(self):
        a=bars();a['t']=E.epoch('2026-04-01')+np.arange(400)*18000
        rows,counts=E.windows(a,E.features(a),'R','RSI',.1)
        self.assertFalse(rows);self.assertGreater(counts['gap'],0)

    def test_paired_null_and_multiplicity(self):
        a=bars();f=E.features(a);f['SMA']=f['ROC'].copy()
        rows,_=E.windows(a,f,'T','SMA',.1);self.assertTrue(rows)
        s=E.summary(rows);self.assertAlmostEqual(s['delta'],0);self.assertEqual(s['p_delta'],1)
        np.testing.assert_allclose(E.holm([.01,.04,.03]),[.03,.06,.06])
        self.assertEqual(len(E.definitions()),36)

if __name__=='__main__':unittest.main()
