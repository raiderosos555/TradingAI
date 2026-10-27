from pathlib import Path
import json,hashlib
A=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((A/'result.json').read_text())
assert r['tick_records']==277031 and r['closed_bars']==31 and r['timer_finalized_bars']==3
assert r['tests']==18 and r['passed'] and r['unknown_utc_strategy_adapter_blocked']
assert r['queue_returns_quote_candidates_not_fills'] and not r['latency_calibrated']
assert r['production_unchanged'] and r['new_orders_sent']==0 and not r['full_backtest_run']
assert all(e['published_raw_ms']>=e['end_raw_ms'] for e in r['publication_events'])
files=[p for p in A.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p!=A/'manifest.json']
(A/'manifest.json').write_text(json.dumps(dict(stage='CHRONOLOGICAL_FEED_AND_QUOTE_CANDIDATES',files=[dict(path=p.relative_to(A).as_posix(),sha256=sha(p)) for p in sorted(files)]),indent=2),encoding='utf-8')
print('Sealed: 18 tests and chronological real-data bar evidence; no full backtest.')
