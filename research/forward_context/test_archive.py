import json,sqlite3,tempfile,unittest
from datetime import datetime,timedelta,timezone
from pathlib import Path
from archive import ContextArchive,stamp


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.now=datetime(2026,10,26,14,tzinfo=timezone.utc)
        self.a=ContextArchive(self.tmp.name,clock=lambda:self.now);self.addCleanup(self.a.close)
        self.spec=dict(kind='calendar',account=[123,'SIMULATOR'],max_age_seconds=900)

    def payload(self,**updates):
        d=dict(schema_version='1.0',read_only=True,status='OK',account_login=123,account_server='SIMULATOR',
            retrieved_at_utc=self.now.timestamp(),coverage_from_utc=self.now.timestamp()-3600,
            coverage_until_utc=self.now.timestamp()+86400,events=[{'name':'CONTROL'}])
        d.update(updates);return json.dumps(d).encode()

    def put(self,raw=None):return self.a.observe('calendar',self.spec,raw=self.payload() if raw is None else raw)

    def test_source_publication_and_mtime_do_not_backdate_receipt(self):
        before=self.now-timedelta(minutes=5)
        self.put(self.payload(retrieved_at_utc=before.timestamp()))
        self.assertEqual(self.a.asof('calendar',before)['status'],'UNAVAILABLE')
        self.assertEqual(self.a.asof('calendar',self.now)['first_received_at'],stamp(self.now))

    def test_duplicate_preserves_first_receipt_and_exact_bytes(self):
        raw=self.payload()+b'\n';self.put(raw);first=stamp(self.now)
        self.now+=timedelta(seconds=5);self.put(raw)
        self.assertEqual(self.a.verify()['versions'],1)
        self.assertEqual(self.a.verify()['observations'],2)
        self.assertEqual(self.a.asof('calendar',self.now)['first_received_at'],first)
        self.assertEqual(self.a.db.execute('SELECT raw FROM versions').fetchone()[0],raw)

    def test_revision_only_available_after_observation(self):
        first=self.now;self.put()
        self.now+=timedelta(seconds=10);self.put(self.payload(events=[{'name':'REVISED'}]))
        self.assertEqual(self.a.asof('calendar',first)['source_payload']['events'][0]['name'],'CONTROL')
        self.assertEqual(self.a.asof('calendar',self.now)['source_payload']['events'][0]['name'],'REVISED')

    def test_new_missing_file_blocks_no_fallback(self):
        self.put();self.now+=timedelta(seconds=5)
        self.a.observe('calendar',self.spec,error='File missing')
        self.assertEqual(self.a.asof('calendar',self.now)['status'],'UNAVAILABLE')

    def test_new_invalid_version_blocks_no_fallback_and_preserves_bytes(self):
        self.put();self.now+=timedelta(seconds=5);raw=b'{"broken"';self.put(raw)
        self.assertEqual(self.a.asof('calendar',self.now)['status'],'INVALID')
        self.assertEqual(self.a.verify()['versions'],2)

    def test_future_provider_time_not_accepted(self):
        self.put(self.payload(retrieved_at_utc=self.now.timestamp()+1))
        self.assertEqual(self.a.asof('calendar',self.now)['status'],'INVALID')

    def test_clock_regression_does_not_create_earlier_availability(self):
        first=self.now;self.put()
        self.now-=timedelta(seconds=10);self.put(self.payload(events=[{'name':'LATER_RECEIVED'}]))
        self.assertEqual(self.a.asof('calendar',self.now)['status'],'UNAVAILABLE')
        self.assertEqual(self.a.asof('calendar',first)['status'],'CLOCK_REGRESSION')
        self.assertTrue(self.a.verify()['observations']==2)

    def test_stale_calendar_and_account_mismatch(self):
        self.put();self.now+=timedelta(seconds=901)
        self.assertEqual(self.a.asof('calendar',self.now)['status'],'STALE')
        self.put(self.payload(account_login=456))
        self.assertEqual(self.a.asof('calendar',self.now)['status'],'INVALID')

    def test_sql_update_and_delete_are_rejected(self):
        self.put()
        for query in ['DELETE FROM observations','DELETE FROM versions',"UPDATE versions SET first_received_at='yesterday'", "UPDATE observations SET payload='{}'"]:
            with self.assertRaises(sqlite3.IntegrityError):self.a.db.execute(query)

    def test_duplicate_keys_nonfinite_and_bad_time_types_rejected(self):
        for raw in [b'{"x":1,"x":2}',b'{"x":NaN}',b'{"x":1e999}',self.payload(coverage_until_utc='invalid')]:
            self.put(raw);self.assertEqual(self.a.asof('calendar',self.now)['status'],'INVALID')

    def test_local_file_mtime_is_not_first_receipt(self):
        path=Path(self.tmp.name)/'source.json';path.write_bytes(self.payload())
        self.a.capture_file('calendar',dict(self.spec,path=str(path)))
        result=self.a.asof('calendar',self.now)
        self.assertTrue(result['receipt']['source_stat']['mtime_is_not_receipt_evidence'])

    def test_news_uses_publication_and_producer_first_seen_and_never_authorizes(self):
        old=stamp(self.now-timedelta(hours=1));future=stamp(self.now+timedelta(hours=1))
        d=dict(as_of=stamp(self.now),mode='SHADOW_CONTEXT',orders_authorized=False,status='PARTIAL',
            coverage_gaps=['fixture gap'],items=[dict(id='old',published_at=old,first_seen_at=old),
                dict(id='future',published_at=future,first_seen_at=old),dict(id='late',published_at=old,first_seen_at=future)])
        self.a.observe('news',dict(kind='news',max_age_seconds=1800),raw=json.dumps(d).encode())
        result=self.a.asof('news',self.now)
        self.assertEqual([x['id'] for x in result['eligible_news_items']],['old'])
        self.assertFalse(result['orders_authorized']);self.assertEqual(result['news_coverage_gaps'],['fixture gap'])

    def test_corruption_is_detected(self):
        self.put();self.a.db.execute('DROP TRIGGER observations_no_update')
        self.a.db.execute("UPDATE observations SET record_hash='forged'")
        with self.assertRaises(AssertionError):self.a.verify()
