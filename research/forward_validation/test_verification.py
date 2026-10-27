import ast,unittest
from pathlib import Path
from verify_capture import ntp_evidence

class EvidenceTests(unittest.TestCase):
    def test_worker_has_only_read_only_mt5_calls(self):
        tree=ast.parse((Path(__file__).parent/'worker.py').read_text())
        calls={n.func.attr for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='mt5'}
        allowed={'initialize','last_error','account_info','terminal_info','version','symbol_info_tick','symbol_info',
            'copy_ticks_range','copy_rates_from_pos','order_calc_profit','order_calc_margin','positions_get',
            'orders_get','history_deals_get','history_orders_get','shutdown'}
        self.assertLessEqual(calls,allowed)
        self.assertNotIn('order_send',calls)
    def test_unknown_ntp_text_cannot_certify_clock(self):
        p={'at':'2026-10-26T18:00:00+00:00','evidence':{'status':{'returncode':0,'stdout':'Unrecognized locale'}}}
        self.assertEqual(ntp_evidence(p)['status'],'NTP_UNPARSED')
    def test_high_uncertainty_and_unsynchronized_ntp_rejected(self):
        text='Leap Indicator: 0\nStratum: 5\nRoot Dispersion: 1.2s\nRoot Delay: 0.1s\nPhase Offset: 0.1s\nTime since Last Good Sync Time: 100s\nLast Sync Error: 0'
        p={'at':'2026-10-26T18:00:00+00:00','evidence':{'status':{'returncode':0,'stdout':text}}}
        self.assertEqual(ntp_evidence(p)['status'],'NTP_STATUS_ACCEPTABLE')
        for changed in [text.replace('Dispersion: 1.2','Dispersion: 5.2'),text.replace('Indicator: 0','Indicator: 3'),text.replace('Time: 100s','Time: 40000s')]:
            p['evidence']['status']['stdout']=changed
            self.assertEqual(ntp_evidence(p)['status'],'NTP_STATUS_NOT_ACCEPTABLE')

if __name__=='__main__':unittest.main()
