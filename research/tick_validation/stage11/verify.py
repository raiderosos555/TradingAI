"""Offline evidence verification. --recompute also repeats every tick/bar comparison."""
import gzip,hashlib,json,sys,unittest
from pathlib import Path
from test_comparison import ComparisonTests
A=Path(__file__).resolve().parent; ROOT=A.parents[2]
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=read(A/'comparison.json'); c=read(A/'resolved_collection.json')
assert r['collection_sha256']==sha(A/'resolved_collection.json')
assert r['config_sha256']==sha(A/'config.json')
assert c['original_collection_sha256']==sha(A/'collection.json')
assert c['retry_config_sha256']==sha(A/'retry_config.json')
assert c['retry_worker_sha256']==sha(A/'fast_probe.py')
assert c['worker_sha256']==sha(A.parent/'stage3/probe.py')
assert len(r['instruments'])==7 and all(not s['missing_request_ranges'] for s in r['instruments'])
assert r['tick_records']==sum(s['tick_records'] for s in r['instruments'])
assert set(r['status_counts'])<= {'MATCH','MATCH_LAST_WITH_INVALID_QUOTES','REFERENCE_ABSENT_NO_LAST'}
assert r['status_counts'].get('MATCH',0)+r['status_counts'].get('MATCH_LAST_WITH_INVALID_QUOTES',0)==213
assert r['status_counts']['REFERENCE_ABSENT_NO_LAST']==4
assert all(s['previous_hour_overlap']['exact_provider_sequence_matches'] for s in r['instruments'])
assert not r['full_backtest_run'] and not r['strategy_parameters_changed'] and r['new_orders_sent']==0
assert r['accepted_historical_UTC_segments']==[] and not r['historical_cost_policy_approved']
for row in r['source_hashes']:assert sha(A.parent/row['path'])==row['sha256'],row['path']
for instrument in c['instruments']:
    for row in instrument['bar_sources']:
        assert sha(A/row['path'])==row['sha256']
codec=read(A/'codec_validation.json')
source=A/codec['source']
assert sha(source)==codec['source_sha256']
raw=gzip.decompress(source.read_bytes())
assert hashlib.sha256(raw).hexdigest()==codec['decoded_sha256']
assert gzip.decompress(gzip.compress(raw,compresslevel=1,mtime=0))==raw
assert codec['decompressed_bytes_identical'] and not codec['broker_called']
tests=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(ComparisonTests))
assert tests.wasSuccessful() and tests.testsRun==14
health=read(A/'demo_health.json')
assert len(health['samples'])==3 and health['orders_sent_by_audit']==0
assert read(A/'demo_audit_retry_process.json')['status']=='COMPLETED'
assert not health['unresolved_operations']
invalid_current_quotes=[]
for sample in health['samples']:
    assert sample['terminal_connected'] and sample['engine_status']['status']=='RUNNING'
    for quote in sample['quotes'].values():
        assert -2<=quote['age_seconds_under_runtime_offset']<=health['risk_limits']['max_tick_age_seconds']
        if not 0<quote['raw']['bid']<=quote['raw']['ask']:
            invalid_current_quotes.append(quote)
    for position in sample['positions']:
        assert position['sl']>0 and position['tp']>0
        assert any(row.get('position_id')==position['identifier'] for h in health['opening_order_history'] for row in h['rows'])
assert len(invalid_current_quotes)==5,'Health conclusion must be reviewed if evidence changes'
for sample in health['samples']:
    for p in sample['positions']:
        alias=next(a for a in sample['quotes'] if p['symbol'].startswith(a+'.'))
        assert 0<sample['quotes'][alias]['raw']['bid']<=sample['quotes'][alias]['raw']['ask']
for row in read(A.parent/'inputs/protected_hashes.json'):assert sha(ROOT/row['path'])==row['sha256'],row['path']
for name in ['stage1_manifest.json',*[f'stage{i}/manifest.json' for i in range(2,11)]]:
    p=A.parent/name
    for row in read(p)['files']:assert sha(p.parent/row['path'])==row['sha256'],row['path']
if '--recompute' in sys.argv:
    from analyze import build
    assert build(verbose=True)==r,'Recomputed result differs'
manifest=A/'manifest.json'
if '--seal' in sys.argv:
    assert not manifest.exists(),'Manifest exists'
    files=[p for p in A.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p!=manifest]
    manifest.write_text(json.dumps(dict(stage='SEVEN_INSTRUMENT_RAW_DAY_VALIDATION',tests=14,
        files=[dict(path=p.relative_to(A).as_posix(),sha256=sha(p)) for p in sorted(files)]),indent=2),encoding='utf-8')
for row in read(manifest)['files']:assert sha(A/row['path'])==row['sha256'],row['path']
print('AUDIT COMPLETE: 213 matching Last bars; 14 tests; production unchanged. DEMO health WARNING: 5/21 fresh snapshots have invalid Bid/Ask.')
