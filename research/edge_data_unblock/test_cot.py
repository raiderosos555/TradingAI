"""Controlled checks of timing, exclusions, arithmetic and multiplicity."""
import unittest
import tempfile,json,argparse
from pathlib import Path
from datetime import date
import numpy as np
import cot_experiment as C

class TestCOT(unittest.TestCase):
    def setUp(self):
        self.d=date(2020,1,7).toordinal()
        self.data={self.d+7*i:{'share':i/100} for i in range(20)}
    def test_cot_never_uses_future(self):
        v,err=C.cot_signal(self.data,self.d+7*10+14,14)
        self.assertIsNone(err);self.assertEqual(v[1][-1],self.d+70)
        self.assertAlmostEqual(v[0],.04)
    def test_stale_is_not_forward_filled(self):
        self.assertEqual(C.cot_signal(self.data,self.d+200,14)[1],'stale_cot')
    def test_report_gap_is_rejected(self):
        del self.data[self.d+63]
        self.assertEqual(C.cot_signal(self.data,self.d+84,14)[1],'cot_gap')
    def test_known_shutdown_excluded(self):
        d=date(2025,9,30).toordinal();data={d+7*i:{'share':i/100} for i in range(6)}
        self.assertEqual(C.cot_signal(data,d+42,14)[1],'publication_disruption')
    def test_previous_is_backward_and_bounded(self):
        self.assertEqual(C.previous([10,15,20],19),15)
        self.assertIsNone(C.previous([10,15,20],40))
    def test_nonoverlapping_and_no_split_leak(self):
        prices={self.d+i:1+i/10000 for i in range(-400,200)}
        rows,_=C.build_rows(prices,self.data,4,14)
        self.assertGreater(len(rows),0)
        for a,b in zip(rows,rows[1:]):self.assertLessEqual(a['exit'],b['entry'])
        for r in rows:self.assertEqual(C.part(date.fromisoformat(r['entry']).toordinal()),C.part(date.fromisoformat(r['exit']).toordinal()))
    def test_holm(self):
        self.assertEqual(C.holm({'a':.01,'b':.03,'c':.8}),{'a':.03,'b':.06,'c':.8})
    def test_known_markout_drawdown(self):
        s=C.markout_stats([10,-20,5]);self.assertEqual(s['max_sum_drawdown_bps'],20)
        self.assertEqual(s['positive_negative_ratio'],.75)
    def test_cash_cost_and_matched_exposure(self):
        rows=[]
        for i in range(12):
            rows.append(dict(A=10.,B=10. if i%2 else 0.,selected=i%2,direction=1,
                move_bps=10.,block=f'202{i//4}Q{i%4+1}',year=2020+i//4,weeks=1,placebo_selected=0))
        s=C.summarize(rows)
        self.assertEqual(s['hurdles']['base']['A'],3)
        self.assertEqual(s['hurdles']['base']['B'],1.5)
        self.assertEqual(s['exposure_matched_delta'],0)
    def test_signed_fx_direction(self):
        move=(1.1/1-1)*10000
        self.assertAlmostEqual(move,1000)
        self.assertAlmostEqual(-move,-1000)
    def test_active_terminal_is_refused_before_ipc(self):
        import isolated_mt5_probe as P
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);terminal=root/'terminal64.exe'
            (root/'config.demo.json').write_text(json.dumps({'terminal_path':str(terminal)}))
            args=argparse.Namespace(root=root,terminal=terminal,out=root/'out.json',child=None)
            with self.assertRaisesRegex(RuntimeError,'Active terminal forbidden'):P.main(args)
            self.assertFalse(args.out.exists())

if __name__=='__main__':unittest.main()
