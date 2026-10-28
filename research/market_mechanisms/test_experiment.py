"""Artificial fixtures test arithmetic/causality ONLY; never reported as market returns."""
import unittest
import numpy as np
import experiment as E
import protocol as P


def bars(n=400,step=3600):
    t=E.epoch('2026-05-04')+np.arange(n)*step
    c=100+np.arange(n)*.01+np.sin(np.arange(n)/3)
    return dict(t=t,open=c-.03,close=c,high=c+.2,low=c-.2)


class Checks(unittest.TestCase):
    def test_prefix_causality_all_mechanisms(self):
        a=bars();b=bars();b['close']=b['close']*.8+np.cos(np.arange(400))*.1
        for m in ('M1','M2','M3','M4'):
            full=E.features(a,m,b)
            short=E.features({k:v[:250] for k,v in a.items()},m,{k:v[:250] for k,v in b.items()})
            for x,y in zip(full,short): np.testing.assert_allclose(x[:250],y)

    def test_pair_sign_notional(self):
        self.assertAlmostEqual(E.pair_return(.02,.01,2),0)
        self.assertAlmostEqual(E.pair_return(.01,.02,1),-.005)

    def test_holm(self):
        np.testing.assert_allclose(E.holm([.01,.04,.03]),[.03,.06,.06])

    def test_next_open_and_nonoverlap(self):
        a=bars(step=86400)
        rows,_=E.events(a,'M1','fixture',.1)
        self.assertTrue(rows)
        for r in rows:
            self.assertGreater(r['entry_raw'],r['signal_raw'])
            e=np.flatnonzero(a['t']==r['entry_raw'])[0];x=e+P.MOMENTUM_HOLD
            self.assertAlmostEqual(r['gross'],r['direction']*(a['open'][x]/a['open'][e]-1)*10000)
            self.assertLess(r['stress'],r['after_hurdle'])
        for r,s in zip(rows,rows[1:]): self.assertGreaterEqual(s['entry_raw'],r['exit_raw'])

    def test_gap_never_filled(self):
        a=bars(step=86400)
        # All daily observations separated by five days -> cannot cross any gap.
        a['t']=E.epoch('2024-08-01')+np.arange(len(a['t']))*5*86400
        rows,rejected=E.events(a,'M1','fixture',.1)
        self.assertEqual(rows,[])
        self.assertGreater(rejected['gap'],0)

    def test_alignment_exact(self):
        a=bars(10);b={k:np.delete(v,4) for k,v in a.items()}
        x,y=E.aligned(a,b)
        self.assertEqual(len(x['t']),9)
        np.testing.assert_array_equal(x['t'],y['t'])
        self.assertNotIn(a['t'][4],x['t'])

    def test_bootstrap_deterministic_and_null(self):
        rows=[dict(block=i,gross=(-1)**i,hurdle=.1,after_hurdle=(-1)**i-.1,
                   stress=(-1)**i-1,benchmark=.2,delta_benchmark=0,
                   entry_raw=E.epoch('2026-05-04')+i*86400,exit_raw=E.epoch('2026-05-05')+i*86400) for i in range(20)]
        a=E.summarize(rows);self.assertEqual(a,E.summarize(rows))
        self.assertLess(a['mean'],0);self.assertGreater(a['p_zero'],.5)


if __name__=='__main__':unittest.main()
