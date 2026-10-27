"""Check captured evidence and seal stage files; no broker calls."""
from pathlib import Path
import json,hashlib
A=Path(__file__).resolve().parent;ROOT=A.parents[2]
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
d=read(A/'comparison.json');c=read(A/'collection.json')
assert d['tick_records']==277031 and len(d['bars'])==31
assert d['request_coverage_complete'] and not d['server_history_completeness_certified']
assert d['tests']==12 and d['tests_passed'] and not d['full_backtest_run'] and not d['accepted_historical_utc_segments']
assert all(b['last_matches'] and b['last_count_matches_tick_volume'] and not b['missing_request_ranges'] for b in d['bars'])
assert {tf:sum(b['timeframe']==tf for b in d['bars']) for tf in ['H1','H4','D1']}=={'H1':24,'H4':6,'D1':1}
assert [b['count'] for b in c['blocks']]==[20875,33548,64170,72434,62580,23424]
assert sum(b['last_updates'] for b in d['bars'] if b['timeframe']=='H1')==138484
assert all(b['max_price_error']['last']==0 for b in d['bars'])
for r in read(A.parent/'inputs/protected_hashes.json'):assert sha(ROOT/r['path'])==r['sha256']
for name in ['stage1_manifest.json','stage2/manifest.json','stage3/manifest.json','stage4/manifest.json']:
    p=A.parent/name
    for r in read(p)['files']:assert sha(p.parent/r['path'])==r['sha256']
files=[p for p in A.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p!=A/'manifest.json']
(A/'manifest.json').write_text(json.dumps(dict(stage='RAW_DAY_BAR_RECONSTRUCTION',files=[dict(path=p.relative_to(A).as_posix(),sha256=sha(p)) for p in sorted(files)]),indent=2),encoding='utf-8')
print('PASS: 277031 ticks, 31 exact Last OHLC/count matches, 12 tests, previous evidence and production unchanged.')
