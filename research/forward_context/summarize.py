"""Summarize captured evidence and inventory existing news, locally/read-only."""
import collections,json,sqlite3
from pathlib import Path
from archive import ContextArchive,utc,stamp
A=Path(__file__).resolve().parent;ROOT=A.parents[1]
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
captures=[]
for folder in sorted(A.glob('capture-*')):
    if not (folder/'result.json').exists():continue
    result=read(folder/'result.json');archive=ContextArchive(folder)
    try:
        chain=archive.verify();assert chain['head_hash']==result['head_hash']
        sources=[]
        for source in read(folder/'config.json')['sources']:
            rows=[dict(r) for r in archive.db.execute('SELECT * FROM observations WHERE source=? ORDER BY seq',(source,))]
            versions=[dict(r) for r in archive.db.execute('SELECT id,first_received_at,raw_sha256 FROM versions WHERE source=? ORDER BY first_received_at',(source,))]
            at=result['finished_at'];choice=archive.asof(source,at)
            sources.append(dict(source=source,observations=len(rows),versions=versions,
                statuses=dict(collections.Counter(json.loads(r['payload'])['status'] for r in rows)),
                final_asof_status=choice['status'],first_receipt=rows[0]['observed_wall_utc'],last_receipt=rows[-1]['observed_wall_utc']))
        # Every new calendar version must be absent from an earlier as-of result.
        checks=[]
        for v in archive.db.execute("SELECT id,first_received_at FROM versions WHERE source='calendar' ORDER BY first_received_at"):
            from datetime import timedelta
            before=archive.asof('calendar',utc(v['first_received_at'])-timedelta(microseconds=1))
            checks.append(dict(version=v['id'],not_visible_before_receipt=before.get('receipt',{}).get('version_id')!=v['id']))
        assert all(x['not_visible_before_receipt'] for x in checks)
        captures.append(dict(path=folder.name,result=result,sources=sources,asof_checks=checks,integrity=chain,
            launch_code_snapshot_present=(folder/'source_snapshot').exists()))
    finally:archive.close()
snapshots=sorted((ROOT/'state/news/snapshots').glob('*.json'))
with sqlite3.connect((ROOT/'state/news/news.sqlite3').resolve().as_uri()+'?mode=ro',uri=True) as db:
    items=[json.loads(r[0]) for r in db.execute('SELECT payload FROM items')]
earliest=min((utc(i['first_seen_at']) for i in items),default=None)
inventory=dict(snapshot_files=len(snapshots),first_snapshot=snapshots[0].name if snapshots else None,
    last_snapshot=snapshots[-1].name if snapshots else None,items=len(items),
    earliest_producer_first_seen=stamp(earliest) if earliest else None,
    latest_snapshot_sources=read(ROOT/'state/news/latest.json')['sources'],
    latest_snapshot_items_by_source=dict(collections.Counter(i['source'] for i in read(ROOT/'state/news/latest.json')['items'])),
    old_publication_does_not_prove_old_receipt=True)
(A/'analysis.json').write_text(json.dumps(dict(captures=captures,news_inventory=inventory,
    orders_authorized=False,complete_future_replay_ready=False),indent=2),encoding='utf-8')
print(json.dumps(dict(captures=[dict(path=c['path'],observations=c['result']['observations'],
    sources=[dict(source=s['source'],versions=len(s['versions']),asof=s['final_asof_status']) for s in c['sources']]) for c in captures],news_inventory=inventory),indent=2))
