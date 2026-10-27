"""Recompute coverage offline; --seal creates a manifest once, otherwise read-only."""
import hashlib, io, json, sys, unittest
from pathlib import Path
from inventory import build
from test_coverage import CoverageTests

A = Path(__file__).resolve().parent
ROOT = A.parents[2]
read = lambda p: json.loads(p.read_text(encoding='utf-8'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
result = read(A / 'coverage_inventory.json')
assert build() == result, 'Offline reconstruction differs'
assert result['downloaded_records'] == 657250
assert result['consistent_unique_records'] == 634030
assert all(not s['overlap_conflicts'] for s in result['instruments'])
assert not result['full_backtest_run'] and result['new_orders_sent'] == 0
assert not result['continuous_history_certified'] and not result['historical_UTC_verified']
tests = unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(CoverageTests))
assert tests.wasSuccessful() and tests.testsRun == 12
collection = read(A / 'collection.json')
assert sha(A.parent / 'stage3/probe.py') == collection['worker_sha256']
assert [r['process_status'] for r in collection['requests']] == ['TIMEOUT', 'NOT_ATTEMPTED_AFTER_ERROR', 'NOT_ATTEMPTED_AFTER_ERROR']
for item in read(A.parent / 'inputs/protected_hashes.json'):
    assert sha(ROOT / item['path']) == item['sha256'], item['path']
for name in ['stage1_manifest.json', *[f'stage{i}/manifest.json' for i in range(2, 10)]]:
    path = A.parent / name
    for item in read(path)['files']:
        assert sha(path.parent / item['path']) == item['sha256'], item['path']
manifest = A / 'manifest.json'
if '--seal' in sys.argv:
    assert not manifest.exists(), 'Manifest already exists'
    files = [p for p in A.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p != manifest]
    manifest.write_text(json.dumps(dict(stage='TICK_COVERAGE_RECONCILIATION', tests=12,
        files=[dict(path=p.relative_to(A).as_posix(), sha256=sha(p)) for p in sorted(files)]), indent=2), encoding='utf-8')
for item in read(manifest)['files']:
    assert sha(A / item['path']) == item['sha256'], item['path']
print('PASS: 634030 reconciled records; 12 tests; captured failure retained; production and stages 1-9 unchanged.')
