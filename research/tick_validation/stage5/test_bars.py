import unittest
from bars import aggregate,missing_intervals,Unverified

def tick(t,bid=100,ask=100.2,last=100.1,flags=14):return dict(time_msc=t,bid=bid,ask=ask,last=last,flags=flags)

class AggregationTests(unittest.TestCase):
    def test_half_open_boundary_tick_only_in_next_bar(self):
        b=aggregate([tick(99),tick(100,last=101)],[(0,100),(100,200)])
        self.assertEqual([r['last_updates'] for r in b],[1,1])
        self.assertEqual(b[1]['ohlc']['last']['open'],101)
    def test_last_quote_carry_not_counted_as_signal_update(self):
        b=aggregate([tick(1,last=100),tick(2,last=500,flags=6),tick(3,last=101)],[(0,10)])[0]
        self.assertEqual(b['tick_records'],3);self.assertEqual(b['last_updates'],2)
        self.assertEqual(b['ohlc']['last'],dict(open=100,high=101,low=100,close=101))
    def test_equal_ms_records_kept_in_provider_order(self):
        b=aggregate([tick(1,last=102),tick(1,last=101)],[(0,10)])[0]
        self.assertEqual(b['last_updates'],2);self.assertEqual(b['ohlc']['last']['close'],101)
    def test_empty_bar_does_not_copy_previous_close(self):
        b=aggregate([tick(1)],[(0,10),(10,20)])
        self.assertEqual(b[1]['tick_records'],0);self.assertIsNone(b[1]['ohlc']['last'])
    def test_unflagged_last_does_not_create_ohlc(self):
        b=aggregate([tick(1,flags=6)],[(0,10)])[0]
        self.assertIsNone(b['ohlc']['last']);self.assertIsNotNone(b['ohlc']['bid'])
    def test_invalid_last_update_blocks_aggregation(self):
        with self.assertRaises(Unverified):aggregate([tick(1,last=0)],[(0,10)])
    def test_out_of_order_quotes_rejected(self):
        with self.assertRaises(Unverified):aggregate([tick(2),tick(1)],[(0,10)])
    def test_overlapping_boundaries_rejected(self):
        with self.assertRaises(ValueError):aggregate([],[(0,20),(10,30)])
    def test_different_boundary_lengths_do_not_assume_24h(self):
        intervals=[(0,23*3600000),(23*3600000,48*3600000)]
        b=aggregate([tick(23*3600000-1),tick(23*3600000)],intervals)
        self.assertEqual([x['tick_records'] for x in b],[1,1])
    def test_internal_missing_request_is_reported(self):
        self.assertEqual(missing_intervals(0,100,[(0,20),(50,100)]),[[20,50]])
    def test_overlapping_requests_do_not_fake_additional_coverage(self):
        self.assertEqual(missing_intervals(0,100,[(0,60),(30,80)]),[[80,100]])
    def test_no_successful_request_means_entire_day_unknown(self):
        self.assertEqual(missing_intervals(0,100,[]),[[0,100]])

if __name__=='__main__':unittest.main()
