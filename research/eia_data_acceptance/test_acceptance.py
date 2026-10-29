import ast,unittest
from pathlib import Path
from types import SimpleNamespace as NS
from validate_tables import parse, scheduled, validate, HERE
from probe_ticks import gate

def sample(extra='',change='3.475'):
    return ('"STUB_1","2/27/26","2/20/26","Difference"\n'
            f'"Commercial (Excluding SPR)","439.279","435.804","{change}"\n'
            '"Total Motor Gasoline","253.130","254.834","-1.704"\n'
            '"Distillate Fuel Oil","120.780","120.351","0.429"\n'+extra).encode()

class AcceptanceTests(unittest.TestCase):
    def test_dst(self):
        self.assertIn('15:30',scheduled('2026-03-04'))
        self.assertIn('14:30',scheduled('2026-03-11'))
    def test_no_invented_publication(self):
        r=parse(sample(),'2026-03-04')
        self.assertIsNone(r['published_at']);self.assertFalse(r['first_print_verified'])
    def test_arithmetic_rejects_corruption(self):
        with self.assertRaises(ValueError):parse(sample(change='4.475'),'2026-03-04')
    def test_duplicate_rejected(self):
        with self.assertRaises(ValueError):parse(sample('"Total Motor Gasoline",1,1,0\n'),'2026-03-04')
    def test_other_sections_not_merged(self):
        r=parse(sample('STUB_1,foo\n"Total Motor Gasoline",1,1,0\n'),'2026-03-04')
        self.assertEqual(r['stocks']['gasoline']['current'],'253.130')
    def test_reference_week(self):
        with self.assertRaises(ValueError):parse(sample(),'2026-03-11')
    def test_gate(self):
        c={'terminal_path':'C:/active/terminal64.exe','account_server':'TEST','account_login':1}
        t=NS(connected=True,path='C:/research',data_path='C:/research',trade_allowed=False,dlls_allowed=False)
        a=NS(trade_mode=0,server='TEST',login=1,trade_allowed=False,trade_expert=False)
        terminal=Path('C:/research/terminal64.exe');active=Path('C:/active-data')
        self.assertTrue(all(gate(t,a,c,terminal,active).values()))
        a.trade_allowed=True;a.trade_expert=True
        self.assertTrue(all(gate(t,a,c,terminal,active).values()))
        for obj,attr,value in ((a,'trade_mode',2),(a,'login',2),(t,'dlls_allowed',True),(t,'trade_allowed',True),
                                (t,'data_path','C:/active-data'),(t,'path','C:/active')):
            old=getattr(obj,attr);setattr(obj,attr,value)
            with self.assertRaises(RuntimeError):gate(t,a,c,terminal,active)
            setattr(obj,attr,old)
    def test_probe_mt5_call_allowlist(self):
        tree=ast.parse((HERE/'probe_ticks.py').read_text())
        calls={n.func.attr for n in ast.walk(tree) if isinstance(n,ast.Call)
               and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='mt5'}
        self.assertEqual(calls,{'initialize','terminal_info','account_info','symbol_info','copy_ticks_range','last_error','shutdown'})
        self.assertFalse(any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name)
                             and n.func.id in ('eval','exec','getattr') for n in ast.walk(tree)))
    @unittest.skipUnless((HERE/'private/tables-v1/manifest.json').exists(),'Private source archive not installed')
    def test_real_source_integrity(self):
        r=validate(HERE/'private/tables-v1')
        self.assertEqual(len(r['events']),12);self.assertEqual(len(r['same_week_comparisons']),33)

if __name__=='__main__':unittest.main()
