"""Chronological validation on existing real ticks; no strategy backtest or orders."""
from pathlib import Path
import json,gzip,hashlib,io,unittest
from timeline import Timeline,Unverified
import test_timeline

A=Path(__file__).resolve().parent;ROOT=A.parents[2];source=A.parent/'stage5'
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
reference=read(source/'comparison.json')
boundaries={tf:[(r['start_raw_ms'],r['end_raw_ms']) for r in reference['bars'] if r['timeframe']==tf] for tf in ['H1','H4','D1']}
timeline=Timeline(boundaries);events=[];processed=0
for block in read(source/'collection.json')['blocks']:
    assert block['status']=='OBSERVED'
    with gzip.open(source/block['path']/'ticks.raw.json.gz','rt',encoding='utf-8') as f:part=json.load(f)
    for tick in part:
        published=timeline.feed(tick);processed+=1
        for event in published:
            assert event['end_raw_ms']<=tick['time_msc']
            events.append(event)
# Explicit raw timer event at the end of a completely requested window; creates no quote/fill.
timer_ms=read(source/'collection.json')['end_raw_ms']
timer_events=timeline.advance(timer_ms);events.extend(timer_events)
for tf in boundaries:
    actual=timeline.snapshot(tf);expected=[r for r in reference['bars'] if r['timeframe']==tf]
    assert len(actual)==len(expected)
    for got,want in zip(actual,expected):
        assert got['status']=='CLOSED'
        assert got['end_raw_ms']<=got['published_raw_ms']
        assert all(got['ohlc'][k]==want['reference_ohlc'][k] for k in ['open','high','low','close'])
        assert got['ohlc']['tick_volume']==want['reference_tick_volume']
try:timeline.utc_market('EURUSD.pro',{},'H1',1,[],10000)
except Unverified:unknown_utc_blocked=True
else:unknown_utc_blocked=False
assert unknown_utc_blocked
out=io.StringIO();r=unittest.TextTestRunner(stream=out,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(test_timeline))
(A/'tests.txt').write_text(out.getvalue(),encoding='utf-8');assert r.wasSuccessful(),out.getvalue()
for item in read(A.parent/'inputs/protected_hashes.json'):assert sha(ROOT/item['path'])==item['sha256']
for name in ['stage1_manifest.json','stage2/manifest.json','stage3/manifest.json','stage4/manifest.json','stage5/manifest.json']:
    manifest=A.parent/name
    for item in read(manifest)['files']:assert sha(manifest.parent/item['path'])==item['sha256']
result=dict(data_class='EXPLORATORY_CHRONOLOGY_TEST',tick_records=processed,closed_bars=len(events),
            timer_finalized_bars=len(timer_events),publication_events=events,ohlc_and_counts_match_reference=True,
            tests=r.testsRun,passed=r.wasSuccessful(),unknown_utc_strategy_adapter_blocked=unknown_utc_blocked,
            production_unchanged=True,new_orders_sent=0,full_backtest_run=False,
            profitability_metrics=None,latency_calibrated=False,queue_returns_quote_candidates_not_fills=True)
(A/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print('PASS:',processed,'ticks;',len(events),'chronological bars;',len(timer_events),'timer closures;',r.testsRun,'tests; unverified UTC blocked.')
