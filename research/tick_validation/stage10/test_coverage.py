import unittest
from coverage import raw_groups, combine, intervals_union

def tick(ms, bid=100):
    return dict(time=ms//1000, time_msc=ms, bid=bid, ask=bid+1, last=bid+.5, volume=0, flags=8, volume_real=0.0)

def capture(name, rows, lo=1000, hi=2000):
    groups, count = raw_groups(rows, lo, hi)
    return dict(source=name, start_raw_ms=lo, end_raw_ms=hi, groups=groups, count=count)

class CoverageTests(unittest.TestCase):
    def test_duplicate_captures_keep_identical_same_ms_rows(self):
        rows = [tick(1000), tick(1000), tick(1500)]
        result = combine([capture('a', rows), capture('b', rows)])
        self.assertEqual(result['consistent_unique_records'], 3)
        self.assertEqual(result['repeated_records_across_captures'], 3)
        self.assertEqual(result['same_ms_additional_records'], 1)

    def test_changed_same_ms_order_conflicts(self):
        result = combine([capture('a', [tick(1000), tick(1000, 101)]), capture('b', [tick(1000, 101), tick(1000)])])
        self.assertIsNone(result['consistent_unique_records'])
        self.assertEqual(len(result['overlap_conflicts']), 1)

    def test_missing_timestamp_in_overlap_conflicts(self):
        result = combine([capture('a', [tick(1000), tick(1500)]), capture('b', [tick(1000)])])
        self.assertEqual(result['overlap_conflicts'][0]['first_differing_raw_ms'], 1500)

    def test_empty_vs_observed_overlap_conflicts(self):
        result = combine([capture('a', []), capture('b', [tick(1000)])])
        self.assertIsNone(result['consistent_unique_records'])

    def test_partial_overlap_only_compares_shared_window(self):
        result = combine([capture('a', [tick(1000), tick(1500)]), capture('b', [tick(1500), tick(2200)], 1500, 2500)])
        self.assertEqual(result['consistent_unique_records'], 3)
        self.assertEqual(result['requested_duration_ms'], 1500)

    def test_half_open_adjacent_windows(self):
        result = combine([capture('a', [tick(1999)]), capture('b', [tick(2000)], 2000, 3000)])
        self.assertEqual(result['checked_overlap_pairs'], 0)
        self.assertEqual(result['successful_request_ranges_raw_ms'], [[1000, 3000]])

    def test_does_not_bridge_missing_time(self):
        self.assertEqual(intervals_union([[1000, 2000], [3000, 4000]]), [[1000, 2000], [3000, 4000]])

    def test_out_of_order_rejected(self):
        with self.assertRaises(ValueError): capture('a', [tick(1500), tick(1000)])

    def test_invalid_quote_rejected(self):
        with self.assertRaises(ValueError): capture('a', [dict(tick(1000), ask=99)])

    def test_legacy_normalized_clock_not_used(self):
        row = dict(tick(1000), time=-7199, time_msc=-7199000, broker_raw_time=1, broker_raw_time_msc=1000)
        groups, count = raw_groups([row], 1000, 2000)
        self.assertEqual(list(groups), [1000])
        self.assertEqual(count, 1)

    def test_incomplete_raw_provenance_rejected(self):
        with self.assertRaises(ValueError): capture('a', [dict(tick(1000), broker_raw_time=1)])

    def test_outside_request_and_inconsistent_seconds_rejected(self):
        for row in [tick(2000), dict(tick(1000), time=2)]:
            with self.subTest(row=row), self.assertRaises(ValueError): capture('a', [row])
