import unittest
from comparison import compare

HOUR = 3600000
def tick(ms, last=100, flags=8):
    return dict(time=ms//1000, time_msc=ms, bid=last-.1, ask=last+.1, last=last, flags=flags)
def ref(ms, price=100, count=1):
    return dict(broker_raw_time=ms//1000, open=price, high=price, low=price, close=price, tick_volume=count)

class ComparisonTests(unittest.TestCase):
    def test_absent_hour_not_merged_into_previous_bar(self):
        rows = compare([tick(22*HOUR)], [ref(22*HOUR)], 'H1', 22*HOUR, 24*HOUR, [[22*HOUR,24*HOUR]])
        self.assertEqual([r['status'] for r in rows], ['MATCH','REFERENCE_ABSENT_NO_LAST'])
        self.assertEqual(rows[0]['end_raw_ms'], 23*HOUR)

    def test_missing_request_not_classified_as_empty_session(self):
        rows = compare([], [], 'H1', 0, HOUR, [])
        self.assertEqual(rows[0]['status'], 'INCOMPLETE_REQUEST_COVERAGE')

    def test_quote_only_updates_do_not_create_last_bar(self):
        rows = compare([tick(0, flags=2)], [], 'H1', 0, HOUR, [[0,HOUR]])
        self.assertEqual(rows[0]['status'], 'REFERENCE_ABSENT_NO_LAST')
        self.assertIsNotNone(rows[0]['ohlc']['bid'])
        self.assertIsNone(rows[0]['ohlc']['last'])

    def test_last_update_with_missing_reference_is_error(self):
        rows = compare([tick(0)], [], 'H1', 0, HOUR, [[0,HOUR]])
        self.assertEqual(rows[0]['status'], 'REFERENCE_MISSING_WITH_LAST')

    def test_tick_count_mismatch_not_hidden_by_equal_ohlc(self):
        rows = compare([tick(0),tick(1)], [ref(0)], 'H1', 0, HOUR, [[0,HOUR]])
        self.assertTrue(rows[0]['last_matches'])
        self.assertEqual(rows[0]['status'], 'MISMATCH')

    def test_reference_off_grid_is_rejected(self):
        with self.assertRaises(ValueError): compare([], [ref(60000)], 'H1', 0, HOUR, [[0,HOUR]])

    def test_duplicate_reference_rejected(self):
        with self.assertRaises(ValueError): compare([], [ref(0),ref(0)], 'H1', 0, HOUR, [[0,HOUR]])

    def test_half_open_tick_moves_to_next_hour(self):
        rows = compare([tick(HOUR)], [ref(HOUR)], 'H1', 0, 2*HOUR, [[0,2*HOUR]])
        self.assertEqual([r['status'] for r in rows], ['REFERENCE_ABSENT_NO_LAST','MATCH'])

    def test_valid_last_does_not_make_zero_quote_executable(self):
        from research.tick_validation.model import execution_price
        bad=dict(tick(0),bid=0,ask=0)
        rows=compare([bad],[ref(0)],'H1',0,HOUR,[[0,HOUR]])
        self.assertEqual(rows[0]['status'],'MATCH_LAST_WITH_INVALID_QUOTES')
        self.assertIsNone(rows[0]['ohlc']['bid'])
        with self.assertRaises(ValueError):execution_price('BUY','OPEN',bad)

    def test_quote_recovery_preserves_same_ms_provider_order(self):
        from quality import quote_health
        bad=dict(tick(1),bid=0,ask=0)
        health=quote_health([tick(0),bad,tick(1)])
        self.assertEqual(health['unavailable_intervals'],[dict(start_provider_index=1,start_raw_ms=1,
            end_provider_index=2,end_raw_ms=1,recovered=True)])

    def test_no_recovery_does_not_fabricate_endpoint(self):
        from quality import quote_health
        health=quote_health([dict(tick(1),ask=0)])
        self.assertIsNone(health['unavailable_intervals'][0]['end_raw_ms'])

    def test_invalid_last_is_not_hidden_by_valid_quote(self):
        rows=compare([dict(tick(0),last=0)],[ref(0)],'H1',0,HOUR,[[0,HOUR]])
        self.assertEqual(rows[0]['status'],'INVALID_LAST_UPDATES')

    def test_invalid_quote_does_not_pollute_spread_or_ohlc(self):
        rows=compare([dict(tick(0),bid=0,ask=0),tick(1)],[ref(0,count=2)],'H1',0,HOUR,[[0,HOUR]])
        self.assertEqual(rows[0]['ohlc']['bid']['low'],99.9)
        self.assertFalse(rows[0]['bid_ask_ohlc_complete'])

    def test_diagnostic_aggregator_still_rejects_reversed_time(self):
        with self.assertRaises(ValueError):compare([tick(1),tick(0)],[ref(0)],'H1',0,HOUR,[[0,HOUR]])
