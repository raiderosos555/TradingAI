import tempfile
import unittest
from pathlib import Path
from datetime import datetime,timedelta,timezone
from trading_ai.news import parse_feed,eligible,summary,markdown
from trading_ai.journal import atomic_write
from trading_ai.models import canonical
from unittest.mock import patch
from trading_ai.news import collect
from trading_ai.news import record_signal_context,download
from trading_ai.journal import Journal
from trading_ai.models import digest
from urllib.error import URLError

class NewsTests(unittest.TestCase):
    def setUp(self):self.now=datetime(2026,10,24,12,tzinfo=timezone.utc)
    def feed(self,date='Sat, 24 Oct 2026 10:00:00 GMT',link='https://www.eia.gov/todayinenergy/detail.php?id=1'):
        return f'<rss><channel><item><title>Oil supply and sanctions</title><link>{link}</link><pubDate>{date}</pubDate></item></channel></rss>'.encode()
    def test_source_provenance_and_no_invented_direction(self):
        items,rejected=parse_feed(self.feed(),'eia',self.now)
        self.assertEqual(rejected,0)
        self.assertEqual(items[0]['direction'],'UNDETERMINED')
        self.assertEqual(items[0]['instruments'],['OIL'])
        self.assertTrue(items[0]['event_keyword'])
    def test_future_undated_and_foreign_links_rejected(self):
        for raw in [self.feed('Sun, 25 Oct 2026 10:00:00 GMT'),self.feed('invalid'),self.feed(link='https://evil.example/news')]:
            with self.assertRaises(ValueError):parse_feed(raw,'eia',self.now)
    def test_no_xml_entities(self):
        with self.assertRaises(ValueError):parse_feed(b'<!DOCTYPE rss>'+self.feed(),'eia',self.now)
    def test_news_cannot_be_used_before_first_observation(self):
        item=parse_feed(self.feed(),'eia',self.now)[0][0]
        item['first_seen_at']=self.now.isoformat()
        self.assertFalse(eligible(item,self.now-timedelta(minutes=30)))
        self.assertTrue(eligible(item,self.now))
        self.assertFalse(eligible(item,self.now+timedelta(days=4)))
    def test_missing_and_stale_feed_are_not_clear(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            self.assertEqual(summary(p,self.now)['status'],'UNAVAILABLE')
            atomic_write(p/'latest.json',canonical({'as_of':(self.now-timedelta(hours=1)).isoformat()}))
            self.assertEqual(summary(p,self.now)['status'],'STALE')
    def test_unavailable_report_renders(self):
        self.assertIn('UNAVAILABLE',markdown({'status':'UNAVAILABLE'}))
    def test_bad_snapshot_does_not_break_operational_report(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);atomic_write(p/'latest.json','{"as_of":"not-a-date"}')
            self.assertEqual(summary(p,self.now)['status'],'UNAVAILABLE')
    def test_repeat_collection_preserves_first_seen_and_marks_failure(self):
        item=parse_feed(self.feed(),'eia',self.now)[0][0]
        def fake(source,now):
            return source,([dict(item)] if source=='eia' else []),{'status':'OK' if source=='eia' else 'UNAVAILABLE'}
        with tempfile.TemporaryDirectory() as d, patch('trading_ai.news.fetch',side_effect=fake):
            with patch('trading_ai.news.utcnow',return_value=self.now):a=collect(Path(d))
            with patch('trading_ai.news.utcnow',return_value=self.now+timedelta(minutes=15)):b=collect(Path(d))
            self.assertEqual(len(b['items']),1)
            self.assertEqual(a['items'][0]['first_seen_at'],b['items'][0]['first_seen_at'])
            self.assertEqual(b['status'],'PARTIAL')

    def test_network_failure_is_not_bypassed(self):
        with patch('trading_ai.news.urlopen',side_effect=URLError('unavailable')),patch('trading_ai.news.subprocess.run') as native:
            with self.assertRaises(URLError):download({'url':'https://example.com','hosts':['example.com']})
            native.assert_not_called()
    def test_signal_news_evidence_cannot_be_replaced_with_later_news(self):
        with tempfile.TemporaryDirectory() as d:
            j=Journal(Path(d))
            try:
                env={'signal':{'id':'one','instrument':'OIL'}}
                record_signal_context(j,[{'signal':env}],self.now)
                before=j.setting('news_evidence:'+digest(env))
                record_signal_context(j,[{'signal':env}],self.now+timedelta(hours=1))
                self.assertEqual(before,j.setting('news_evidence:'+digest(env)))
                self.assertFalse(before['affects_execution'])
            finally:j.close()

if __name__=='__main__':unittest.main()
