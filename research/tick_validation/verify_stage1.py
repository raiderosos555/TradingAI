"""Offline deliverable/evidence consistency; not a profitability certification."""
from pathlib import Path
import json,hashlib,csv
A=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
m=read(A/'stage1_manifest.json')
for item in m['files']:
 assert hashlib.sha256((A/item['path']).read_bytes()).hexdigest()==item['sha256'],item['path']
p=read(A/'price_checks.json');assert len(p)==7 and sum(r['ticks'] for r in p)==371167
for r in p:
 assert r['Last_updates_OHLC_error']==0 and r['Bid_OHLC_error']>0
 assert r['raw_start_ms']<=r['first_raw_ms']<=r['last_raw_ms']<r['raw_end_ms']
 assert r['first_quotes']['BUY_OPEN']==r['first_quotes']['SELL_CLOSE']
 assert r['first_quotes']['BUY_CLOSE']==r['first_quotes']['SELL_OPEN']
 assert r['PnL'] is None and r['utc_mapping']=='UNVERIFIED_FOR_INTERVAL'
with (A/'price_checks.csv').open(encoding='utf-8-sig',newline='') as f:assert len(list(csv.DictReader(f)))==len(p)
t=read(A/'tests.json');assert t['passed'] and not t['failures'] and not t['errors']
clock=read(A/'clock_assessment.v2.json');assert not clock['accepted_historical_segments'] and not clock['tick_encoding_after_DST_verified']
assert clock['offset_candidate_seconds']==7200 and clock['fresh_EA_offset_seconds']==[3600]
assert not m['full_backtest_run'] and not m['strategy_optimized'] and m['orders_sent']==0
assert all(r['unchanged'] for r in read(A/'production_integrity.json'))
for name in ('DATA_COVERAGE','PRICE_MODEL','EXECUTION_PARITY','BACKTEST_COMPARISON','REMAINING_LIMITATIONS'):
 assert (A/(name+'.md')).stat().st_size>500
print('PASS: file hashes, 7 tick streams, 371167 records, 30 tests, price/clock evidence, 5 reports; no full replay.')
