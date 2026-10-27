import unittest
from datetime import datetime,timezone
from window_audit import gaps,ready_time
class WindowTests(unittest.TestCase):
    def test_union_does_not_double_count_overlaps(self):self.assertEqual(gaps([(0,60),(30,90),(90,120)],0,120),[])
    def test_missing_edge_and_internal_ranges(self):self.assertEqual(gaps([(10,20),(40,90)],0,100),[[0,10],[20,40],[90,100]])
    def test_clip_outside_window(self):self.assertEqual(gaps([(-100,20),(20,200)],0,100),[])
    def test_empty_and_exclusive_boundary(self):self.assertEqual(gaps([(100,150)],0,100),[[0,100]])
    def test_must_wait_until_complete_window(self):
        end=datetime(2026,10,27,16,tzinfo=timezone.utc)
        self.assertFalse(ready_time(end.replace(hour=15),end));self.assertTrue(ready_time(end,end))
