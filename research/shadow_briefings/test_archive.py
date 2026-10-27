import copy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from archive import Archive, MAX_BYTES, canonical

BASE=datetime(2026,10,26,8,0,tzinfo=timezone.utc)

def fixture():
    return dict(schema_version='shadow-briefing-1.0',mode='SHADOW',orders_authorized=False,
                complete=True,briefing_id='synthetic-morning-001',session='morning',
                source=dict(kind='manual_export',document_id='synthetic-message-001',
                            published_at='2026-10-26T09:00:00+01:00',publication_evidence='Synthetic fixture; not a real briefing'),
                plans=[dict(plan_id='p1',instrument='US500',decision='TRADE',kind='BUY_LIMIT',entry=100.,
                            sl=99.,tp=[102.,103.],valid_from='2026-10-26T08:00:00Z',valid_until='2026-10-26T12:00:00Z',reason='Synthetic'),
                       dict(plan_id='p2',instrument='EURPLN',decision='NO TRADE',sl=None,tp=None,reason='No setup'),
                       dict(plan_id='p3',target_plan_id='prior-oil',instrument='OIL',decision='HOLD',sl=95.,tp=[110.],reason='Await data'),
                       dict(plan_id='p4',target_plan_id='prior-gold',instrument='GOLD',decision='CANCEL',sl=None,tp=None,reason='Expired setup')])

class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.now=BASE+timedelta(seconds=5)
        self.a=Archive(Path(self.tmp.name)/'store',clock=lambda:self.now)
        self.addCleanup(self.a.close)
        self.document='Pełny briefing — SYNTHETIC TEST ONLY\n```json\n{}\n```\n'.encode('utf-8')
    def ingest(self,meta=None,document=None):
        return self.a.ingest(self.document if document is None else document,canonical(fixture() if meta is None else meta).encode('utf-8'))

    def test_full_document_all_decisions_and_exact_bytes_export(self):
        r=self.ingest();self.assertFalse(r['validation_errors'])
        data=self.a.get(r['record_id'])
        self.assertEqual([x['decision'] for x in data['metadata']['plans']],['TRADE','NO TRADE','HOLD','CANCEL'])
        out=Path(self.tmp.name)/'export';self.a.export(r['record_id'],out)
        self.assertEqual((out/(r['record_id']+'.source')).read_bytes(),self.document)
        self.assertEqual((out/(r['record_id']+'.metadata.source')).read_bytes(),canonical(fixture()).encode())
        self.assertIn('US500',(out/(r['record_id']+'.md')).read_text(encoding='utf-8'))
        self.assertFalse(data['orders_authorized'])

    def test_duplicate_keeps_first_receipt_and_adds_observation(self):
        one=self.ingest();self.now+=timedelta(hours=1);two=self.ingest()
        self.assertEqual(one['record_id'],two['record_id'])
        self.assertEqual(one['first_received_at'],two['first_received_at'])
        self.assertTrue(two['duplicate'])
        self.assertEqual(len(self.a.get(one['record_id'])['receipts']),2)

    def test_late_arrival_excluded_from_earlier_point_in_time(self):
        self.now+=timedelta(hours=2);self.ingest()
        self.assertEqual(self.a.as_of('2026-10-26T09:00:00Z'),[])
        self.assertTrue(self.a.as_of('2026-10-26T11:00:00Z')[0]['context_eligible'])

    def test_receipt_boundary_inclusive(self):
        r=self.ingest()
        self.assertEqual(len(self.a.as_of(r['first_received_at'])),1)
        self.assertEqual(self.a.as_of((self.now-timedelta(microseconds=1)).isoformat()),[])

    def test_later_duplicate_receipt_is_not_leaked_into_earlier_view(self):
        self.ingest();self.now+=timedelta(hours=2);self.ingest()
        self.assertEqual(len(self.a.as_of('2026-10-26T09:00:00Z')[0]['receipts']),1)

    def test_correction_retains_original_and_is_not_visible_early(self):
        one=self.ingest();self.now+=timedelta(hours=2)
        m=fixture();m['plans'][0]['sl']=98.;two=self.ingest(m)
        self.assertNotEqual(one['record_id'],two['record_id'])
        early=self.a.as_of('2026-10-26T09:00:00Z')
        self.assertEqual(len(early),1);self.assertEqual(early[0]['metadata']['plans'][0]['sl'],99.)
        self.assertEqual(len(self.a.as_of('2026-10-26T11:00:00Z')),2)

    def test_truncated_document_is_retained_but_ineligible(self):
        m=fixture();m['complete']=False;r=self.ingest(m)
        self.assertFalse(self.a.as_of(self.now.isoformat())[0]['context_eligible'])
        self.assertEqual(self.a.get(r['record_id'])['document_utf8'],self.document.decode())

    def test_publication_later_than_cutoff_excluded(self):
        m=fixture();m['source']['published_at']='2026-10-27T08:00:00Z';self.ingest(m)
        self.assertFalse(self.a.as_of(self.now.isoformat())[0]['context_eligible'])

    def test_unknown_publication_or_timezone_not_inferred(self):
        for value in [None,'2026-10-26T09:00:00','invalid']:
            with self.subTest(value=value):
                m=fixture();m['source']['published_at']=value;r=self.ingest(m)
                self.assertTrue(r['validation_errors'])
        self.assertTrue(all(not x['context_eligible'] for x in self.a.as_of(self.now.isoformat())))

    def test_injected_first_received_cannot_backdate_local_receipt(self):
        m=fixture();m['first_received_at']='2000-01-01T00:00:00Z';r=self.ingest(m)
        self.assertEqual(r['first_received_at'],'2026-10-26T08:00:05.000000+00:00')
        self.assertEqual(self.a.as_of('2026-10-26T08:00:04Z'),[])

    def test_authorization_flag_does_not_authorize_and_invalidates_context(self):
        m=fixture();m.update(orders_authorized=True,mode='LIVE');r=self.ingest(m)
        self.assertTrue(r['validation_errors']);self.assertFalse(r['orders_authorized'])
        self.assertFalse(self.a.get(r['record_id'])['orders_authorized'])

    def test_duplicate_plan_id_bad_levels_and_missing_cancel_target(self):
        m=fixture();m['plans'][1]['plan_id']='p1';m['plans'][0]['sl']=101.;del m['plans'][3]['target_plan_id']
        r=self.ingest(m);self.assertEqual(len(r['validation_errors']),3)

    def test_bad_metadata_exact_bytes_retained(self):
        for raw in [b'{bad',b'{"a":1,"a":2}',b'{"x":NaN}',b'{"x":1e999}',b'null',b'[]']:
            with self.subTest(raw=raw):
                r=self.a.ingest(self.document,raw)
                self.assertTrue(r['validation_errors'])
                stored=self.a.db.execute('SELECT raw_metadata FROM records WHERE id=?',(r['record_id'],)).fetchone()[0]
                self.assertEqual(stored,raw)

    def test_non_utf8_source_retained_without_fake_completeness(self):
        r=self.ingest(document=b'\xff\xfe')
        self.assertTrue(r['validation_errors'])
        self.assertFalse(self.a.as_of(self.now.isoformat())[0]['context_eligible'])

    def test_sql_records_and_receipts_append_only(self):
        self.ingest()
        for table in ['records','receipts']:
            with self.assertRaises(sqlite3.IntegrityError):self.a.db.execute('DELETE FROM '+table)
            self.a.db.rollback()
        with self.assertRaises(sqlite3.IntegrityError):self.a.db.execute("UPDATE records SET first_received_at='2000'")
        self.a.db.rollback()

    def test_clock_regression_is_visible_and_ineligible(self):
        self.ingest();self.now-=timedelta(seconds=1)
        r=self.ingest(document=b'Changed synthetic document')
        self.assertTrue(r['clock_regression'])
        self.assertFalse(self.a.as_of(self.now.isoformat())[0]['context_eligible'])

    def test_source_identifiers_are_not_used_as_paths(self):
        m=fixture();m['source']['document_id']='../../escape';m['briefing_id']='../escape'
        r=self.ingest(m);out=Path(self.tmp.name)/'export';self.a.export(r['record_id'],out)
        self.assertEqual(len(list(out.iterdir())),4)
        self.assertTrue(all(p.name.startswith(r['record_id']) for p in out.iterdir()))
        self.assertFalse((Path(self.tmp.name)/'escape').exists())

    def test_oversized_document_is_rejected_not_truncated(self):
        with self.assertRaisesRegex(ValueError,'not truncated'):self.ingest(document=b'x'*(MAX_BYTES+1))
        self.assertEqual(self.a.db.execute('SELECT count(*) FROM records').fetchone()[0],0)

    def test_malformed_nested_types_retained_as_invalid(self):
        for field,value in [('plans',{}),('source',[]),('session',{}),('source',{'kind':[]}),('plans',[{'decision':[]}])]:
            with self.subTest(field=field,value=value):
                m=fixture();m[field]=value;r=self.ingest(m)
                self.assertTrue(r['validation_errors'])

    def test_export_refuses_overwrite_after_later_receipt(self):
        r=self.ingest();out=Path(self.tmp.name)/'export';self.a.export(r['record_id'],out)
        self.now+=timedelta(seconds=1);self.ingest()
        with self.assertRaises(FileExistsError):self.a.export(r['record_id'],out)

    def test_plan_expiry_is_reported_without_authorizing_context(self):
        self.ingest();rows=self.a.as_of('2026-10-26T12:00:00Z')
        self.assertEqual(rows[0]['plan_states'][0]['temporal_state'],'EXPIRED')
        self.assertTrue(all(not p['orders_authorized'] for p in rows[0]['plan_states']))

    def test_archive_export_rejected_by_production_trade_import_schema(self):
        import sys
        sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
        from trading_ai.models import validate_briefing, Blocked
        r=self.ingest()
        with self.assertRaises(Blocked):validate_briefing(self.a.get(r['record_id']))

    def test_raw_blob_tampering_detected_even_if_sql_trigger_removed(self):
        r=self.ingest()
        self.a.db.execute('DROP TRIGGER records_no_update')
        self.a.db.execute("UPDATE records SET raw_document=X'00'")
        self.a.db.commit()
        with self.assertRaisesRegex(ValueError,'integrity failure'):self.a.get(r['record_id'])

    def test_cli_roundtrip_in_separate_process(self):
        import subprocess,sys
        root=Path(self.tmp.name);doc=root/'input.md';meta=root/'input.json'
        doc.write_bytes(self.document);meta.write_text(canonical(fixture()),encoding='utf-8')
        command=[sys.executable,str(Path(__file__).with_name('archive.py')),'--root',str(root/'cli')]
        first=subprocess.run(command+['ingest','--document',str(doc),'--metadata',str(meta)],capture_output=True,encoding='utf-8',check=True)
        receipt=json.loads(first.stdout);self.assertFalse(receipt['orders_authorized'])
        second=subprocess.run(command+['export','--id',receipt['record_id'],'--output',str(root/'cli-export')],capture_output=True,encoding='utf-8',check=True)
        exported=json.loads(Path(json.loads(second.stdout)['export']).read_text(encoding='utf-8'))
        self.assertEqual(exported['document_utf8'],self.document.decode('utf-8'))
        self.assertFalse(exported['orders_authorized'])

if __name__=='__main__':unittest.main()
