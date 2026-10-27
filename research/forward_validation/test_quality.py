import unittest
from quality import inspect_ticks,clock_anchor,executable

def tick(ms,bid=100,ask=101,flags=6):return dict(time_msc=ms,bid=bid,ask=ask,last=100.5,flags=flags,volume=1)

class QualityTests(unittest.TestCase):
    def test_duplicate_ticks_and_equal_time_order_preserved(self):
        rows=[tick(1000),tick(1000),tick(1000,bid=0,ask=0,flags=24)]
        q=inspect_ticks(rows,1000,2000)
        self.assertEqual(q['count'],3);self.assertEqual(q['invalid_quotes'],1)
        self.assertEqual(q['trade_only_invalid'],1)
        self.assertIsNone(q['last_explicit_side_change_raw_ms']['bid'])
    def test_last_update_does_not_refresh_side_clock(self):
        q=inspect_ticks([tick(1000),tick(1100,flags=24)],1000,2000)
        self.assertEqual(q['last_explicit_side_change_raw_ms'],dict(bid=1000,ask=1000))
    def test_overlap_exact_sequence_not_set(self):
        rows=[tick(1000),tick(1000),tick(3100)]
        self.assertEqual(inspect_ticks(rows,3000,4000,rows[:2])['overlap_status'],'MATCH')
        self.assertEqual(inspect_ticks(rows,3000,4000,rows[:1])['overlap_status'],'MISMATCH')
    def test_exclusive_upper_boundary(self):
        self.assertEqual(inspect_ticks([tick(1000),tick(2000)],1000,2000)['count'],1)
    def test_empty_is_not_certified_complete(self):
        q=inspect_ticks([],1000,2000)
        self.assertTrue(q['empty_interval']);self.assertFalse(q['completeness_certified'])
    def test_backwards_provider_order_rejected(self):
        with self.assertRaises(ValueError):inspect_ticks([tick(1500),tick(1000)],1000,2000)
    def test_crossed_nan_zero_quotes(self):
        for t in [tick(1,102,101),tick(1,0,101),tick(1,float('nan'),101)]:self.assertFalse(executable(t))
    def test_forward_offset_requires_ea_agreement(self):
        self.assertEqual(clock_anchor(4600000,1000,1000.1,3600)['status'],'CONSISTENT_CANDIDATE')
        self.assertEqual(clock_anchor(4600000,1000,1000.1,7200)['status'],'UNCORROBORATED')
    def test_stale_tick_does_not_verify_offset(self):
        self.assertEqual(clock_anchor(4590000,1000,1000.1,3600)['status'],'UNCORROBORATED')
    def test_clock_rollback_and_slow_call(self):
        for a,b in [(1001,1000),(1000,1003)]:self.assertEqual(clock_anchor(4600000,a,b,3600)['status'],'INVALID_HOST_BRACKET')

if __name__=='__main__':unittest.main()
