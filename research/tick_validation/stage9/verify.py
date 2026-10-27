"""Offline, read-only verification; --seal creates the immutable manifest once."""
import hashlib, json, sys, unittest
from pathlib import Path
from analyze import evaluate
from test_grid import GridTests

A = Path(__file__).resolve().parent
ROOT = A.parents[2]
read = lambda p: json.loads(p.read_text(encoding='utf-8'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
result, capture, config = (read(A / name) for name in ['comparison.json', 'capture.json', 'config.json'])
assert sha(A / 'config.json') == result['config_sha256']
assert sha(A / 'capture.json') == result['capture_sha256']
assert evaluate(capture, config) == result['instruments']
assert len(result['instruments']) == 7 and result['observations'] == 504
assert all(s['observations'] == 72 and s['status'] == 'DIAGNOSTIC_ONLY' for s in result['instruments'])
assert all(c['compared'] == 72 and c['excluded'] == 0 for s in result['instruments'] for c in s['comparisons'])
assert not result['historical_policy_approved'] and result['accepted_historical_cost_policy'] is None
assert not result['full_backtest_run'] and result['new_orders_sent'] == 0
tests = unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(GridTests))
assert tests.wasSuccessful() and tests.testsRun == result['tests'] == 11
for item in read(A.parent / 'inputs/protected_hashes.json'):
    assert sha(ROOT / item['path']) == item['sha256'], item['path']
for name in ['stage1_manifest.json', *[f'stage{i}/manifest.json' for i in range(2, 9)]]:
    p = A.parent / name
    for item in read(p)['files']:
        assert sha(p.parent / item['path']) == item['sha256'], item['path']
manifest = A / 'manifest.json'
if '--seal' in sys.argv:
    assert not manifest.exists(), 'Manifest already exists'
    files = [p for p in A.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p != manifest]
    manifest.write_text(json.dumps(dict(stage='MULTI_CONTRACT_CURRENT_CASH_DIAGNOSTIC',
        files=[dict(path=p.relative_to(A).as_posix(), sha256=sha(p)) for p in sorted(files)]), indent=2), encoding='utf-8')
for item in read(manifest)['files']:
    assert sha(A / item['path']) == item['sha256'], item['path']
print('PASS: 504 broker calculations reproduced offline; 11 tests; stage and production integrity verified.')
