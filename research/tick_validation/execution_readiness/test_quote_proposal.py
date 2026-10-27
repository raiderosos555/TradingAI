import unittest
from quote_proposal import QuoteEvidence,recover_fresh_pair
class Tests(unittest.TestCase):
    def base(self):
        q=QuoteEvidence();q.feed(dict(time_msc=1000,flags=6,bid=100,ask=101));return q
    def test_last_does_not_refresh_quotes(self):
        q=self.base();q.feed(dict(time_msc=12000,flags=24,bid=0,ask=0,last=102))
        with self.assertRaises(ValueError):q.candidate(12000,continuous_evidence_id='SYNTHETIC',connected=True)
    def test_sides_have_separate_ages(self):
        q=self.base();q.feed(dict(time_msc=12000,flags=2,bid=100.1,ask=101))
        with self.assertRaises(ValueError):q.candidate(12000,continuous_evidence_id='SYNTHETIC',connected=True)
    def test_no_continuity_no_candidate(self):
        with self.assertRaises(ValueError):self.base().candidate(1001,continuous_evidence_id=None,connected=True)
    def test_reset_invalidates_side(self):
        q=self.base();q.feed(dict(time_msc=1001,flags=2,bid=0))
        with self.assertRaises(ValueError):q.candidate(1001,continuous_evidence_id='SYNTHETIC',connected=True)
    def test_same_ms_order_and_no_authority(self):
        q=self.base();q.feed(dict(time_msc=1000,flags=24,last=102,bid=0,ask=0))
        with self.assertRaises(ValueError):q.candidate(1000,continuous_evidence_id='SYNTHETIC',connected=True)
        q.feed(dict(time_msc=1000,flags=6,bid=100,ask=101))
        self.assertFalse(q.candidate(1000,continuous_evidence_id='SYNTHETIC',connected=True)['orders_authorized'])
    def test_disconnected(self):
        with self.assertRaises(ValueError):self.base().candidate(1000,continuous_evidence_id='SYNTHETIC',connected=False)
    def test_crossed(self):
        q=self.base();q.feed(dict(time_msc=1001,flags=2,bid=102))
        with self.assertRaises(ValueError):q.candidate(1001,continuous_evidence_id='SYNTHETIC',connected=True)

    def test_recovery_requires_new_both_sides_event(self):
        values=iter([dict(time_msc=1000,flags=6,bid=100,ask=101),
            dict(time_msc=1001,flags=24,bid=100,ask=101),dict(time_msc=1002,flags=6,bid=100,ask=101)])
        r=recover_fresh_pair(dict(time_msc=1000),lambda:next(values),now_raw_ms=lambda:1002)
        self.assertEqual(r['tick']['time_msc'],1002);self.assertFalse(r['orders_authorized'])

    def test_recovery_exhaustion_has_no_fallback(self):
        with self.assertRaises(ValueError):
            recover_fresh_pair(dict(time_msc=1000),lambda:dict(time_msc=999,flags=6,bid=100,ask=101),now_raw_ms=lambda:1001)

    def test_future_and_stale_recovery_rejected(self):
        for ms in [999999,1001]:
            with self.assertRaises(ValueError):
                recover_fresh_pair(dict(time_msc=1000),lambda:dict(time_msc=ms,flags=6,bid=100,ask=101),now_raw_ms=lambda:20000)
