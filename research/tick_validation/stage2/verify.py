"""Verify sealed controlled-test artifacts without loading a broker or rerunning tests."""
from pathlib import Path
import hashlib
import json

A=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for item in read(A/'manifest.json')['files']:
    assert sha(A/item['path'])==item['sha256'],item['path']
r=read(A/'tests.json')
assert r['tests']==35 and r['passed'] and not r['failures'] and not r['errors']
assert r['real_orders_sent']==0 and not r['full_backtest_run'] and r['source_unchanged']
assert sha(A/'traces.json')==r['traces_sha256']
traces=read(A/'traces.json')
assert len(traces)==35
for cases in traces.values():
    for t in cases:
        assert t['data_class']=='SYNTHETIC_CONTROLLED_TEST'
        assert t['time_basis']=='EXPLICIT_UTC_FIXTURE'
        assert t['config']['terminal_path']=='IN_MEMORY_ONLY'
        assert t['config']['account_server']=='SIMULATOR'
        assert t['account']['server']=='SIMULATOR'
        assert t['account']['login']==123456
for item in read(A/'source_manifest.json'):
    assert sha(A/'source_snapshot'/item['path'])==item['sha256']
    assert sha(A.parents[2]/item['path'])==item['sha256'], 'Production changed: '+item['path']
print('PASS: 35 synthetic cases, hashes, frozen policy, production integrity; no full backtest.')
