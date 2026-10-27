import unittest
from analysis import prior_quotes,price_difference,offset_interval

class ComparisonTests(unittest.TestCase):
    def test_future_quotes_not_used(self):
        with self.assertRaisesRegex(ValueError,'future'):prior_quotes([{'time_msc':101}],100)
    def test_no_pick_best_of_equal_timestamp_quotes(self):
        ticks=[{'time_msc':99,'bid':9},{'time_msc':100,'bid':10},{'time_msc':100,'bid':11},{'time_msc':101,'bid':12}]
        group,age=prior_quotes(ticks,100)
        self.assertEqual([x['bid'] for x in group],[10,11]);self.assertEqual(age,0)
    def test_stale_predecessor_rejected(self):
        with self.assertRaisesRegex(ValueError,'stale'):prior_quotes([{'time_msc':100}],1101)
    def test_out_of_order_input_rejected(self):
        with self.assertRaisesRegex(ValueError,'Chronology'):prior_quotes([{'time_msc':101},{'time_msc':100}],102)
    def test_transaction_direction_defines_adverse_change(self):
        self.assertAlmostEqual(price_difference(0,100.2,100),.2)
        self.assertAlmostEqual(price_difference(1,99.8,100),.2)
        self.assertAlmostEqual(price_difference(1,100.2,100),-.2)
    def test_offset_interval_not_latency_estimate(self):
        # Synthetic raw clock at epoch+7200.1 s; host bounds epoch+0.02..0.04 s.
        self.assertEqual(offset_interval(7200100,'1970-01-01T00:00:00.020+00:00','1970-01-01T00:00:00.040+00:00'),[7200060.,7200080.])
    def test_reversed_host_events_rejected(self):
        with self.assertRaises(ValueError):offset_interval(1,'2026-01-01T00:00:01+00:00','2026-01-01T00:00:00+00:00')

if __name__=='__main__':unittest.main()
