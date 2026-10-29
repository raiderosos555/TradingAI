import ast,json,tempfile,unittest
from unittest.mock import patch
from datetime import datetime,timedelta,timezone
from pathlib import Path
from capture_eia import accept,clocks_consistent
from run_eia_window import slots,run

RAW=('"STUB_1","10/23/26","10/16/26","Difference"\n'
     '"Commercial (Excluding SPR)","410.625","412.517","-1.892"\n'
     '"Total Motor Gasoline","209.180","205.310","3.870"\n'
     '"Distillate Fuel Oil","102.824","104.286","-1.462"\n').encode()

class CaptureTests(unittest.TestCase):
    def test_reference_and_no_invented_publication(self):
        r=accept(RAW,'2026-10-23');self.assertEqual(r['stocks']['crude']['change'],'-1.892')
        self.assertNotIn('release_date',r);self.assertNotIn('scheduled_utc',r)
    def test_old_response_rejected(self):
        with self.assertRaises(ValueError):accept(RAW,'2026-10-30')
    def test_html_and_corruption_rejected(self):
        for blob in (b'<html>error</html>',RAW.replace(b'-1.892',b'1.892')):
            with self.assertRaises((ValueError,IndexError)):accept(blob,'2026-10-23')
    def test_clock_regression_and_jump(self):
        before=datetime(2026,10,29,tzinfo=timezone.utc)
        self.assertTrue(clocks_consistent(before,before+timedelta(seconds=2),2.01))
        self.assertFalse(clocks_consistent(before,before-timedelta(seconds=2),2))
        self.assertFalse(clocks_consistent(before,before+timedelta(hours=1),2))
    def test_no_trading_dependencies(self):
        tree=ast.parse(Path(__file__).with_name('capture_eia.py').read_text())
        imports=[n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
        imports += [a.name for n in ast.walk(tree) if isinstance(n,ast.Import) for a in n.names]
        self.assertFalse(any(x and ('MetaTrader5' in x or 'trading_ai' in x) for x in imports))
    def test_fixed_window_limits(self):
        p=json.loads(Path(__file__).with_name('eia_pilot_20261104.json').read_text())
        s=slots(p);self.assertEqual(len(s),40);self.assertEqual(s[-1]-s[0],39*60)
        p['max_requests']=41
        with self.assertRaises(ValueError):slots(p)
    def test_no_late_backfill_or_early_service(self):
        protocol=Path(__file__).with_name('eia_pilot_20261104.json')
        p=json.loads(protocol.read_text());s=slots(p)
        for clock in (s[0]-1000,s[-1]+120):
            with tempfile.TemporaryDirectory() as d,patch('run_eia_window.time.time',return_value=clock):
                out=Path(d)/'attempt'
                with self.assertRaises(ValueError):run(protocol,out)
                self.assertFalse(out.exists())

if __name__=='__main__':unittest.main()
